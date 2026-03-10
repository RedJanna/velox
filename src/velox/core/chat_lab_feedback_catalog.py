"""Catalog definitions for Chat Lab feedback scoring, categories, and tags."""

from velox.models.chat_lab_feedback import FeedbackOptionItem, FeedbackScaleItem

FEEDBACK_SCALE: tuple[FeedbackScaleItem, ...] = (
    FeedbackScaleItem(
        rating=1,
        label="Kesinlikle Yanlis",
        summary="Yanit tamamen hatali.",
        tooltip="Bilgi tamamen yanlis mi? Burayi sec ve dogruyu sisteme ogret.",
        correction_required=True,
    ),
    FeedbackScaleItem(
        rating=2,
        label="Hatali Anlatim",
        summary="Bilgi ozunde dogru ama anlatim bozuk.",
        tooltip="Bilgi dogru ama anlatim bozuk mu?",
        correction_required=True,
    ),
    FeedbackScaleItem(
        rating=3,
        label="Eksik Bilgi",
        summary="Temel cevap dogru ama kritik detay eksik.",
        tooltip="Cevap yetersiz mi? Eksikleri tamamla.",
        correction_required=True,
    ),
    FeedbackScaleItem(
        rating=4,
        label="Gereksiz Ayrinti",
        summary="Bilgi dogru ama fazla uzun.",
        tooltip="Cok mu laf kalabaligi var? Sadelestirilmis halini onayla.",
        correction_required=True,
    ),
    FeedbackScaleItem(
        rating=5,
        label="Mukemmel",
        summary="Yanit dogru ve onayli ornek olmaya uygun.",
        tooltip="Yanit dogruysa bunu secin; onayli ornek havuzuna eklenir.",
        correction_required=False,
    ),
)

CATEGORY_ITEMS: tuple[FeedbackOptionItem, ...] = (
    FeedbackOptionItem(
        key="yanlis_bilgi",
        label="Yanlis Bilgi",
        description="Net olarak yanlis bilgi verilmesi.",
        tooltip="Ornek: EUR yerine USD yazmak.",
    ),
    FeedbackOptionItem(
        key="eksik_bilgi",
        label="Eksik Bilgi",
        description="Temel cevap dogru ama kritik detaylar eksik.",
        tooltip="Cevap yarim kaliyor veya gerekli bilgi tamamlanmiyor.",
    ),
    FeedbackOptionItem(
        key="alakasiz_yanit",
        label="Alakasiz Yanit",
        description="Sorudan kopuk veya konu disi cevap.",
        tooltip="Kullanici niyetini kaciran cevaplar.",
    ),
    FeedbackOptionItem(
        key="baglam_kopuklugu",
        label="Baglam Kopuklugu",
        description="Sohbetin onceki akisina uyumsuz cevap.",
        tooltip="Hafiza kaybi gibi davranan cevaplar.",
    ),
    FeedbackOptionItem(
        key="uydurma_bilgi",
        label="Asiri Ozyguvenli Uydurma",
        description="Kaynaksiz ve emin bir dille uydurulan bilgi.",
        tooltip="Bilmiyorum demek yerine uydurma bilgi verilmesi.",
    ),
    FeedbackOptionItem(
        key="gevezelik",
        label="Gevezelik / Uzunluk",
        description="Gereksiz uzun veya daginik cevap.",
        tooltip="Kisa istek icin asiri uzun mesaj.",
    ),
    FeedbackOptionItem(
        key="intent_iskalama",
        label="Intent Iskalama",
        description="Kelimeyi anlayip amaci kaciran cevap.",
        tooltip="Asil talebi gormeyen cevap.",
    ),
    FeedbackOptionItem(
        key="format_ihlali",
        label="Format Ihlali",
        description="Istenen sunum bicimine uymayan cevap.",
        tooltip="Liste yerine duz metin gibi.",
    ),
    FeedbackOptionItem(
        key="mantik_celiskisi",
        label="Eksik / Celiskili Mantik",
        description="Kendi icinde tutarsiz veya eksik mantik.",
        tooltip="Bir adimin digerini bozmasi.",
    ),
    FeedbackOptionItem(
        key="ton_politika_ihlali",
        label="Ton / Politika Ihlali",
        description="Uslup, politika veya sinir ihlali.",
        tooltip="Kaba uslup ya da yetkisiz taahhut.",
    ),
    FeedbackOptionItem(
        key="ozel_kategori",
        label="Ozel Kategori",
        description="Hazir listeye sigmayan durum.",
        tooltip="Aciklamayi admin manuel yazar.",
    ),
)

CATEGORY_BY_KEY = {item.key: item for item in CATEGORY_ITEMS}

TAG_ITEMS: tuple[FeedbackOptionItem, ...] = (
    FeedbackOptionItem(
        key="yanlis_bilgi",
        label="Yanlis Bilgi",
        description="Net bilgi hatasi.",
        tooltip="Veri veya politika yanlisi.",
    ),
    FeedbackOptionItem(
        key="eksik_bilgi",
        label="Eksik Bilgi",
        description="Kritik detay eksik.",
        tooltip="Cevap yarim kaliyor.",
    ),
    FeedbackOptionItem(
        key="alakasiz_yanit",
        label="Alakasiz Yanit",
        description="Sorudan kopuk cevap.",
        tooltip="Konu disi veya kacmis niyet.",
    ),
    FeedbackOptionItem(
        key="baglam_kopuklugu",
        label="Baglam Kopuklugu",
        description="Onceki konusma unutuluyor.",
        tooltip="Diyalog hafizasi zayif.",
    ),
    FeedbackOptionItem(
        key="niyet_iskalama",
        label="Niyet Iskalama",
        description="Asil amac anlasilmiyor.",
        tooltip="Intent yanlis tespit ediliyor.",
    ),
    FeedbackOptionItem(
        key="asiri_uzun_yanit",
        label="Asiri Uzun Yanit",
        description="Gereksiz uzun mesaj.",
        tooltip="Laf kalabaligi olusuyor.",
    ),
    FeedbackOptionItem(
        key="asiri_kisa_yanit",
        label="Asiri Kisa Yanit",
        description="Eksik aciklama iceren kisa cevap.",
        tooltip="Gerekli bilgi verilmiyor.",
    ),
    FeedbackOptionItem(
        key="tekrar_loop",
        label="Tekrar / Loop",
        description="Ayni kalip tekrar ediyor.",
        tooltip="Cevap kisa donguye giriyor.",
    ),
    FeedbackOptionItem(
        key="format_ihlali",
        label="Format Ihlali",
        description="Istenen format bozuluyor.",
        tooltip="Liste, tablo ya da siralama eksik.",
    ),
    FeedbackOptionItem(
        key="ton_uyumsuzlugu",
        label="Ton Uyumsuzlugu",
        description="Duruma uygun olmayan uslup.",
        tooltip="Fazla sert ya da fazla neseli.",
    ),
    FeedbackOptionItem(
        key="kaba_uslup",
        label="Kaba Uslup",
        description="Premium sicak tonun bozulmasi.",
        tooltip="Kisa ve itici ifade.",
    ),
    FeedbackOptionItem(
        key="politika_ihlali",
        label="Politika Ihlali",
        description="Kurallarin disina cikilmasi.",
        tooltip="Yetkisiz soz veya riskli icerik.",
    ),
    FeedbackOptionItem(
        key="uydurma_bilgi",
        label="Uydurma Bilgi",
        description="Kaynaksiz bilgi uydurulmasi.",
        tooltip="Hotel profile veya tool disi iddia.",
    ),
    FeedbackOptionItem(
        key="guncel_olmayan_bilgi",
        label="Guncel Olmayan Bilgi",
        description="Eski bilgi kullanilmasi.",
        tooltip="Degisen surec hala gecerli saniliyor.",
    ),
    FeedbackOptionItem(
        key="hotel_profile_celiskisi",
        label="Hotel Profile Celiskisi",
        description="Hotel profile ile uyumsuz cevap.",
        tooltip="Kaynak veri ile cevap catismasi.",
    ),
    FeedbackOptionItem(
        key="tool_output_celiskisi",
        label="Tool Output Celiskisi",
        description="Tool sonucu ile uyumsuz cevap.",
        tooltip="Gercek sonuc yanlis aktariliyor.",
    ),
    FeedbackOptionItem(
        key="mantik_celiskisi",
        label="Mantik Celiskisi",
        description="Cevap kendi icinde tutarsiz.",
        tooltip="Bir kisim digerini bozuyor.",
    ),
    FeedbackOptionItem(
        key="eksik_dogrulama_sorusu",
        label="Eksik Dogrulama Sorusu",
        description="Gerekli netlestirme sorusu yok.",
        tooltip="Slots eksikken direkt cevap veriliyor.",
    ),
    FeedbackOptionItem(
        key="gereksiz_pii_talebi",
        label="Gereksiz PII Talebi",
        description="Gereksiz kisisel veri isteme.",
        tooltip="Fazla bilgi isteniyor.",
    ),
    FeedbackOptionItem(
        key="gereksiz_escalation",
        label="Gereksiz Escalation",
        description="Gereksiz insan devri.",
        tooltip="Sorun kendi icinde cozulebilecekken aktarim.",
    ),
)
