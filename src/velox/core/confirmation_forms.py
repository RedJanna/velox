"""Reservation confirmation HTML form generation and public-link persistence."""

# ruff: noqa: E501

from __future__ import annotations

import hmac
import re
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from html import escape
from typing import Any, Literal

import asyncpg
import orjson
import structlog

from velox.config.constants import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES
from velox.config.settings import settings
from velox.core.hotel_profile_loader import get_profile
from velox.models.hotel_profile import HotelProfile
from velox.utils.json import decode_json_object

logger = structlog.get_logger(__name__)

ConfirmationFormType = Literal["accommodation", "restaurant", "transfer"]

TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_-]{32,160}$")
ROUTE_SPLIT_PATTERN = re.compile(r"\s*(?:<->|->|→|↔|\bto\b| - | – | — )\s*", re.IGNORECASE)
DEFAULT_EXPIRY_DAYS = 30

FORM_TYPE_FROM_APPROVAL = {
    "STAY": "accommodation",
    "ACCOMMODATION": "accommodation",
    "RESTAURANT": "restaurant",
    "TRANSFER": "transfer",
}

APPROVAL_TYPE_FROM_FORM = {
    "accommodation": "STAY",
    "restaurant": "RESTAURANT",
    "transfer": "TRANSFER",
}


@dataclass(frozen=True)
class ConfirmationDetail:
    """One customer-facing detail row in the generated confirmation."""

    label: str
    value: str
    emphasis: bool = False


@dataclass(frozen=True)
class ConfirmationSection:
    """A section of details in the generated confirmation."""

    title: str
    items: tuple[ConfirmationDetail, ...]


@dataclass(frozen=True)
class ConfirmationContext:
    """Normalized, source-grounded data used to render a confirmation form."""

    form_type: ConfirmationFormType
    hotel_id: int
    hotel_name: str
    language: str
    customer_name: str
    phone_display: str
    reference_id: str
    confirmation_no: str
    sections: tuple[ConfirmationSection, ...]
    important_note: str
    generated_at: datetime


@dataclass(frozen=True)
class ConfirmationPreview:
    """Rendered confirmation form preview."""

    context: ConfirmationContext
    html: str
    whatsapp_message: str


@dataclass(frozen=True)
class ConfirmationDelivery:
    """Persisted confirmation form delivery data."""

    form_id: str
    public_url: str
    token_prefix: str
    html: str
    whatsapp_message: str


COPY: dict[str, dict[str, str]] = {
    "en": {
        "document_title": "Reservation Confirmation",
        "confirmed": "Reservation Confirmed",
        "intro": "Your reservation has been confirmed by our team. Please review the details below.",
        "confirmation_no": "Confirmation No.",
        "status": "Status",
        "confirmed_status": "Confirmed",
        "customer_information": "Customer Information",
        "confirmation_information": "Confirmation Information",
        "important_information": "Important Information",
        "generated_on": "Generated on",
        "secure_notice": "This confirmation page is intended for the customer only. Please do not share the link publicly.",
        "form_link_line": "You can view your secure confirmation form here:",
        "accommodation": "Accommodation",
        "restaurant": "Restaurant",
        "transfer": "Transfer",
        "stay_details": "Stay Details",
        "restaurant_details": "Restaurant Details",
        "transfer_details": "Transfer Details",
        "guest": "Guest",
        "phone": "Phone",
        "email": "Email Address",
        "checkin": "Check-in",
        "checkout": "Check-out",
        "room": "Room",
        "board": "Board",
        "guests": "Guests",
        "total": "Total",
        "policy": "Policy",
        "date": "Date",
        "time": "Time",
        "party_size": "Party Size",
        "area": "Area",
        "table": "Table",
        "route": "Route",
        "pax": "Passengers",
        "flight": "Flight",
        "vehicle": "Vehicle",
        "baby_seat": "Baby Seat",
        "price": "Price",
        "notes": "Notes",
        "yes": "Yes",
        "no": "No",
        "accommodation_note": "Payment and cancellation conditions remain subject to the confirmed reservation policy.",
        "restaurant_note": "Please arrive on time. Special requests are subject to operational availability.",
        "transfer_note": "Please keep your phone reachable near the pickup time. Flight and route changes must be shared with the team.",
    },
    "tr": {
        "document_title": "Rezervasyon Onay Formu",
        "confirmed": "Rezervasyon Onaylandı",
        "intro": "Rezervasyonunuz ekibimiz tarafından onaylanmıştır. Lütfen aşağıdaki bilgileri kontrol ediniz.",
        "confirmation_no": "Onay No.",
        "status": "Durum",
        "confirmed_status": "Onaylandı",
        "customer_information": "Misafir Bilgileri",
        "confirmation_information": "Onay Bilgileri",
        "important_information": "Önemli Bilgilendirme",
        "generated_on": "Oluşturulma",
        "secure_notice": "Bu onay sayfası yalnızca ilgili misafir içindir. Lütfen bağlantıyı herkese açık şekilde paylaşmayınız.",
        "form_link_line": "Güvenli onay formunuzu buradan görüntüleyebilirsiniz:",
        "accommodation": "Konaklama",
        "restaurant": "Restoran",
        "transfer": "Transfer",
        "stay_details": "Konaklama Detayları",
        "restaurant_details": "Restoran Detayları",
        "transfer_details": "Transfer Detayları",
        "guest": "Misafir",
        "phone": "Telefon",
        "email": "E-posta",
        "checkin": "Giriş",
        "checkout": "Çıkış",
        "room": "Oda",
        "board": "Pansiyon",
        "guests": "Kişi",
        "total": "Toplam",
        "policy": "Politika",
        "date": "Tarih",
        "time": "Saat",
        "party_size": "Kişi Sayısı",
        "area": "Alan",
        "table": "Masa",
        "route": "Güzergah",
        "pax": "Yolcu",
        "flight": "Uçuş",
        "vehicle": "Araç",
        "baby_seat": "Bebek Koltuğu",
        "price": "Fiyat",
        "notes": "Notlar",
        "yes": "Evet",
        "no": "Hayır",
        "accommodation_note": "Ödeme ve iptal koşulları onaylanan rezervasyon politikasına tabidir.",
        "restaurant_note": "Lütfen rezervasyon saatinizde hazır olunuz. Özel talepler operasyonel uygunluğa göre değerlendirilir.",
        "transfer_note": "Lütfen transfer saatine yakın telefonunuzu ulaşılabilir tutunuz. Uçuş veya güzergah değişikliklerini ekibimizle paylaşınız.",
    },
    "ru": {
        "document_title": "Подтверждение бронирования",
        "confirmed": "Бронирование подтверждено",
        "intro": "Ваше бронирование подтверждено нашей командой. Пожалуйста, проверьте детали ниже.",
        "confirmation_no": "Номер подтверждения",
        "status": "Статус",
        "confirmed_status": "Подтверждено",
        "customer_information": "Информация о госте",
        "confirmation_information": "Информация о подтверждении",
        "important_information": "Важная информация",
        "generated_on": "Создано",
        "secure_notice": "Эта страница предназначена только для клиента. Не публикуйте ссылку открыто.",
        "form_link_line": "Вашу защищенную форму подтверждения можно открыть здесь:",
        "accommodation": "Проживание",
        "restaurant": "Ресторан",
        "transfer": "Трансфер",
        "stay_details": "Детали проживания",
        "restaurant_details": "Детали ресторана",
        "transfer_details": "Детали трансфера",
        "guest": "Гость",
        "phone": "Телефон",
        "email": "Электронная почта",
        "checkin": "Заезд",
        "checkout": "Выезд",
        "room": "Номер",
        "board": "Питание",
        "guests": "Гости",
        "total": "Итого",
        "policy": "Политика",
        "date": "Дата",
        "time": "Время",
        "party_size": "Количество гостей",
        "area": "Зона",
        "table": "Стол",
        "route": "Маршрут",
        "pax": "Пассажиры",
        "flight": "Рейс",
        "vehicle": "Автомобиль",
        "baby_seat": "Детское кресло",
        "price": "Цена",
        "notes": "Примечания",
        "yes": "Да",
        "no": "Нет",
        "accommodation_note": "Условия оплаты и отмены зависят от подтвержденной политики бронирования.",
        "restaurant_note": "Пожалуйста, приходите вовремя. Особые пожелания зависят от операционной возможности.",
        "transfer_note": "Пожалуйста, держите телефон доступным перед временем встречи. Сообщайте команде об изменениях рейса или маршрута.",
    },
    "de": {
        "document_title": "Reservierungsbestätigung",
        "confirmed": "Reservierung bestätigt",
        "intro": "Ihre Reservierung wurde von unserem Team bestätigt. Bitte prüfen Sie die Details unten.",
        "confirmation_no": "Bestätigungsnummer",
        "status": "Status",
        "confirmed_status": "Bestätigt",
        "customer_information": "Gästeinformationen",
        "confirmation_information": "Bestätigungsinformationen",
        "important_information": "Wichtige Informationen",
        "generated_on": "Erstellt am",
        "secure_notice": "Diese Bestätigungsseite ist nur für den Kunden bestimmt. Bitte teilen Sie den Link nicht öffentlich.",
        "form_link_line": "Ihre sichere Bestätigungsseite finden Sie hier:",
        "accommodation": "Unterkunft",
        "restaurant": "Restaurant",
        "transfer": "Transfer",
        "stay_details": "Aufenthaltsdetails",
        "restaurant_details": "Restaurantdetails",
        "transfer_details": "Transferdetails",
        "guest": "Gast",
        "phone": "Telefon",
        "email": "E-Mail-Adresse",
        "checkin": "Check-in",
        "checkout": "Check-out",
        "room": "Zimmer",
        "board": "Verpflegung",
        "guests": "Gäste",
        "total": "Gesamt",
        "policy": "Richtlinie",
        "date": "Datum",
        "time": "Uhrzeit",
        "party_size": "Personen",
        "area": "Bereich",
        "table": "Tisch",
        "route": "Route",
        "pax": "Passagiere",
        "flight": "Flug",
        "vehicle": "Fahrzeug",
        "baby_seat": "Kindersitz",
        "price": "Preis",
        "notes": "Notizen",
        "yes": "Ja",
        "no": "Nein",
        "accommodation_note": "Zahlungs- und Stornierungsbedingungen richten sich nach der bestätigten Reservierungsrichtlinie.",
        "restaurant_note": "Bitte erscheinen Sie pünktlich. Sonderwünsche hängen von der operativen Verfügbarkeit ab.",
        "transfer_note": "Bitte halten Sie Ihr Telefon zur Abholzeit erreichbar. Flug- oder Routenänderungen müssen dem Team mitgeteilt werden.",
    },
    "ar": {
        "document_title": "تأكيد الحجز",
        "confirmed": "تم تأكيد الحجز",
        "intro": "تم تأكيد حجزكم من قبل فريقنا. يرجى مراجعة التفاصيل أدناه.",
        "confirmation_no": "رقم التأكيد",
        "status": "الحالة",
        "confirmed_status": "مؤكد",
        "customer_information": "معلومات العميل",
        "confirmation_information": "معلومات التأكيد",
        "important_information": "معلومات مهمة",
        "generated_on": "تاريخ الإنشاء",
        "secure_notice": "هذه صفحة تأكيد مخصصة للعميل فقط. يرجى عدم نشر الرابط علناً.",
        "form_link_line": "يمكنكم عرض نموذج التأكيد الآمن من هنا:",
        "accommodation": "الإقامة",
        "restaurant": "المطعم",
        "transfer": "النقل",
        "stay_details": "تفاصيل الإقامة",
        "restaurant_details": "تفاصيل المطعم",
        "transfer_details": "تفاصيل النقل",
        "guest": "الضيف",
        "phone": "الهاتف",
        "email": "البريد الإلكتروني",
        "checkin": "تسجيل الوصول",
        "checkout": "تسجيل المغادرة",
        "room": "الغرفة",
        "board": "الخدمة",
        "guests": "الضيوف",
        "total": "الإجمالي",
        "policy": "السياسة",
        "date": "التاريخ",
        "time": "الوقت",
        "party_size": "عدد الأشخاص",
        "area": "المكان",
        "table": "الطاولة",
        "route": "المسار",
        "pax": "الركاب",
        "flight": "الرحلة",
        "vehicle": "المركبة",
        "baby_seat": "مقعد طفل",
        "price": "السعر",
        "notes": "ملاحظات",
        "yes": "نعم",
        "no": "لا",
        "accommodation_note": "تخضع شروط الدفع والإلغاء لسياسة الحجز المؤكدة.",
        "restaurant_note": "يرجى الحضور في الوقت المحدد. تعتمد الطلبات الخاصة على التوفر التشغيلي.",
        "transfer_note": "يرجى إبقاء هاتفكم متاحاً قرب وقت الاستقبال. يجب إبلاغ الفريق بأي تغيير في الرحلة أو المسار.",
    },
    "es": {
        "document_title": "Confirmación de Reserva",
        "confirmed": "Reserva Confirmada",
        "intro": "Su reserva ha sido confirmada por nuestro equipo. Revise los detalles a continuación.",
        "confirmation_no": "N.º de confirmación",
        "status": "Estado",
        "confirmed_status": "Confirmada",
        "customer_information": "Información del cliente",
        "confirmation_information": "Información de confirmación",
        "important_information": "Información importante",
        "generated_on": "Generado el",
        "secure_notice": "Esta página de confirmación es solo para el cliente. No comparta el enlace públicamente.",
        "form_link_line": "Puede ver su formulario seguro de confirmación aquí:",
        "accommodation": "Alojamiento",
        "restaurant": "Restaurante",
        "transfer": "Traslado",
        "stay_details": "Detalles de la estancia",
        "restaurant_details": "Detalles del restaurante",
        "transfer_details": "Detalles del traslado",
        "guest": "Huésped",
        "phone": "Teléfono",
        "email": "Correo electrónico",
        "checkin": "Llegada",
        "checkout": "Salida",
        "room": "Habitación",
        "board": "Régimen",
        "guests": "Huéspedes",
        "total": "Total",
        "policy": "Política",
        "date": "Fecha",
        "time": "Hora",
        "party_size": "Personas",
        "area": "Zona",
        "table": "Mesa",
        "route": "Ruta",
        "pax": "Pasajeros",
        "flight": "Vuelo",
        "vehicle": "Vehículo",
        "baby_seat": "Silla de bebé",
        "price": "Precio",
        "notes": "Notas",
        "yes": "Sí",
        "no": "No",
        "accommodation_note": "Las condiciones de pago y cancelación están sujetas a la política de reserva confirmada.",
        "restaurant_note": "Por favor, llegue a tiempo. Las solicitudes especiales dependen de la disponibilidad operativa.",
        "transfer_note": "Mantenga su teléfono disponible cerca de la hora de recogida. Informe al equipo sobre cambios de vuelo o ruta.",
    },
    "fr": {
        "document_title": "Confirmation de Réservation",
        "confirmed": "Réservation Confirmée",
        "intro": "Votre réservation a été confirmée par notre équipe. Veuillez vérifier les détails ci-dessous.",
        "confirmation_no": "N° de confirmation",
        "status": "Statut",
        "confirmed_status": "Confirmée",
        "customer_information": "Informations client",
        "confirmation_information": "Informations de confirmation",
        "important_information": "Informations importantes",
        "generated_on": "Généré le",
        "secure_notice": "Cette page de confirmation est destinée uniquement au client. Ne partagez pas le lien publiquement.",
        "form_link_line": "Vous pouvez consulter votre formulaire de confirmation sécurisé ici :",
        "accommodation": "Hébergement",
        "restaurant": "Restaurant",
        "transfer": "Transfert",
        "stay_details": "Détails du séjour",
        "restaurant_details": "Détails du restaurant",
        "transfer_details": "Détails du transfert",
        "guest": "Client",
        "phone": "Téléphone",
        "email": "Adresse e-mail",
        "checkin": "Arrivée",
        "checkout": "Départ",
        "room": "Chambre",
        "board": "Pension",
        "guests": "Personnes",
        "total": "Total",
        "policy": "Politique",
        "date": "Date",
        "time": "Heure",
        "party_size": "Nombre de personnes",
        "area": "Espace",
        "table": "Table",
        "route": "Trajet",
        "pax": "Passagers",
        "flight": "Vol",
        "vehicle": "Véhicule",
        "baby_seat": "Siège bébé",
        "price": "Prix",
        "notes": "Notes",
        "yes": "Oui",
        "no": "Non",
        "accommodation_note": "Les conditions de paiement et d'annulation restent soumises à la politique de réservation confirmée.",
        "restaurant_note": "Merci d'arriver à l'heure. Les demandes spéciales dépendent de la disponibilité opérationnelle.",
        "transfer_note": "Merci de garder votre téléphone joignable près de l'heure de prise en charge. Signalez tout changement de vol ou de trajet.",
    },
    "zh": {
        "document_title": "预订确认",
        "confirmed": "预订已确认",
        "intro": "您的预订已由我们的团队确认。请查看以下详细信息。",
        "confirmation_no": "确认编号",
        "status": "状态",
        "confirmed_status": "已确认",
        "customer_information": "客户信息",
        "confirmation_information": "确认信息",
        "important_information": "重要信息",
        "generated_on": "生成时间",
        "secure_notice": "此确认页面仅供客户本人使用。请勿公开分享链接。",
        "form_link_line": "您可以在此查看安全确认表：",
        "accommodation": "住宿",
        "restaurant": "餐厅",
        "transfer": "接送",
        "stay_details": "住宿详情",
        "restaurant_details": "餐厅详情",
        "transfer_details": "接送详情",
        "guest": "客人",
        "phone": "电话",
        "email": "电子邮件",
        "checkin": "入住",
        "checkout": "退房",
        "room": "房型",
        "board": "餐食",
        "guests": "人数",
        "total": "总计",
        "policy": "政策",
        "date": "日期",
        "time": "时间",
        "party_size": "用餐人数",
        "area": "区域",
        "table": "桌号",
        "route": "路线",
        "pax": "乘客",
        "flight": "航班",
        "vehicle": "车辆",
        "baby_seat": "婴儿座椅",
        "price": "价格",
        "notes": "备注",
        "yes": "是",
        "no": "否",
        "accommodation_note": "付款和取消条件以已确认的预订政策为准。",
        "restaurant_note": "请准时到达。特殊要求需视现场运营情况而定。",
        "transfer_note": "请在接送时间前后保持电话畅通。如航班或路线有变化，请通知团队。",
    },
    "hi": {
        "document_title": "आरक्षण पुष्टि",
        "confirmed": "आरक्षण पुष्टि हो गया",
        "intro": "आपका आरक्षण हमारी टीम द्वारा पुष्टि किया गया है। कृपया नीचे दिए गए विवरण देखें।",
        "confirmation_no": "पुष्टि संख्या",
        "status": "स्थिति",
        "confirmed_status": "पुष्टि",
        "customer_information": "ग्राहक जानकारी",
        "confirmation_information": "पुष्टि जानकारी",
        "important_information": "महत्वपूर्ण जानकारी",
        "generated_on": "बनाया गया",
        "secure_notice": "यह पुष्टि पृष्ठ केवल ग्राहक के लिए है। कृपया लिंक सार्वजनिक रूप से साझा न करें।",
        "form_link_line": "आप अपना सुरक्षित पुष्टि फॉर्म यहां देख सकते हैं:",
        "accommodation": "आवास",
        "restaurant": "रेस्तरां",
        "transfer": "ट्रांसफर",
        "stay_details": "ठहरने का विवरण",
        "restaurant_details": "रेस्तरां विवरण",
        "transfer_details": "ट्रांसफर विवरण",
        "guest": "अतिथि",
        "phone": "फोन",
        "email": "ईमेल पता",
        "checkin": "चेक-इन",
        "checkout": "चेक-आउट",
        "room": "कमरा",
        "board": "भोजन योजना",
        "guests": "अतिथि",
        "total": "कुल",
        "policy": "नीति",
        "date": "तारीख",
        "time": "समय",
        "party_size": "लोगों की संख्या",
        "area": "क्षेत्र",
        "table": "टेबल",
        "route": "मार्ग",
        "pax": "यात्री",
        "flight": "फ्लाइट",
        "vehicle": "वाहन",
        "baby_seat": "बेबी सीट",
        "price": "कीमत",
        "notes": "नोट्स",
        "yes": "हाँ",
        "no": "नहीं",
        "accommodation_note": "भुगतान और रद्द करने की शर्तें पुष्टि की गई आरक्षण नीति के अधीन हैं।",
        "restaurant_note": "कृपया समय पर पहुंचें। विशेष अनुरोध संचालन उपलब्धता पर निर्भर हैं।",
        "transfer_note": "कृपया पिकअप समय के आसपास अपना फोन उपलब्ध रखें। फ्लाइट या मार्ग में बदलाव टीम को बताएं।",
    },
    "pt": {
        "document_title": "Confirmação de Reserva",
        "confirmed": "Reserva Confirmada",
        "intro": "A sua reserva foi confirmada pela nossa equipa. Consulte os detalhes abaixo.",
        "confirmation_no": "N.º de confirmação",
        "status": "Estado",
        "confirmed_status": "Confirmada",
        "customer_information": "Informações do cliente",
        "confirmation_information": "Informações de confirmação",
        "important_information": "Informação importante",
        "generated_on": "Gerado em",
        "secure_notice": "Esta página de confirmação destina-se apenas ao cliente. Não partilhe o link publicamente.",
        "form_link_line": "Pode consultar o seu formulário de confirmação seguro aqui:",
        "accommodation": "Alojamento",
        "restaurant": "Restaurante",
        "transfer": "Transfer",
        "stay_details": "Detalhes da estadia",
        "restaurant_details": "Detalhes do restaurante",
        "transfer_details": "Detalhes do transfer",
        "guest": "Hóspede",
        "phone": "Telefone",
        "email": "E-mail",
        "checkin": "Check-in",
        "checkout": "Check-out",
        "room": "Quarto",
        "board": "Regime",
        "guests": "Hóspedes",
        "total": "Total",
        "policy": "Política",
        "date": "Data",
        "time": "Hora",
        "party_size": "Pessoas",
        "area": "Área",
        "table": "Mesa",
        "route": "Rota",
        "pax": "Passageiros",
        "flight": "Voo",
        "vehicle": "Veículo",
        "baby_seat": "Cadeira de bebé",
        "price": "Preço",
        "notes": "Notas",
        "yes": "Sim",
        "no": "Não",
        "accommodation_note": "As condições de pagamento e cancelamento estão sujeitas à política de reserva confirmada.",
        "restaurant_note": "Por favor, chegue à hora marcada. Pedidos especiais dependem da disponibilidade operacional.",
        "transfer_note": "Mantenha o telefone disponível perto da hora de recolha. Alterações de voo ou rota devem ser comunicadas à equipa.",
    },
}


DOCUMENT_PROFILE_COPY: dict[str, dict[ConfirmationFormType, dict[str, str]]] = {
    "en": {
        "accommodation": {
            "title": "ACCOMMODATION RESERVATION CONFIRMATION FORM",
            "subtitle": "Accommodation reservation confirmation details",
        },
        "restaurant": {
            "title": "RESTAURANT RESERVATION CONFIRMATION FORM",
            "subtitle": "Restaurant reservation confirmation details",
        },
        "transfer": {
            "title": "TRANSFER RESERVATION CONFIRMATION FORM",
            "subtitle": "Transfer reservation confirmation details",
        },
    },
    "tr": {
        "accommodation": {
            "title": "KONAKLAMA REZERVASYON ONAY FORMU",
            "subtitle": "Konaklama rezervasyon onay detayları",
        },
        "restaurant": {
            "title": "RESTORAN REZERVASYON ONAY FORMU",
            "subtitle": "Restoran rezervasyon onay detayları",
        },
        "transfer": {
            "title": "TRANSFER REZERVASYON ONAY FORMU",
            "subtitle": "Transfer rezervasyon onay detayları",
        },
    },
}

PROMPT_FIELD_LABELS: dict[str, dict[str, str]] = {
    "en": {
        "authorized_confirmation": "Authorized Confirmation",
        "guest_name": "Guest Name",
        "phone_number": "Phone Number",
        "email": "Email Address",
        "reservation_date": "Reservation Date",
        "reservation_time": "Reservation Time",
        "restaurant_guest_count": "Number of Guests",
        "restaurant_seating": "Table Type / Seating Preference",
        "restaurant_area": "Indoor / Outdoor Preference",
        "occasion": "Occasion",
        "special_requests": "Special Requests",
        "transfer_type": "Transfer Type",
        "pickup_location": "Pick-up Location",
        "dropoff_location": "Drop-off Location",
        "transfer_date": "Transfer Date",
        "transfer_time": "Transfer Time",
        "transfer_guests": "Number of Guests",
    },
    "tr": {
        "authorized_confirmation": "Yetkili Onayı / Authorized Confirmation",
        "guest_name": "Misafir Adı / Guest Name",
        "phone_number": "Telefon Numarası / Phone Number",
        "email": "E-posta / Email Address",
        "reservation_date": "Rezervasyon Tarihi / Reservation Date",
        "reservation_time": "Rezervasyon Saati / Reservation Time",
        "restaurant_guest_count": "Kişi Sayısı / Number of Guests",
        "restaurant_seating": "Masa Tipi / Seating Preference",
        "restaurant_area": "İç/Dış Alan Tercihi / Indoor/Outdoor Preference",
        "occasion": "Özel Gün / Occasion",
        "special_requests": "Özel Talepler / Special Requests",
        "transfer_type": "Transfer Tipi / Transfer Type",
        "pickup_location": "Alış Noktası / Pick-up Location",
        "dropoff_location": "Bırakış Noktası / Drop-off Location",
        "transfer_date": "Transfer Tarihi / Transfer Date",
        "transfer_time": "Transfer Saati / Transfer Time",
        "transfer_guests": "Kişi Sayısı / Number of Guests",
    },
}


def normalize_language(language: str | None) -> str:
    """Normalize a language code to the supported active language set."""
    normalized = str(language or "").strip().lower()
    return normalized if normalized in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def copy_for(language: str) -> dict[str, str]:
    """Return localized copy with English fallback for missing keys."""
    normalized = normalize_language(language)
    fallback = COPY[DEFAULT_LANGUAGE]
    selected = COPY.get(normalized, fallback)
    return {**fallback, **selected}


def generate_public_token() -> str:
    """Generate an unguessable public token for a confirmation form."""
    return secrets.token_urlsafe(36)


def token_is_valid(token: str) -> bool:
    """Return True when token shape is acceptable for public lookup."""
    return bool(TOKEN_PATTERN.fullmatch(token.strip()))


def hash_public_token(token: str) -> str:
    """Hash a public token with app secret so plaintext tokens are never stored."""
    secret = settings.app_secret_key or settings.admin_jwt_secret or "velox-confirmation-token"
    return hmac.new(secret.encode("utf-8"), token.encode("utf-8"), sha256).hexdigest()


def public_url_for_token(token: str) -> str:
    """Build the HTTPS public URL for a confirmation token."""
    return f"{settings.public_base_url.rstrip('/')}/confirmations/{token}"


def _contact_phone_display(phone: object) -> str:
    """Return the customer-provided phone value for the confirmation document."""
    return _clean(phone)


def _clean(value: object, fallback: str = "-") -> str:
    """Normalize a display value without fabricating missing details."""
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def _coalesce_clean(*values: object, fallback: str = "-") -> str:
    for value in values:
        text = _clean(value, "")
        if text:
            return text
    return fallback


def _prompt_label(language: str, key: str, fallback: str) -> str:
    language_labels = PROMPT_FIELD_LABELS.get(language)
    if language_labels and key in language_labels:
        return language_labels[key]
    return fallback


def _document_profile(form_type: ConfirmationFormType, language: str, labels: dict[str, str]) -> dict[str, str]:
    language_copy = DOCUMENT_PROFILE_COPY.get(language)
    if language_copy and form_type in language_copy:
        return language_copy[form_type]
    return {"title": labels["confirmed"], "subtitle": labels["intro"]}


def _route_endpoints(route: object) -> tuple[str, str]:
    text = _clean(route, "")
    if not text:
        return "", ""
    parts = [part.strip() for part in ROUTE_SPLIT_PATTERN.split(text, maxsplit=1) if part.strip()]
    if len(parts) >= 2:
        return parts[0], parts[1]
    return "", ""


def _format_bool(value: object, language: str) -> str:
    labels = copy_for(language)
    if isinstance(value, bool):
        return labels["yes"] if value else labels["no"]
    return _clean(value)


def _format_money(value: object, currency: object = "EUR") -> str:
    if value in (None, "") or isinstance(value, bool):
        return "-"
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return _clean(value)
    return f"{amount:.2f} {_clean(currency, 'EUR')}"


def _format_date(value: object) -> str:
    text = _clean(value)
    if text == "-":
        return text
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return parsed.strftime("%d.%m.%Y")
    except ValueError:
        pass
    try:
        parsed_date = datetime.strptime(text, "%Y-%m-%d")  # noqa: DTZ007
        return parsed_date.strftime("%d.%m.%Y")
    except ValueError:
        return text


def _format_generated_at(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%d.%m.%Y %H:%M UTC")


def _hotel_name(profile: HotelProfile | None, language: str, hotel_id: int) -> str:
    if profile is None:
        return f"Hotel {hotel_id}"
    localized = profile.hotel_name
    selected = getattr(localized, language, "") if hasattr(localized, language) else ""
    return str(selected or localized.en or localized.tr or f"Hotel {hotel_id}").strip()


def _room_label(profile: HotelProfile | None, draft: dict[str, Any], language: str) -> str:
    explicit = _clean(draft.get("room_type_name"), "")
    if explicit:
        return explicit
    room_type_id = int(draft.get("room_type_id") or 0)
    if profile is None or room_type_id <= 0:
        return "-"
    for room in profile.room_types:
        if room.pms_room_type_id == room_type_id or room.id == room_type_id:
            selected = getattr(room.name, language, "") if hasattr(room.name, language) else ""
            return _clean(selected or room.name.en or room.name.tr)
    return "-"


def _board_label(profile: HotelProfile | None, draft: dict[str, Any], language: str) -> str:
    explicit = _clean(draft.get("board_type_name"), "")
    if explicit:
        return explicit
    board_code = _clean(draft.get("board_type") or draft.get("board_type_id"), "")
    if profile is None:
        return board_code or "-"
    for board in profile.board_types:
        if str(board.id) == board_code or board.code == board_code:
            selected = getattr(board.name, language, "") if hasattr(board.name, language) else ""
            return _clean(selected or board.name.en or board.name.tr)
    return board_code or "-"


def _guest_count_label(draft: dict[str, Any], language: str) -> str:
    labels = copy_for(language)
    adults = int(draft.get("adults") or 0)
    child_ages = draft.get("chd_ages")
    children = len(child_ages) if isinstance(child_ages, list) else 0
    if children:
        return f"{adults} + {children} {labels['guests'].lower()}"
    return f"{adults} {labels['guests'].lower()}"


def _section(title: str, items: list[ConfirmationDetail]) -> ConfirmationSection:
    return ConfirmationSection(title=title, items=tuple(items))


def build_context_from_hold(
    *,
    approval_type: str,
    hold: asyncpg.Record | dict[str, Any],
    hotel_id: int,
    language: str,
    generated_at: datetime | None = None,
) -> ConfirmationContext:
    """Build a confirmation context from a persisted hold row."""
    form_type = FORM_TYPE_FROM_APPROVAL.get(approval_type.upper())
    if form_type is None:
        raise ValueError("unsupported_confirmation_form_type")
    normalized_language = normalize_language(language)
    labels = copy_for(normalized_language)
    profile = get_profile(hotel_id)
    row = dict(hold)
    now = generated_at or datetime.now(UTC)
    hotel_name = _hotel_name(profile, normalized_language, hotel_id)
    reference_id = _clean(row.get("hold_id"))

    if form_type == "accommodation":
        draft = decode_json_object(row.get("draft_json"))
        customer_name = _clean(draft.get("guest_name"))
        confirmation_no = _clean(row.get("reservation_no") or row.get("voucher_no") or reference_id)
        sections = (
            _section(
                labels["customer_information"],
                [
                    ConfirmationDetail(_prompt_label(normalized_language, "guest_name", labels["guest"]), customer_name, True),
                    ConfirmationDetail(_prompt_label(normalized_language, "phone_number", labels["phone"]), _contact_phone_display(draft.get("phone"))),
                    ConfirmationDetail(_prompt_label(normalized_language, "email", labels["email"]), _clean(draft.get("email"), "")),
                ],
            ),
            _section(
                labels["stay_details"],
                [
                    ConfirmationDetail(labels["checkin"], _format_date(draft.get("checkin_date")), True),
                    ConfirmationDetail(labels["checkout"], _format_date(draft.get("checkout_date")), True),
                    ConfirmationDetail(labels["room"], _room_label(profile, draft, normalized_language)),
                    ConfirmationDetail(labels["board"], _board_label(profile, draft, normalized_language)),
                    ConfirmationDetail(labels["guests"], _guest_count_label(draft, normalized_language)),
                    ConfirmationDetail(
                        labels["total"],
                        _format_money(draft.get("total_price_eur"), draft.get("currency_display") or "EUR"),
                        True,
                    ),
                    ConfirmationDetail(labels["policy"], _clean(draft.get("cancel_policy_type"))),
                    ConfirmationDetail(labels["notes"], _clean(draft.get("notes"))),
                ],
            ),
        )
        return ConfirmationContext(
            form_type=form_type,
            hotel_id=hotel_id,
            hotel_name=hotel_name,
            language=normalized_language,
            customer_name=customer_name,
            phone_display=_contact_phone_display(draft.get("phone")),
            reference_id=reference_id,
            confirmation_no=confirmation_no,
            sections=sections,
            important_note=labels["accommodation_note"],
            generated_at=now,
        )

    if form_type == "restaurant":
        customer_name = _clean(row.get("guest_name"))
        sections = (
            _section(
                labels["customer_information"],
                [
                    ConfirmationDetail(_prompt_label(normalized_language, "guest_name", labels["guest"]), customer_name, True),
                    ConfirmationDetail(_prompt_label(normalized_language, "phone_number", labels["phone"]), _contact_phone_display(row.get("phone"))),
                    ConfirmationDetail(_prompt_label(normalized_language, "email", labels["email"]), _clean(row.get("email"), "")),
                ],
            ),
            _section(
                labels["restaurant_details"],
                [
                    ConfirmationDetail(_prompt_label(normalized_language, "reservation_date", labels["date"]), _format_date(row.get("date")), True),
                    ConfirmationDetail(_prompt_label(normalized_language, "reservation_time", labels["time"]), _clean(row.get("time")), True),
                    ConfirmationDetail(_prompt_label(normalized_language, "restaurant_guest_count", labels["party_size"]), _clean(row.get("party_size"))),
                    ConfirmationDetail(_prompt_label(normalized_language, "restaurant_area", labels["area"]), _clean(row.get("area"))),
                    ConfirmationDetail(_prompt_label(normalized_language, "restaurant_seating", labels["table"]), _clean(row.get("table_id"))),
                    ConfirmationDetail(_prompt_label(normalized_language, "occasion", labels["notes"]), _clean(row.get("occasion"))),
                    ConfirmationDetail(_prompt_label(normalized_language, "special_requests", labels["notes"]), _clean(row.get("notes"))),
                ],
            ),
        )
        return ConfirmationContext(
            form_type=form_type,
            hotel_id=hotel_id,
            hotel_name=hotel_name,
            language=normalized_language,
            customer_name=customer_name,
            phone_display=_contact_phone_display(row.get("phone")),
            reference_id=reference_id,
            confirmation_no=reference_id,
            sections=sections,
            important_note=labels["restaurant_note"],
            generated_at=now,
        )

    customer_name = _clean(row.get("guest_name"))
    pickup_location, dropoff_location = _route_endpoints(row.get("route"))
    sections = (
        _section(
            labels["customer_information"],
            [
                ConfirmationDetail(_prompt_label(normalized_language, "guest_name", labels["guest"]), customer_name, True),
                ConfirmationDetail(_prompt_label(normalized_language, "phone_number", labels["phone"]), _contact_phone_display(row.get("phone"))),
                ConfirmationDetail(_prompt_label(normalized_language, "email", labels["email"]), _clean(row.get("email"), "")),
            ],
        ),
        _section(
            labels["transfer_details"],
            [
                ConfirmationDetail(_prompt_label(normalized_language, "transfer_type", labels["route"]), _coalesce_clean(row.get("transfer_type"), row.get("service_type"), fallback="")),
                ConfirmationDetail(_prompt_label(normalized_language, "pickup_location", labels["route"]), _coalesce_clean(row.get("pickup_location"), row.get("pickup"), pickup_location, fallback=""), True),
                ConfirmationDetail(_prompt_label(normalized_language, "dropoff_location", labels["route"]), _coalesce_clean(row.get("dropoff_location"), row.get("dropoff"), dropoff_location, fallback=""), True),
                ConfirmationDetail(labels["route"], _clean(row.get("route"))),
                ConfirmationDetail(_prompt_label(normalized_language, "transfer_date", labels["date"]), _format_date(row.get("date")), True),
                ConfirmationDetail(_prompt_label(normalized_language, "transfer_time", labels["time"]), _clean(row.get("time")), True),
                ConfirmationDetail(_prompt_label(normalized_language, "transfer_guests", labels["pax"]), _clean(row.get("pax_count"))),
                ConfirmationDetail(labels["vehicle"], _clean(row.get("vehicle_type"))),
                ConfirmationDetail(labels["flight"], _clean(row.get("flight_no"))),
                ConfirmationDetail(labels["baby_seat"], _format_bool(row.get("baby_seat"), normalized_language)),
                ConfirmationDetail(labels["price"], _format_money(row.get("price_eur"), "EUR")),
                ConfirmationDetail(labels["notes"], _clean(row.get("notes"))),
            ],
        ),
    )
    return ConfirmationContext(
        form_type=form_type,
        hotel_id=hotel_id,
        hotel_name=hotel_name,
        language=normalized_language,
        customer_name=customer_name,
        phone_display=_contact_phone_display(row.get("phone")),
        reference_id=reference_id,
        confirmation_no=reference_id,
        sections=sections,
        important_note=labels["transfer_note"],
        generated_at=now,
    )


def build_context_from_manual_payload(
    *,
    form_type: ConfirmationFormType,
    hotel_id: int,
    language: str,
    payload: dict[str, Any],
    generated_at: datetime | None = None,
) -> ConfirmationContext:
    """Build a confirmation context from admin-entered manual form fields."""
    normalized_language = normalize_language(language)
    labels = copy_for(normalized_language)
    profile = get_profile(hotel_id)
    now = generated_at or datetime.now(UTC)
    hotel_name = _hotel_name(profile, normalized_language, hotel_id)
    customer = payload.get("customer") if isinstance(payload.get("customer"), dict) else {}
    details = payload.get("details") if isinstance(payload.get("details"), dict) else {}
    customer_name = _clean(customer.get("guest_name") or payload.get("guest_name"), "")
    phone = customer.get("phone") or payload.get("phone")
    email = customer.get("email") or payload.get("email")
    confirmation_no = _clean(payload.get("confirmation_no") or details.get("confirmation_no"), "")
    reference_id = _clean(payload.get("reference_id") or confirmation_no, "MANUAL-PREVIEW")

    customer_section = _section(
        labels["customer_information"],
        [
            ConfirmationDetail(_prompt_label(normalized_language, "guest_name", labels["guest"]), customer_name, True),
            ConfirmationDetail(_prompt_label(normalized_language, "phone_number", labels["phone"]), _contact_phone_display(phone)),
            ConfirmationDetail(_prompt_label(normalized_language, "email", labels["email"]), _clean(email, "")),
        ],
    )

    if form_type == "accommodation":
        section = _section(
            labels["stay_details"],
            [
                ConfirmationDetail(labels["checkin"], _format_date(details.get("checkin_date")), True),
                ConfirmationDetail(labels["checkout"], _format_date(details.get("checkout_date")), True),
                ConfirmationDetail(labels["room"], _clean(details.get("room"))),
                ConfirmationDetail(labels["board"], _clean(details.get("board"))),
                ConfirmationDetail(labels["guests"], _clean(details.get("guests"))),
                ConfirmationDetail(labels["total"], _clean(details.get("total")), True),
                ConfirmationDetail(labels["policy"], _clean(details.get("policy"))),
                ConfirmationDetail(labels["notes"], _clean(details.get("notes"))),
            ],
        )
        note = labels["accommodation_note"]
    elif form_type == "restaurant":
        section = _section(
            labels["restaurant_details"],
            [
                ConfirmationDetail(_prompt_label(normalized_language, "reservation_date", labels["date"]), _format_date(details.get("date")), True),
                ConfirmationDetail(_prompt_label(normalized_language, "reservation_time", labels["time"]), _clean(details.get("time")), True),
                ConfirmationDetail(_prompt_label(normalized_language, "restaurant_guest_count", labels["party_size"]), _clean(details.get("party_size"))),
                ConfirmationDetail(_prompt_label(normalized_language, "restaurant_area", labels["area"]), _clean(details.get("area"))),
                ConfirmationDetail(_prompt_label(normalized_language, "restaurant_seating", labels["table"]), _clean(details.get("table"))),
                ConfirmationDetail(_prompt_label(normalized_language, "occasion", labels["notes"]), _clean(details.get("occasion"))),
                ConfirmationDetail(_prompt_label(normalized_language, "special_requests", labels["notes"]), _clean(details.get("notes"))),
            ],
        )
        note = labels["restaurant_note"]
    elif form_type == "transfer":
        pickup_location, dropoff_location = _route_endpoints(details.get("route"))
        section = _section(
            labels["transfer_details"],
            [
                ConfirmationDetail(_prompt_label(normalized_language, "transfer_type", labels["route"]), _clean(details.get("transfer_type"))),
                ConfirmationDetail(_prompt_label(normalized_language, "pickup_location", labels["route"]), _coalesce_clean(details.get("pickup_location"), pickup_location, fallback=""), True),
                ConfirmationDetail(_prompt_label(normalized_language, "dropoff_location", labels["route"]), _coalesce_clean(details.get("dropoff_location"), dropoff_location, fallback=""), True),
                ConfirmationDetail(labels["route"], _clean(details.get("route"))),
                ConfirmationDetail(_prompt_label(normalized_language, "transfer_date", labels["date"]), _format_date(details.get("date")), True),
                ConfirmationDetail(_prompt_label(normalized_language, "transfer_time", labels["time"]), _clean(details.get("time")), True),
                ConfirmationDetail(_prompt_label(normalized_language, "transfer_guests", labels["pax"]), _clean(details.get("pax"))),
                ConfirmationDetail(labels["vehicle"], _clean(details.get("vehicle"))),
                ConfirmationDetail(labels["flight"], _clean(details.get("flight_no"))),
                ConfirmationDetail(labels["baby_seat"], _format_bool(details.get("baby_seat"), normalized_language)),
                ConfirmationDetail(labels["price"], _clean(details.get("price")), True),
                ConfirmationDetail(labels["notes"], _clean(details.get("notes"))),
            ],
        )
        note = labels["transfer_note"]
    else:
        raise ValueError("unsupported_confirmation_form_type")

    return ConfirmationContext(
        form_type=form_type,
        hotel_id=hotel_id,
        hotel_name=hotel_name,
        language=normalized_language,
        customer_name=customer_name,
        phone_display=_contact_phone_display(phone),
        reference_id=reference_id,
        confirmation_no=confirmation_no,
        sections=(customer_section, section),
        important_note=note,
        generated_at=now,
    )


def render_confirmation_html(context: ConfirmationContext) -> str:
    """Render a premium A4 line-form confirmation document."""
    labels = copy_for(context.language)
    dir_attr = "rtl" if context.language == "ar" else "ltr"
    document = _document_profile(context.form_type, context.language, labels)
    document_sections = _render_document_sections(context, labels)
    footer_note_html = _render_footer_note(context)
    brand_primary, brand_place = _brand_lockup_names(context.hotel_name)
    brand_place_html = f'<div class="brand-place">{escape(brand_place)}</div>' if brand_place else ""
    motif_class = f"motif-{context.form_type}"
    variant_class = _document_variant_class(context.form_type)
    type_ornament = _render_type_ornament(context.form_type)
    map_art = _render_map_linework()
    return f"""<!doctype html>
<html lang="{escape(context.language)}" dir="{dir_attr}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="robots" content="noindex,nofollow">
  <title>{escape(context.hotel_name)} · {escape(document["title"])}</title>
  <style>
    :root {{
      --page:#eef2fb; --paper:#ffffff; --ink:#172036; --near:#10172a;
      --primary:#192f9a; --primary-deep:#10206f; --primary-soft:#e8edff;
      --accent:#c79a2d; --accent-soft:#fbf3df; --teal:#0f7f8c;
      --fume:#38415f; --muted:#6c7288; --line:#8f9bd2; --soft-line:#dbe2ff;
      --hair:var(--primary); --wash:rgba(232,237,255,.56); --type-accent:var(--primary);
      --sans:"Aviano Sans", "Avenir Next", Montserrat, "Century Gothic", "Segoe UI", ui-sans-serif, system-ui, sans-serif;
      --display:"Aviano Sans", "Avenir Next", Montserrat, "Century Gothic", "Segoe UI", ui-sans-serif, system-ui, sans-serif;
    }}
    * {{ box-sizing:border-box; }}
    body {{
      margin:0; background:var(--page); color:var(--ink);
      font-family:var(--sans);
      line-height:1.45;
    }}
    .page {{ max-width:900px; margin:0 auto; padding:24px 18px; }}
    .sheet {{
      position:relative; overflow:hidden; isolation:isolate; color:var(--ink);
      width:min(100%, 794px); min-height:1123px; margin:0 auto; padding:36px 48px 30px;
      border:1px solid rgba(25,47,154,.34); box-shadow:0 26px 80px rgba(16,32,111,.14);
      background:
        linear-gradient(90deg, rgba(25,47,154,.035) 1px, transparent 1px),
        linear-gradient(0deg, rgba(25,47,154,.028) 1px, transparent 1px),
        var(--paper);
      background-size:38px 38px, 38px 38px, auto;
    }}
    .sheet::before {{
      content:""; position:absolute; inset:9px; border:1px solid rgba(25,47,154,.3);
      pointer-events:none; z-index:0;
    }}
    .sheet::after {{
      content:""; position:absolute; inset:17px; border:1px solid rgba(199,154,45,.22);
      pointer-events:none; z-index:0;
    }}
    .corner {{ position:absolute; z-index:2; width:34px; height:34px; pointer-events:none; }}
    .corner-tl {{ top:7px; left:7px; border-top:2px solid rgba(25,47,154,.56); border-left:2px solid rgba(25,47,154,.56); border-top-left-radius:24px; }}
    .corner-tr {{ top:7px; right:7px; border-top:2px solid rgba(25,47,154,.56); border-right:2px solid rgba(25,47,154,.56); border-top-right-radius:24px; }}
    .corner-bl {{ bottom:7px; left:7px; border-bottom:2px solid rgba(25,47,154,.56); border-left:2px solid rgba(25,47,154,.56); border-bottom-left-radius:24px; }}
    .corner-br {{ bottom:7px; right:7px; border-bottom:2px solid rgba(25,47,154,.56); border-right:2px solid rgba(25,47,154,.56); border-bottom-right-radius:24px; }}
    .linework,.map-art {{ position:absolute; inset:0; pointer-events:none; z-index:0; color:rgba(25,47,154,.3); }}
    .linework .route-left {{ position:absolute; left:18px; top:18px; width:128px; height:128px; border-top:1px dashed rgba(25,47,154,.28); border-left:1px dashed rgba(25,47,154,.24); border-radius:50%; }}
    .linework .route-right {{ position:absolute; right:20px; top:500px; width:64px; height:250px; border-right:1px dashed rgba(25,47,154,.32); border-radius:50%; transform:rotate(-6deg); }}
    .linework .pin {{ position:absolute; width:15px; height:15px; border:1px solid rgba(25,47,154,.62); border-radius:50%; }}
    .linework .pin::after {{ content:""; position:absolute; inset:4px; border-radius:50%; background:rgba(25,47,154,.48); }}
    .linework .pin-a {{ top:640px; left:24px; }}
    .linework .pin-b {{ right:54px; top:116px; }}
    .linework .arrow {{ position:absolute; width:0; height:0; border-top:7px solid transparent; border-bottom:7px solid transparent; border-left:9px solid rgba(25,47,154,.48); }}
    .linework .arrow-right {{ right:35px; top:680px; transform:rotate(106deg); }}
    .starburst {{ position:absolute; top:62px; right:78px; width:56px; height:56px; z-index:1; opacity:.55; }}
    .starburst::before {{
      content:""; position:absolute; inset:0; border-radius:50%;
      background:repeating-conic-gradient(from 0deg, rgba(199,154,45,.72) 0deg 4deg, transparent 4deg 12deg);
      -webkit-mask:radial-gradient(circle, transparent 0 7px, #000 8px 29px, transparent 30px);
      mask:radial-gradient(circle, transparent 0 7px, #000 8px 29px, transparent 30px);
    }}
    .starburst::after {{ content:""; position:absolute; inset:22px; border:1px solid rgba(25,47,154,.58); border-radius:50%; background:var(--paper); }}
    .decor-map {{ position:absolute; opacity:.55; }}
    .decor-map path,.decor-map circle,.decor-map line {{ fill:none; stroke:currentColor; stroke-width:1; }}
    .decor-map .thin {{ opacity:.35; }}
    .decor-map .dash {{ stroke-dasharray:6 7; opacity:.54; }}
    .decor-map.top {{ top:-18px; right:-6px; width:375px; height:210px; }}
    .decor-map.bottom {{ left:-28px; bottom:-4px; width:360px; height:235px; transform:rotate(-2deg); }}
    .decor-dots {{ position:absolute; right:86px; bottom:96px; width:86px; height:86px; opacity:.24; background-image:radial-gradient(rgba(25,47,154,.36) 1.2px, transparent 1.2px); background-size:12px 12px; transform:rotate(-15deg); }}
    .letterhead,.hero,.document-body,.confirmation-note,.doc-footer {{ position:relative; z-index:1; }}
    .letterhead {{ display:flex; justify-content:center; align-items:center; min-height:112px; padding-top:2px; }}
    .brand-lockup {{
      min-width:300px; max-width:360px; padding:10px 24px 13px; text-align:center;
      border:1px solid rgba(25,47,154,.42); background:rgba(255,255,255,.84);
    }}
    .brand-name {{
      font-family:var(--display); font-size:30px; line-height:1.04;
      letter-spacing:0; color:var(--primary); font-weight:800;
    }}
    .brand-place {{
      display:block; margin-top:5px; font-size:12px; letter-spacing:0;
      text-transform:uppercase; color:var(--muted); font-weight:700;
    }}
    .divider {{ position:relative; height:1px; margin:14px 0 30px; background:rgba(25,47,154,.34); }}
    .divider::after,.mini-divider::after,.footer-seal::before {{ content:"✦"; position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); color:var(--hair); background:var(--paper); padding:0 12px; font-size:15px; line-height:1; }}
    .hero {{ text-align:center; margin-bottom:22px; }}
    h1 {{
      margin:0 auto 5px; max-width:704px; font-family:var(--display);
      font-size:27px; line-height:1.13; font-weight:800; letter-spacing:0; color:var(--primary-deep);
      text-transform:uppercase;
    }}
    .subtitle {{ margin:0; color:var(--fume); font-size:14px; letter-spacing:0; }}
    .mini-divider {{ position:relative; width:206px; max-width:58%; height:1px; margin:18px auto 0; background:rgba(25,47,154,.34); }}
    .document-body {{ max-width:670px; margin:0 auto; }}
    .document-section {{ margin:0 0 16px; }}
    .section-heading {{ display:flex; align-items:center; gap:10px; margin:0 0 9px; color:var(--primary-deep); }}
    .section-star {{ font-size:14px; line-height:1; color:var(--accent); }}
    .section-number {{ font-size:10px; font-weight:800; min-width:15px; color:var(--primary); }}
    .section-title {{ margin:0; font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:0; white-space:nowrap; }}
    .section-rule {{ flex:1; height:1px; border-top:1px dotted rgba(25,47,154,.34); position:relative; }}
    .section-rule::after {{ content:""; position:absolute; right:0; top:-2px; width:28px; border-top:1px solid rgba(25,47,154,.58); transform:skewX(-28deg); }}
    .document-fields {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); column-gap:28px; row-gap:9px; }}
    .section-status .document-fields {{ grid-template-columns:repeat(3,minmax(0,1fr)); column-gap:22px; }}
    .line-field {{ display:grid; grid-template-columns:minmax(92px,auto) 12px minmax(70px,1fr); align-items:end; min-height:23px; break-inside:avoid; }}
    .line-label {{ color:var(--fume); font-size:11px; font-family:var(--sans); font-weight:700; white-space:nowrap; }}
    .line-label em {{ color:var(--muted); font-size:10px; font-style:normal; font-weight:600; }}
    .line-colon {{ color:var(--fume); font-size:11px; text-align:center; }}
    .line-value {{ min-height:18px; border-bottom:1px solid var(--soft-line); color:var(--near); font-size:12px; font-weight:650; overflow-wrap:anywhere; padding:0 4px 2px; }}
    .line-field.is-wide {{ grid-column:1 / -1; }}
    .line-field.is-emphasis .line-value {{ border-bottom-color:var(--line); }}
    .notes-box {{ position:relative; min-height:68px; border:1px solid rgba(25,47,154,.26); background:var(--wash); padding:10px 16px 10px; }}
    .notes-box::before,.notes-box::after {{ content:""; position:absolute; width:15px; height:15px; border-color:rgba(25,47,154,.48); }}
    .notes-box::before {{ top:-1px; left:-1px; border-top:1px solid; border-left:1px solid; }}
    .notes-box::after {{ right:-1px; bottom:-1px; border-right:1px solid; border-bottom:1px solid; }}
    .notes-label {{ display:block; color:var(--fume); font-size:11px; font-family:var(--sans); font-weight:700; margin-bottom:8px; }}
    .notes-label em {{ color:var(--muted); font-size:10px; font-style:normal; }}
    .notes-text {{ margin:0; min-height:44px; color:var(--near); font-size:12px; font-weight:600; white-space:pre-wrap; overflow-wrap:anywhere; }}
    .note-lines {{ height:40px; background:repeating-linear-gradient(to bottom, transparent 0 15px, var(--soft-line) 15px 16px); }}
    .footer-seal {{ width:70px; height:70px; margin:6px auto 0; border:1px solid rgba(25,47,154,.36); display:flex; align-items:center; justify-content:center; position:relative; color:var(--primary); font-family:var(--display); font-size:38px; font-weight:800; background:rgba(255,255,255,.9); }}
    .footer-seal::before {{ top:0; background:transparent; font-size:13px; }}
    .confirmation-note {{ max-width:600px; margin:8px auto 0; text-align:center; color:var(--fume); }}
    .confirmation-note .note-line {{ position:relative; height:1px; width:378px; max-width:72%; margin:0 auto 12px; background:rgba(25,47,154,.34); }}
    .confirmation-note .note-line::after,.confirmation-note .note-mark::after {{ content:"✦"; position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); background:var(--paper); padding:0 12px; color:var(--hair); font-size:14px; }}
    .confirmation-note p {{ margin:0 auto 7px; font-size:11px; line-height:1.45; max-width:540px; }}
    .confirmation-note .note-secondary {{ color:var(--muted); font-size:11px; }}
    .confirmation-note .note-mark {{ position:relative; width:82px; height:1px; margin:6px auto 0; background:rgba(25,47,154,.3); }}
    .doc-footer {{ margin:12px auto 0; max-width:684px; display:flex; justify-content:space-between; gap:14px; color:var(--muted); font-size:9px; letter-spacing:0; }}
    .type-ornament {{ position:absolute; pointer-events:none; z-index:0; color:var(--type-accent); opacity:.42; }}
    .ornament-accommodation {{ left:62px; top:144px; width:168px; height:42px; border-top:1px solid currentColor; border-bottom:1px solid currentColor; opacity:.36; }}
    .ornament-accommodation::before {{ content:""; position:absolute; left:0; right:0; top:16px; border-top:1px dotted currentColor; }}
    .ornament-accommodation::after {{ content:"STAY"; position:absolute; right:0; top:18px; font-size:9px; letter-spacing:0; color:currentColor; }}
    .ornament-restaurant {{ right:76px; top:162px; width:116px; height:116px; border:1px solid currentColor; border-radius:50%; opacity:.34; }}
    .ornament-restaurant::before {{ content:""; position:absolute; inset:22px; border:1px solid currentColor; border-radius:50%; }}
    .ornament-restaurant::after {{ content:""; position:absolute; left:-30px; top:30px; width:18px; height:58px; border-left:1px solid currentColor; border-right:1px solid currentColor; box-shadow:6px 0 0 rgba(15,127,140,.16); }}
    .ornament-transfer {{ left:54px; right:54px; top:174px; height:58px; border-top:1px dashed currentColor; opacity:.38; transform:skewY(-3deg); }}
    .ornament-transfer::before,.ornament-transfer::after {{ content:""; position:absolute; top:-6px; width:11px; height:11px; border:1px solid currentColor; border-radius:50%; background:var(--paper); }}
    .ornament-transfer::before {{ left:0; }}
    .ornament-transfer::after {{ right:0; }}
    .template-accommodation-ledger .letterhead {{ min-height:116px; }}
    .template-accommodation-ledger {{ --type-accent:var(--primary); }}
    .template-accommodation-ledger .brand-lockup {{ box-shadow:0 0 0 6px rgba(232,237,255,.64), inset 0 0 0 1px rgba(25,47,154,.12); }}
    .template-accommodation-ledger .document-body {{ max-width:664px; }}
    .template-accommodation-ledger .section-customer .document-fields {{ grid-template-columns:1fr; row-gap:8px; }}
    .template-accommodation-ledger .section-status {{ padding-top:4px; }}
    .template-accommodation-ledger .section-status .document-fields {{ grid-template-columns:repeat(3,minmax(0,1fr)); column-gap:22px; padding:12px 0 2px; border-top:1px solid rgba(25,47,154,.18); border-bottom:1px solid rgba(25,47,154,.18); }}
    .sheet.template-restaurant-table {{ --type-accent:var(--teal); background:var(--paper); }}
    .template-restaurant-table .letterhead {{ justify-content:flex-start; min-height:94px; padding-left:18px; }}
    .template-restaurant-table .brand-lockup {{ min-width:292px; max-width:382px; padding:9px 20px 12px; border-left:0; border-right:0; background:rgba(255,255,255,.8); }}
    .template-restaurant-table .brand-name {{ font-size:26px; }}
    .template-restaurant-table .brand-place {{ font-size:10px; }}
    .template-restaurant-table .divider {{ margin:8px 0 22px; }}
    .template-restaurant-table .hero {{ text-align:left; margin:0 0 18px 34px; padding-left:24px; border-left:2px solid rgba(15,127,140,.48); }}
    .template-restaurant-table h1 {{ margin-left:0; max-width:548px; font-size:25px; }}
    .template-restaurant-table .subtitle {{ max-width:420px; }}
    .template-restaurant-table .mini-divider {{ margin-left:0; width:172px; }}
    .template-restaurant-table .document-body {{ max-width:642px; border:1px solid rgba(15,127,140,.22); padding:16px 18px 10px; background:rgba(255,255,255,.72); }}
    .template-restaurant-table .document-section {{ margin-bottom:13px; }}
    .template-restaurant-table .section-heading {{ gap:8px; }}
    .template-restaurant-table .section-star {{ font-size:12px; }}
    .template-restaurant-table .section-rule::after {{ width:44px; transform:none; }}
    .template-restaurant-table .line-label {{ white-space:normal; }}
    .template-restaurant-table .section-details .document-fields {{ grid-template-columns:repeat(2,minmax(0,1fr)); column-gap:24px; }}
    .template-restaurant-table .section-notes .notes-box {{ min-height:58px; border-left:0; border-right:0; }}
    .template-restaurant-table .confirmation-note {{ margin-top:10px; }}
    .template-transfer-route .letterhead {{ justify-content:flex-start; min-height:108px; padding-left:4px; }}
    .template-transfer-route {{ --type-accent:var(--accent); }}
    .template-transfer-route .brand-lockup {{ min-width:318px; max-width:404px; text-align:left; border:0; background:transparent; padding:8px 0 10px 22px; }}
    .template-transfer-route .brand-place {{ margin-left:70px; }}
    .template-transfer-route .divider {{ margin:8px 0 28px; }}
    .template-transfer-route .hero {{ margin-bottom:20px; }}
    .template-transfer-route h1 {{ font-size:29px; }}
    .template-transfer-route .document-body {{ max-width:690px; }}
    .template-transfer-route .section-details {{ position:relative; padding:12px 15px 12px; border-left:1px dashed rgba(199,154,45,.46); border-right:1px dashed rgba(199,154,45,.46); }}
    .template-transfer-route .section-details::before {{ content:""; position:absolute; left:20px; right:20px; top:46%; border-top:1px dashed rgba(199,154,45,.22); z-index:-1; }}
    .template-transfer-route .section-details .document-fields {{ grid-template-columns:repeat(2,minmax(0,1fr)); column-gap:24px; row-gap:10px; }}
    .template-transfer-route .section-details .line-field.is-wide {{ grid-column:1 / -1; }}
    .template-transfer-route .section-status .document-fields {{ grid-template-columns:repeat(3,minmax(0,1fr)); }}
    .motif-accommodation .decor-map.top {{ opacity:.2; }}
    .motif-accommodation .decor-map.bottom {{ opacity:.34; }}
    .motif-accommodation .linework .route-right,.motif-accommodation .linework .pin-b,.motif-accommodation .linework .arrow-right {{ display:none; }}
    .motif-restaurant .decor-map.top,.motif-restaurant .decor-map.bottom,.motif-restaurant .linework .route-left,.motif-restaurant .linework .route-right,.motif-restaurant .linework .pin,.motif-restaurant .linework .arrow {{ display:none; }}
    .motif-restaurant .decor-dots {{ right:78px; top:312px; bottom:auto; width:56px; height:56px; opacity:.18; }}
    .motif-transfer .starburst {{ top:72px; right:72px; }}
    @page {{ size:A4; margin:0; }}
    @media(max-width:760px) {{
      .page {{ padding:16px; }}
      .sheet {{ min-height:0; padding:34px 24px 30px; }}
      .brand-lockup {{ min-width:0; width:78%; padding:9px 14px 12px; }}
      .brand-name {{ font-size:24px; }}
      h1 {{ font-size:23px; }}
      .type-ornament {{ display:none; }}
      .template-restaurant-table .letterhead,.template-transfer-route .letterhead {{ justify-content:center; padding-left:0; }}
      .template-restaurant-table .hero {{ margin-left:0; padding-left:16px; }}
      .template-restaurant-table .document-body {{ padding:14px 14px 8px; }}
      .document-fields,.section-status .document-fields {{ grid-template-columns:1fr; }}
      .template-accommodation-ledger .section-status .document-fields,.template-restaurant-table .section-details .document-fields,.template-transfer-route .section-details .document-fields {{ grid-template-columns:1fr; }}
      .line-field.is-wide {{ grid-column:auto; }}
      .doc-footer {{ flex-direction:column; }}
    }}
    @media print {{
      body {{ background:#fff; }}
      .page {{ padding:0; max-width:none; }}
      .sheet {{ box-shadow:none; width:794px; min-height:1123px; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <article class="sheet {motif_class} {variant_class}" aria-label="{escape(labels["document_title"])}">
      <span class="corner corner-tl"></span><span class="corner corner-tr"></span><span class="corner corner-bl"></span><span class="corner corner-br"></span>
      {map_art}
      <div class="linework" aria-hidden="true">
        <span class="route-left"></span><span class="route-right"></span><span class="pin pin-a"></span><span class="pin pin-b"></span><span class="arrow arrow-right"></span><span class="decor-dots"></span>
      </div>
      <span class="starburst" aria-hidden="true"></span>
      {type_ornament}
      <header class="letterhead">
        <div class="brand-lockup">
          <div class="brand-name">{escape(brand_primary)}</div>
          {brand_place_html}
        </div>
      </header>
      <div class="divider" aria-hidden="true"></div>
      <section class="hero">
        <h1>{escape(document["title"])}</h1>
        <p class="subtitle">{escape(document["subtitle"])}</p>
        <div class="mini-divider" aria-hidden="true"></div>
      </section>
      <section class="document-body" aria-label="{escape(labels["confirmation_information"])}">
        {document_sections}
      </section>
      <section class="confirmation-note">
        <div class="note-line" aria-hidden="true"></div>
        {footer_note_html}
        <div class="note-mark" aria-hidden="true"></div>
        <div class="footer-seal" aria-hidden="true">{escape(brand_primary[:1].upper() or "K")}</div>
      </section>
      <footer class="doc-footer">
        <span>{escape(context.hotel_name)}</span>
        <span>{escape(_document_extra_label(context.language, "official_document"))}</span>
      </footer>
    </article>
  </main>
</body>
</html>"""


def _render_document_sections(
    context: ConfirmationContext,
    labels: dict[str, str],
) -> str:
    customer_section = context.sections[0] if context.sections else _section(labels["customer_information"], [])
    detail_section = context.sections[1] if len(context.sections) > 1 else _section(labels["confirmation_information"], [])
    detail_items = tuple(item for item in detail_section.items if not _is_note_label(item.label, labels))
    notes_item = _extract_note_item(detail_section.items, labels)
    status_section = _build_status_section(context, detail_items, labels)
    authorization_section = _build_authorization_section(context, labels)
    sections = (
        (1, customer_section.title, customer_section.items, "section-customer"),
        (2, detail_section.title, detail_items, "section-details"),
        (3, status_section.title, status_section.items, "section-status"),
        (4, _document_extra_label(context.language, "notes_requests"), (notes_item,), "section-notes"),
        (5, authorization_section.title, authorization_section.items, "section-authorization"),
    )
    return "\n".join(
        _render_document_section(context.language, number, title, items, class_name, labels)
        for number, title, items, class_name in sections
    )


def _render_document_section(
    language: str,
    number: int,
    title: str,
    items: tuple[ConfirmationDetail, ...],
    class_name: str,
    labels: dict[str, str],
) -> str:
    heading = (
        '<div class="section-heading">'
        '<span class="section-star">✦</span>'
        f'<span class="section-number">{number}.</span>'
        f'<h2 class="section-title">{escape(title)}</h2>'
        '<span class="section-rule" aria-hidden="true"></span>'
        "</div>"
    )
    if class_name == "section-notes":
        body = _render_notes_box(items[0] if items else ConfirmationDetail(labels["notes"], ""))
    else:
        body = '<div class="document-fields">' + "\n".join(_render_line_field(item, labels) for item in items) + "</div>"
    return f'<section class="document-section {class_name}" lang="{escape(language)}">{heading}{body}</section>'


def _render_line_field(item: ConfirmationDetail, labels: dict[str, str]) -> str:
    emphasis_class = " is-emphasis" if item.emphasis else ""
    wide_class = " is-wide" if _is_wide_line_field(item.label, labels) else ""
    main_label, hint_label = _split_field_label(item.label)
    hint_html = f" <em>/ {escape(hint_label)}</em>" if hint_label else ""
    value = escape(_display_value(item.value)) or "&nbsp;"
    return (
        f'<div class="line-field{wide_class}{emphasis_class}">'
        f'<span class="line-label">{escape(main_label)}{hint_html}</span>'
        '<span class="line-colon">:</span>'
        f'<span class="line-value">{value}</span>'
        "</div>"
    )


def _render_notes_box(item: ConfirmationDetail) -> str:
    main_label, hint_label = _split_field_label(item.label)
    hint_html = f" <em>/ {escape(hint_label)}</em>" if hint_label else ""
    value = _display_value(item.value)
    content = f'<p class="notes-text">{escape(value)}</p>' if value else '<div class="note-lines" aria-hidden="true"></div>'
    return f'<div class="notes-box"><span class="notes-label">{escape(main_label)}{hint_html}</span>{content}</div>'


def _build_status_section(
    context: ConfirmationContext,
    detail_items: tuple[ConfirmationDetail, ...],
    labels: dict[str, str],
) -> ConfirmationSection:
    total_or_price = _field_value(detail_items, labels["total"], labels["price"], "total", "price", "fiyat")
    payment_status_label = _document_extra_label(context.language, "payment_status")
    title_key = "payment_status_section" if context.form_type == "accommodation" else "status_section"
    items = [
        ConfirmationDetail(_document_extra_label(context.language, "reservation_number"), context.confirmation_no, True),
        ConfirmationDetail(_document_extra_label(context.language, "reservation_status"), labels["confirmed_status"], True),
    ]
    if context.form_type == "accommodation":
        items.extend(
            [
                ConfirmationDetail(_document_extra_label(context.language, "number_of_nights"), _night_count(detail_items, labels)),
                ConfirmationDetail(payment_status_label, ""),
                ConfirmationDetail(_document_extra_label(context.language, "total_amount"), total_or_price, True),
                ConfirmationDetail(_document_extra_label(context.language, "deposit"), ""),
                ConfirmationDetail(_document_extra_label(context.language, "balance_due"), ""),
            ]
        )
    else:
        items.extend(
            [
                ConfirmationDetail(_document_extra_label(context.language, "total_amount"), total_or_price, True),
            ]
        )
    return ConfirmationSection(title=_document_extra_label(context.language, title_key), items=tuple(items))


def _build_authorization_section(context: ConfirmationContext, labels: dict[str, str]) -> ConfirmationSection:
    return ConfirmationSection(
        title=_document_extra_label(context.language, "authorization"),
        items=(
            ConfirmationDetail(_document_extra_label(context.language, "prepared_by"), context.hotel_name),
            ConfirmationDetail(_document_extra_label(context.language, "date"), _format_generated_at(context.generated_at)),
            ConfirmationDetail(_prompt_label(context.language, "authorized_confirmation", labels["confirmation_information"]), context.hotel_name, True),
            ConfirmationDetail(_document_extra_label(context.language, "signature"), ""),
        ),
    )


def _extract_note_item(items: tuple[ConfirmationDetail, ...], labels: dict[str, str]) -> ConfirmationDetail:
    for item in items:
        if _is_note_label(item.label, labels):
            return item
    return ConfirmationDetail(labels["notes"], "")


def _display_value(value: str) -> str:
    return "" if not value or value == "-" else value


def _is_wide_line_field(label: str, labels: dict[str, str]) -> bool:
    return _label_contains(
        label,
        labels["route"],
        "transfer type",
        "transfer tipi",
        "pickup",
        "drop-off",
        "reservation number",
        "rezervasyon numarası",
        "authorized confirmation",
        "yetkili onayı",
    )


def _field_value(items: tuple[ConfirmationDetail, ...], *needles: str) -> str:
    for item in items:
        if _label_contains(item.label, *needles):
            value = _display_value(item.value)
            if value:
                return value
    return ""


def _night_count(items: tuple[ConfirmationDetail, ...], labels: dict[str, str]) -> str:
    checkin = _parse_display_date(_field_value(items, labels["checkin"], "check-in", "giriş"))
    checkout = _parse_display_date(_field_value(items, labels["checkout"], "check-out", "çıkış"))
    if not checkin or not checkout:
        return ""
    nights = (checkout - checkin).days
    return str(nights) if nights > 0 else ""


def _parse_display_date(value: str) -> datetime | None:
    if not value:
        return None
    for date_format in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, date_format)  # noqa: DTZ007
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _brand_lockup_names(hotel_name: str) -> tuple[str, str]:
    brand = _clean(hotel_name, "")
    return brand, ""


def _document_variant_class(form_type: ConfirmationFormType) -> str:
    variants = {
        "accommodation": "template-accommodation-ledger",
        "restaurant": "template-restaurant-table",
        "transfer": "template-transfer-route",
    }
    return variants[form_type]


def _render_type_ornament(form_type: ConfirmationFormType) -> str:
    return f'<div class="type-ornament ornament-{escape(form_type)}" aria-hidden="true"></div>'


def _document_extra_label(language: str, key: str) -> str:
    labels = {
        "en": {
            "payment_status_section": "Payment & Status",
            "status_section": "Reservation Status",
            "notes_requests": "Special Notes / Requests",
            "authorization": "Authorization",
            "reservation_number": "Reservation Number",
            "reservation_status": "Reservation Status",
            "payment_status": "Payment Status",
            "total_amount": "Total Amount",
            "number_of_nights": "Number of Nights",
            "deposit": "Deposit",
            "balance_due": "Balance Due",
            "prepared_by": "Prepared By",
            "date": "Date",
            "signature": "Signature",
            "official_document": "Official Reservation Document",
        },
        "tr": {
            "payment_status_section": "Ödeme ve Durum",
            "status_section": "Rezervasyon Durumu",
            "notes_requests": "Özel Notlar / Talepler",
            "authorization": "Yetkilendirme",
            "reservation_number": "Rezervasyon Numarası",
            "reservation_status": "Rezervasyon Durumu",
            "payment_status": "Ödeme Durumu",
            "total_amount": "Toplam Tutar",
            "number_of_nights": "Gece Sayısı",
            "deposit": "Depozito",
            "balance_due": "Kalan Tutar",
            "prepared_by": "Hazırlayan",
            "date": "Tarih",
            "signature": "İmza",
            "official_document": "Resmi Rezervasyon Belgesi",
        },
    }
    selected = labels.get(normalize_language(language), labels["en"])
    return selected.get(key, labels["en"][key])


def _is_note_label(label: str, labels: dict[str, str]) -> bool:
    return _label_contains(label, labels["notes"], "special request", "special note", "özel talep", "özel not")


def _label_contains(label: str, *needles: str) -> bool:
    normalized = label.casefold()
    return any(needle and needle.casefold() in normalized for needle in needles)


def _split_field_label(label: str) -> tuple[str, str]:
    main, separator, hint = label.partition(" / ")
    if not separator:
        return label, ""
    return main.strip(), hint.strip()


def _render_footer_note(context: ConfirmationContext) -> str:
    primary = escape(context.important_note)
    english_note = COPY["en"][f"{context.form_type}_note"]
    if context.language == "en" or english_note == context.important_note:
        return f"<p>{primary}</p>"
    return f'<p>{primary}</p><p class="note-secondary">{escape(english_note)}</p>'


def _render_map_linework() -> str:
    return """
      <svg class="decor-map top map-art" viewBox="0 0 360 220" aria-hidden="true">
        <path class="thin" d="M88 12c24 22 66 23 88 45 25 25-7 53 24 73 35 23 93 10 126 47"/>
        <path class="thin" d="M133 2c34 36 75 29 106 49 32 21 27 59 70 79"/>
        <path class="thin" d="M196 2c24 14 45 17 74 18 34 1 56 25 80 45"/>
        <path class="thin" d="M238 12c28 10 45 13 77 13 21 0 34 18 43 32"/>
        <path class="dash" d="M64 6c28 49 102 69 150 93 45 22 75 53 112 93"/>
        <circle cx="312" cy="127" r="10"/><circle cx="312" cy="127" r="3"/>
        <path d="M312 99c12 0 21 9 21 20 0 19-21 36-21 36s-21-17-21-36c0-11 9-20 21-20z"/>
      </svg>
      <svg class="decor-map bottom map-art" viewBox="0 0 360 235" aria-hidden="true">
        <path class="thin" d="M7 174c40-23 44-65 66-99 29-45 79-45 118-71"/>
        <path class="thin" d="M2 200c47-25 54-75 80-112 32-46 83-47 123-73"/>
        <path class="thin" d="M25 232c48-31 57-81 88-114 35-38 77-44 111-75"/>
        <path class="dash" d="M12 128c28-18 56-24 82-18 41 10 44 63 92 78 32 10 75-7 115-24"/>
        <circle cx="150" cy="171" r="8"/><circle cx="150" cy="171" r="3"/>
      </svg>"""


def render_whatsapp_message(context: ConfirmationContext, public_url: str) -> str:
    """Render short WhatsApp text containing the secure confirmation link."""
    labels = copy_for(context.language)
    type_label = labels[context.form_type]
    return (
        f"{labels['confirmed']}\n"
        f"{labels['confirmation_no']}: {context.confirmation_no}\n"
        f"{type_label}: {labels['confirmed_status']}\n\n"
        f"{labels['form_link_line']}\n{public_url}"
    )


def build_preview(context: ConfirmationContext, public_url: str = "https://example.com/confirmations/preview") -> ConfirmationPreview:
    """Render a preview without persisting a public token."""
    html = render_confirmation_html(context)
    return ConfirmationPreview(
        context=context,
        html=html,
        whatsapp_message=render_whatsapp_message(context, public_url),
    )


async def resolve_language_for_hold(
    conn: asyncpg.Connection,
    hold: asyncpg.Record | dict[str, Any],
    requested_language: str | None,
) -> str:
    """Resolve form language from explicit admin selection, conversation language, then default."""
    explicit = normalize_language(requested_language)
    if requested_language and explicit in SUPPORTED_LANGUAGES:
        return explicit
    row = dict(hold)
    conversation_id = row.get("conversation_id")
    if conversation_id:
        language = await conn.fetchval("SELECT language FROM conversations WHERE id = $1", conversation_id)
        normalized = normalize_language(str(language or ""))
        if normalized in SUPPORTED_LANGUAGES:
            return normalized
    return DEFAULT_LANGUAGE


async def load_hold_for_form(
    conn: asyncpg.Connection,
    *,
    hotel_id: int,
    form_type: ConfirmationFormType,
    reference_id: str,
) -> asyncpg.Record:
    """Load a hold row for a confirmation form."""
    approval_type = APPROVAL_TYPE_FROM_FORM[form_type]
    if approval_type == "STAY":
        row = await conn.fetchrow("SELECT * FROM stay_holds WHERE hotel_id = $1 AND hold_id = $2", hotel_id, reference_id)
    elif approval_type == "RESTAURANT":
        row = await conn.fetchrow(
            "SELECT * FROM restaurant_holds WHERE hotel_id = $1 AND hold_id = $2",
            hotel_id,
            reference_id,
        )
    else:
        row = await conn.fetchrow(
            "SELECT * FROM transfer_holds WHERE hotel_id = $1 AND hold_id = $2",
            hotel_id,
            reference_id,
        )
    if row is None:
        raise ValueError("confirmation_source_hold_not_found")
    return row


async def create_confirmation_form(
    conn: asyncpg.Connection,
    *,
    context: ConfirmationContext,
    generated_by: str,
    expiry_days: int = DEFAULT_EXPIRY_DAYS,
) -> ConfirmationDelivery:
    """Persist a confirmation form snapshot and return its secure public URL."""
    token = generate_public_token()
    public_url = public_url_for_token(token)
    html = render_confirmation_html(context)
    whatsapp_message = render_whatsapp_message(context, public_url)
    token_hash = hash_public_token(token)
    token_prefix = token[:8]
    payload = {
        "form_type": context.form_type,
        "reference_id": context.reference_id,
        "confirmation_no": context.confirmation_no,
        "customer_name": context.customer_name,
        "phone_display": context.phone_display,
        "generated_at": context.generated_at.isoformat(),
    }
    row = await conn.fetchrow(
        """
        INSERT INTO reservation_confirmation_forms (
            hotel_id, form_type, reference_id, language, token_hash, token_prefix,
            html_snapshot, whatsapp_message, payload_json, generated_by, expires_at
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, $10, $11)
        RETURNING id
        """,
        context.hotel_id,
        context.form_type,
        context.reference_id,
        context.language,
        token_hash,
        token_prefix,
        html,
        whatsapp_message,
        orjson.dumps(payload).decode("utf-8"),
        generated_by,
        datetime.now(UTC) + timedelta(days=expiry_days),
    )
    if row is None:
        raise RuntimeError("confirmation_form_insert_failed")
    return ConfirmationDelivery(
        form_id=str(row["id"]),
        public_url=public_url,
        token_prefix=token_prefix,
        html=html,
        whatsapp_message=whatsapp_message,
    )


async def mark_confirmation_sent(
    conn: asyncpg.Connection,
    *,
    form_id: str,
    whatsapp_message_id: str | None,
    delivered: bool,
) -> None:
    """Update delivery state for a generated confirmation form."""
    await conn.execute(
        """
        UPDATE reservation_confirmation_forms
        SET status = $2::varchar,
            sent_at = CASE WHEN $4::bool THEN now() ELSE sent_at END,
            whatsapp_message_id = COALESCE($3::varchar, whatsapp_message_id),
            updated_at = now()
        WHERE id = $1::uuid
        """,
        form_id,
        "SENT" if delivered else "DELIVERY_FAILED",
        whatsapp_message_id,
        delivered,
    )
