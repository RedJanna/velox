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
            "subtitle": "Transfer reservation confirmation details",
        },
    },
}

PROMPT_FIELD_LABELS: dict[str, dict[str, str]] = {
    "en": {
        "authorized_confirmation": "Authorized Confirmation",
        "guest_name": "Guest Name",
        "phone_number": "Phone Number",
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
        "reservation_date": "Rezervasyon Tarihi / Reservation Date",
        "reservation_time": "Rezervasyon Saati / Reservation Time",
        "restaurant_guest_count": "Kişi Sayısı / Number of Guests",
        "restaurant_seating": "Masa Tipi / Seating Preference",
        "restaurant_area": "İç / Dış Alan Tercihi",
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


def mask_phone(phone: object) -> str:
    """Mask phone number for public confirmation display."""
    value = re.sub(r"\s+", "", str(phone or "").strip())
    if not value:
        return "-"
    if len(value) <= 6:
        return "***"
    return f"{value[:3]} *** *** {value[-4:]}"


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
    filtered = tuple(item for item in items if item.value and item.value != "-")
    return ConfirmationSection(title=title, items=filtered)


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
                    ConfirmationDetail(_prompt_label(normalized_language, "phone_number", labels["phone"]), mask_phone(draft.get("phone"))),
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
            phone_display=mask_phone(draft.get("phone")),
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
                    ConfirmationDetail(_prompt_label(normalized_language, "phone_number", labels["phone"]), mask_phone(row.get("phone"))),
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
            phone_display=mask_phone(row.get("phone")),
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
                ConfirmationDetail(_prompt_label(normalized_language, "phone_number", labels["phone"]), mask_phone(row.get("phone"))),
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
        phone_display=mask_phone(row.get("phone")),
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
    customer_name = _clean(customer.get("guest_name") or payload.get("guest_name"))
    phone = customer.get("phone") or payload.get("phone")
    confirmation_no = _clean(payload.get("confirmation_no") or details.get("confirmation_no"), "MANUAL-PREVIEW")
    reference_id = _clean(payload.get("reference_id") or confirmation_no)
    if customer_name == "-":
        raise ValueError("guest_name_required")

    customer_section = _section(
        labels["customer_information"],
        [
            ConfirmationDetail(_prompt_label(normalized_language, "guest_name", labels["guest"]), customer_name, True),
            ConfirmationDetail(_prompt_label(normalized_language, "phone_number", labels["phone"]), mask_phone(phone)),
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

    if not section.items:
        raise ValueError("reservation_details_required")
    return ConfirmationContext(
        form_type=form_type,
        hotel_id=hotel_id,
        hotel_name=hotel_name,
        language=normalized_language,
        customer_name=customer_name,
        phone_display=mask_phone(phone),
        reference_id=reference_id,
        confirmation_no=confirmation_no,
        sections=(customer_section, section),
        important_note=note,
        generated_at=now,
    )


def render_confirmation_html(context: ConfirmationContext) -> str:
    """Render premium fume/white HTML confirmation form."""
    labels = copy_for(context.language)
    dir_attr = "rtl" if context.language == "ar" else "ltr"
    type_label = labels[context.form_type]
    document = _document_profile(context.form_type, context.language, labels)
    confirmation_section = _section(
        labels["confirmation_information"],
        [
            ConfirmationDetail(labels["status"], labels["confirmed_status"], True),
            ConfirmationDetail(
                _prompt_label(context.language, "authorized_confirmation", labels["confirmation_information"]),
                context.hotel_name,
                True,
            ),
        ],
    )
    sections = [section for section in context.sections if section.items]
    sections.append(confirmation_section)
    section_html = "\n".join(_render_section(section) for section in sections if section.items)
    intro = f"{labels['intro']}"
    generated = _format_generated_at(context.generated_at)
    brand_parts = context.hotel_name.split()
    brand_primary = brand_parts[0] if brand_parts else context.hotel_name
    brand_place = " ".join(brand_parts[1:]) if len(brand_parts) > 1 else context.hotel_name
    motif_class = f"motif-{context.form_type}"
    return f"""<!doctype html>
<html lang="{escape(context.language)}" dir="{dir_attr}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="robots" content="noindex,nofollow">
  <title>{escape(context.hotel_name)} · {escape(document["title"])}</title>
  <style>
    :root {{
      --paper:#ffffff; --page:#f0f0ec; --ink:#111111; --near:#1b1b18;
      --fume:#343431; --fume-soft:#ededeb; --muted:#686864; --line:#d8d8d2;
      --hair:#20201d; --wash:#fafaf8;
    }}
    * {{ box-sizing:border-box; }}
    body {{
      margin:0; background:var(--page); color:var(--ink);
      font-family:Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height:1.5;
    }}
    .page {{ max-width:900px; margin:0 auto; padding:42px 20px; }}
    .sheet {{
      position:relative; overflow:hidden; background:var(--paper); color:var(--ink);
      width:min(100%, 794px); min-height:1123px; margin:0 auto;
      border:1px solid var(--hair); box-shadow:0 24px 70px rgba(15,15,12,.10);
    }}
    .sheet::before {{
      content:""; position:absolute; inset:18px; border:1px solid rgba(32,32,29,.18);
      pointer-events:none; z-index:0;
    }}
    .linework {{ position:absolute; inset:0; pointer-events:none; z-index:0; opacity:.95; }}
    .linework span {{ position:absolute; height:1px; background:repeating-linear-gradient(90deg, rgba(22,22,20,.78) 0 72px, transparent 72px 104px); }}
    .linework .lw-a {{ top:132px; left:42px; width:48%; }}
    .linework .lw-b {{ top:172px; right:56px; width:26%; background:linear-gradient(90deg, transparent, rgba(52,52,49,.72), transparent); }}
    .linework .lw-c {{ top:348px; left:0; width:34%; opacity:.38; }}
    .linework .lw-d {{ bottom:166px; right:42px; width:42%; opacity:.52; }}
    .linework .lw-e {{ top:94px; right:88px; width:1px; height:118px; background:linear-gradient(180deg, rgba(17,17,17,.68), transparent); }}
    .motif-restaurant .lw-a {{ width:36%; }}
    .motif-restaurant .lw-b {{ top:214px; right:46px; width:34%; }}
    .motif-restaurant .lw-d {{ bottom:142px; width:32%; }}
    .motif-transfer .lw-c {{ top:386px; left:36px; width:46%; transform:rotate(-4deg); transform-origin:left center; opacity:.48; }}
    .motif-transfer .lw-d {{ bottom:188px; width:52%; transform:rotate(3deg); transform-origin:right center; }}
    .letterhead,.hero,.status-strip,.content,.footer {{ position:relative; z-index:1; }}
    .letterhead {{
      min-height:176px; padding:42px 46px 30px; border-bottom:1px solid var(--hair);
      display:flex; justify-content:space-between; gap:28px; align-items:flex-start;
    }}
    .brand-lockup {{ min-width:230px; }}
    .brand-name {{
      font-family:Georgia, "Times New Roman", serif; font-size:42px; line-height:.86;
      letter-spacing:.05em; text-transform:uppercase; color:var(--near);
    }}
    .brand-place {{
      display:inline-block; margin-top:14px; padding-top:10px; border-top:1px solid var(--near);
      font-size:12px; letter-spacing:.48em; text-transform:uppercase; color:var(--fume);
    }}
    .doc-meta {{ text-align:end; color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:.08em; }}
    .doc-meta strong {{ display:block; color:var(--near); font-size:15px; letter-spacing:0; margin-top:8px; text-transform:none; }}
    .hero {{ padding:44px 46px 30px; border-bottom:1px solid var(--line); }}
    .eyebrow {{ color:var(--muted); font-size:11px; letter-spacing:.18em; text-transform:uppercase; font-weight:800; }}
    h1 {{
      margin:16px 0 12px; max-width:660px; font-family:Georgia, "Times New Roman", serif;
      font-size:42px; line-height:1.05; font-weight:500; letter-spacing:0; color:var(--near);
    }}
    .subtitle {{ margin:0; color:var(--near); font-size:13px; letter-spacing:.11em; text-transform:uppercase; font-weight:800; }}
    .intro {{ max-width:670px; color:var(--fume); font-size:15px; margin:18px 0 0; }}
    .status-strip {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); border-bottom:1px solid var(--hair); background:var(--wash); }}
    .status-cell {{ min-height:84px; padding:18px 46px; border-inline-end:1px solid var(--line); }}
    .status-cell:last-child {{ border-inline-end:none; }}
    .status-cell span {{ display:block; color:var(--muted); font-size:10px; text-transform:uppercase; letter-spacing:.14em; font-weight:800; }}
    .status-cell strong {{ display:block; margin-top:8px; color:var(--near); font-size:15px; overflow-wrap:anywhere; }}
    .content {{ padding:34px 46px 44px; }}
    .section {{ padding:28px 0; border-bottom:1px solid var(--line); }}
    .section:first-child {{ padding-top:0; }}
    .section-title-row {{ display:flex; align-items:center; gap:18px; margin:0 0 18px; }}
    .section-title-row h2 {{ margin:0; flex:0 0 auto; font-size:12px; letter-spacing:.18em; text-transform:uppercase; color:var(--fume); }}
    .section-title-row i {{ flex:1 1 auto; height:1px; background:linear-gradient(90deg, rgba(32,32,29,.72) 0 62px, transparent 62px 88px, rgba(32,32,29,.28) 88px 100%); }}
    .details {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); border-top:1px solid var(--hair); border-inline-start:1px solid var(--line); }}
    .detail {{ min-height:88px; padding:18px 18px 16px; border-inline-end:1px solid var(--line); border-bottom:1px solid var(--line); background:rgba(255,255,255,.94); }}
    .detail span {{ display:block; color:var(--muted); font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:.08em; }}
    .detail strong {{ display:block; margin-top:10px; color:var(--ink); font-size:16px; overflow-wrap:anywhere; }}
    .detail.is-emphasis {{ background:var(--fume-soft); }}
    .note {{ margin-top:30px; padding:24px 26px; border:1px solid var(--hair); background:#fbfbf9; box-shadow:inset 0 1px 0 rgba(255,255,255,.8); }}
    .note h2 {{ margin:0 0 10px; font-family:Georgia, "Times New Roman", serif; font-size:24px; font-weight:500; }}
    .note p {{ margin:0; color:var(--fume); }}
    .footer {{
      padding:20px 46px 34px; border-top:1px solid var(--hair);
      display:flex; justify-content:space-between; gap:18px; color:var(--muted); font-size:12px;
    }}
    @page {{ size:A4; margin:0; }}
    @media(max-width:760px) {{
      .page {{ padding:16px; }}
      .sheet {{ min-height:0; }}
      .letterhead,.hero,.content,.footer {{ padding-left:22px; padding-right:22px; }}
      .letterhead,.footer {{ flex-direction:column; }}
      .doc-meta {{ text-align:start; }}
      .brand-name {{ font-size:34px; }}
      .brand-place {{ letter-spacing:.32em; }}
      h1 {{ font-size:31px; }}
      .status-strip,.details {{ grid-template-columns:1fr; }}
      .status-cell {{ border-inline-end:none; border-bottom:1px solid var(--line); }}
      .status-cell:last-child {{ border-bottom:none; }}
    }}
    @media print {{
      body {{ background:#fff; }}
      .page {{ padding:0; max-width:none; }}
      .sheet {{ box-shadow:none; border:none; width:794px; min-height:1123px; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <article class="sheet {motif_class}" aria-label="{escape(labels["document_title"])}">
      <div class="linework" aria-hidden="true">
        <span class="lw-a"></span><span class="lw-b"></span><span class="lw-c"></span><span class="lw-d"></span><span class="lw-e"></span>
      </div>
      <header class="letterhead">
        <div class="brand-lockup">
          <div class="brand-name">{escape(brand_primary)}</div>
          <div class="brand-place">{escape(brand_place)}</div>
        </div>
        <div class="doc-meta">
          <span>{escape(labels["confirmation_no"])}</span>
          <strong>{escape(context.confirmation_no)}</strong>
        </div>
      </header>
      <section class="hero">
        <div class="eyebrow">{escape(type_label)} · {escape(labels["confirmed_status"])}</div>
        <h1>{escape(document["title"])}</h1>
        <p class="subtitle">{escape(document["subtitle"])}</p>
        <p class="intro">{escape(intro)}</p>
      </section>
      <section class="status-strip" aria-label="{escape(labels["confirmation_information"])}">
        <div class="status-cell"><span>{escape(labels["status"])}</span><strong>{escape(labels["confirmed_status"])}</strong></div>
        <div class="status-cell"><span>{escape(labels["guest"])}</span><strong>{escape(context.customer_name)}</strong></div>
        <div class="status-cell"><span>{escape(labels["generated_on"])}</span><strong>{escape(generated)}</strong></div>
      </section>
      <section class="content">
        {section_html}
        <section class="note">
          <h2>{escape(labels["important_information"])}</h2>
          <p>{escape(context.important_note)}</p>
        </section>
      </section>
      <footer class="footer">
        <span>{escape(context.hotel_name)}</span>
        <span>{escape(labels["secure_notice"])}</span>
      </footer>
    </article>
  </main>
</body>
</html>"""


def _render_section(section: ConfirmationSection) -> str:
    rows = "\n".join(
        (
            f'<div class="detail{" is-emphasis" if item.emphasis else ""}">'
            f"<span>{escape(item.label)}</span><strong>{escape(item.value)}</strong></div>"
        )
        for item in section.items
    )
    return f"""<section class="section">
          <div class="section-title-row"><h2>{escape(section.title)}</h2><i aria-hidden="true"></i></div>
          <div class="details">{rows}</div>
        </section>"""


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
