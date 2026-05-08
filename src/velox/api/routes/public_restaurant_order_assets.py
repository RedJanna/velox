"""Static assets for the public restaurant ordering panel."""

# ruff: noqa: E501

PUBLIC_RESTAURANT_ORDER_STYLE = """\
:root{
  --color-primary:#192f9a;
  --color-primary-700:#0f1f70;
  --color-primary-500:#243fb4;
  --color-primary-50:#edf1ff;
  --color-surface:#f6efe5;
  --color-surface-soft:#fffaf0;
  --color-surface-elevated:#ffffff;
  --color-border:rgba(25,47,154,.18);
  --color-ink:#111827;
  --color-muted:#6f5e4e;
  --color-muted-2:#8b7a67;
  --color-olive:#193d36;
  --color-olive-soft:#e6eee8;
  --color-terracotta:#c87045;
  --color-terracotta-accessible:#9a4b2e;
  --color-terracotta-soft:#f7dcc8;
  --color-gold:#d7a844;
  --color-gold-accessible:#7a5805;
  --color-gold-soft:#fbefd0;
  --radius-sm:10px;
  --radius-md:16px;
  --radius-lg:22px;
  --radius-xl:28px;
  --shadow-card:0 12px 34px rgba(17,24,39,.08);
  --shadow-floating:0 18px 45px rgba(17,24,39,.16);
  --space-1:4px;
  --space-2:8px;
  --space-3:12px;
  --space-4:16px;
  --space-5:20px;
  --space-6:24px;
  --space-8:32px;
  --font-display:"Cinzel","Trajan Pro",Georgia,serif;
  --font-ui:Inter,Manrope,Aptos,"Segoe UI",system-ui,-apple-system,BlinkMacSystemFont,sans-serif;
  font-family:var(--font-ui);
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;min-height:100vh;background:#f7f2e8;color:var(--color-ink);font-size:16px}
button,input,textarea,select{font:inherit}
button{cursor:pointer}
button:disabled{cursor:not-allowed;opacity:.52}
a{color:inherit}
.order-shell{width:min(1180px,100%);margin:0 auto;padding:var(--space-5) var(--space-4) calc(116px + env(safe-area-inset-bottom))}
.order-top{position:relative;display:flex;justify-content:space-between;gap:var(--space-4);align-items:center;margin-bottom:var(--space-5);border:1px solid var(--color-border);border-radius:var(--radius-xl);background:linear-gradient(135deg,rgba(255,250,240,.96),rgba(255,255,255,.86));box-shadow:var(--shadow-card);padding:var(--space-4)}
.order-top:after{content:"";position:absolute;inset:auto var(--space-6) -1px var(--space-6);height:3px;border-radius:999px;background:linear-gradient(90deg,var(--color-primary),var(--color-terracotta),var(--color-gold))}
.brand{display:flex;align-items:center;gap:var(--space-3);min-width:0}
.brand-logo{display:inline-flex;align-items:center;justify-content:center;width:58px;height:58px;border:1px solid rgba(25,47,154,.26);border-radius:18px;background:var(--color-primary-50);color:var(--color-primary);font-family:var(--font-display);font-size:26px;font-weight:900;overflow:hidden;flex:0 0 auto}
.brand-logo img{width:100%;height:100%;object-fit:contain;padding:7px}
.brand h1{margin:0;font-family:var(--font-display);font-size:clamp(24px,4vw,38px);line-height:1;color:var(--color-primary);letter-spacing:0}
.brand p{margin:7px 0 0;color:var(--color-muted);font-size:14px;font-weight:650}
.brand-copy{min-width:0}
.header-actions{display:flex;flex-direction:column;align-items:flex-end;gap:var(--space-2);min-width:min(360px,42vw)}
.language-strip{display:flex;justify-content:flex-end;gap:6px;flex-wrap:wrap}
.language-chip{min-height:34px;border:1px solid var(--color-border);border-radius:999px;background:#fff;color:var(--color-primary-700);padding:6px 10px;font-size:12px;font-weight:900}
.language-chip.active{background:var(--color-primary);border-color:var(--color-primary);color:#fff}
.pill{display:inline-flex;align-items:center;gap:7px;border:1px solid var(--color-border);border-radius:999px;background:rgba(255,255,255,.76);padding:9px 13px;font-weight:850;color:var(--color-primary-700);white-space:nowrap}
.pill:before{content:"";width:8px;height:8px;border-radius:999px;background:var(--color-terracotta)}
.panel{border:1px solid var(--color-border);border-radius:var(--radius-xl);background:rgba(255,250,240,.94);box-shadow:var(--shadow-card);padding:var(--space-6)}
.panel h2{margin:0 0 var(--space-4);font-size:clamp(23px,4vw,34px);line-height:1.12;color:var(--color-primary);letter-spacing:0}
.panel h3{margin:var(--space-5) 0 var(--space-3);font-size:18px}
.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:var(--space-3)}
.grid-2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:var(--space-3)}
.card{border:1px solid var(--color-border);border-radius:var(--radius-lg);background:var(--color-surface-elevated);padding:var(--space-4);text-align:left;box-shadow:0 8px 18px rgba(17,24,39,.05);transition:transform .16s ease,border-color .16s ease,box-shadow .16s ease}
.card:hover{transform:translateY(-1px);box-shadow:var(--shadow-card)}
.card strong{display:block;font-size:17px;line-height:1.25}
.card small{display:block;margin-top:7px;color:var(--color-muted);line-height:1.45}
.card.active{border-color:var(--color-primary);box-shadow:0 0 0 4px rgba(25,47,154,.11),var(--shadow-card)}
.primary,.secondary,.danger{min-height:46px;border-radius:999px;border:1px solid transparent;padding:11px 17px;font-weight:900;line-height:1.1;transition:transform .16s ease,box-shadow .16s ease,background .16s ease}
.primary{background:linear-gradient(135deg,var(--color-primary),var(--color-primary-500));color:#fff;box-shadow:0 10px 20px rgba(25,47,154,.22)}
.primary:hover{transform:translateY(-1px)}
.secondary{background:#fff;color:var(--color-primary-700);border-color:var(--color-border)}
.danger{background:#fff1ef;color:#991b1b;border-color:#fac5bd}
.toolbar{display:flex;gap:var(--space-2);flex-wrap:wrap;margin:var(--space-4) 0}
.toolbar a{text-decoration:none}
.menu-heading-row{display:flex;align-items:flex-start;justify-content:space-between;gap:var(--space-3);margin-bottom:var(--space-3)}
.meal-tabs{display:flex;gap:var(--space-2);overflow-x:auto;padding-bottom:var(--space-2);scrollbar-width:thin}
.meal-tab{flex:0 0 auto;min-height:42px;border:1px solid var(--color-border);border-radius:999px;background:#fff;color:var(--color-primary-700);padding:9px 14px;font-weight:900}
.meal-tab.active{background:var(--color-primary);border-color:var(--color-primary);color:#fff}
.pdf-strip{display:flex;align-items:center;gap:var(--space-2);flex-wrap:wrap;border:1px solid rgba(25,47,154,.12);border-radius:var(--radius-md);background:rgba(255,255,255,.66);padding:var(--space-3);margin:0 0 var(--space-4)}
.pdf-strip span{color:var(--color-muted);font-size:14px;font-weight:750}
.pdf-link{min-height:36px;padding:8px 12px;font-size:13px}
.order-menu-layout{display:grid;grid-template-columns:minmax(0,1fr) 330px;gap:var(--space-5);align-items:start}
.order-menu-main{min-width:0}
.order-search{position:sticky;top:0;z-index:4;margin:calc(var(--space-2) * -1) 0 var(--space-4);padding:var(--space-2) 0;background:linear-gradient(180deg,var(--color-surface-soft),rgba(255,250,240,.86))}
.order-search input{width:100%;min-height:50px;border:1px solid var(--color-border);border-radius:999px;background:#fff;padding:0 var(--space-5);font-weight:750;color:var(--color-ink);box-shadow:0 8px 24px rgba(17,24,39,.06)}
.order-category-rail{position:sticky;top:64px;z-index:3;display:flex;gap:var(--space-2);overflow-x:auto;padding:0 0 var(--space-3);margin-bottom:var(--space-4);scrollbar-width:thin}
.category-chip{flex:0 0 auto;min-height:42px;border:1px solid var(--color-border);border-radius:999px;background:#fff;color:var(--color-primary-700);padding:9px 14px;font-weight:850}
.category-chip.active{background:var(--color-primary);color:#fff;border-color:var(--color-primary)}
.category-section{display:grid;gap:var(--space-3);margin-bottom:var(--space-6)}
.category-heading{display:flex;align-items:end;justify-content:space-between;gap:var(--space-3);border-bottom:1px solid var(--color-border);padding-bottom:var(--space-2)}
.category-heading h3{margin:0;font-family:var(--font-display);font-size:22px;color:var(--color-primary)}
.category-heading span{color:var(--color-muted);font-weight:800;font-size:13px}
.items{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:var(--space-3)}
.product-card{display:grid;gap:var(--space-3);min-height:0;padding:var(--space-4)}
.item-title{display:flex;justify-content:space-between;gap:var(--space-3);align-items:flex-start}
.item-title b{font-size:17px;line-height:1.25;overflow-wrap:anywhere}
.price{font-weight:950;color:var(--color-primary);white-space:nowrap}
.product-content{margin:0;color:var(--color-muted);font-size:15px;line-height:1.45}
.product-content strong{color:var(--color-primary-700)}
.product-details{border-top:1px solid rgba(25,47,154,.12);padding-top:var(--space-2)}
.product-details summary{cursor:pointer;color:var(--color-primary-700);font-size:14px;font-weight:900}
.product-details p{margin:var(--space-2) 0 0;color:var(--color-muted);font-size:14px;line-height:1.45}
.product-meta{display:flex;gap:var(--space-2);flex-wrap:wrap;margin-top:auto}
.tag{display:inline-flex;align-items:center;min-height:24px;border-radius:999px;background:var(--color-olive-soft);color:var(--color-olive);padding:4px 9px;font-size:12px;font-weight:850}
.muted{color:var(--color-muted)}
.field{display:grid;gap:7px;margin:var(--space-3) 0}
.field label{font-weight:850;color:var(--color-primary-700)}
.field input,.field textarea{width:100%;border:1px solid var(--color-border);border-radius:var(--radius-md);background:#fff;padding:13px 14px;color:var(--color-ink)}
.field textarea{min-height:92px;resize:vertical}
.summary{display:grid;gap:var(--space-2)}
.summary-row{display:flex;justify-content:space-between;gap:var(--space-3);border-bottom:1px solid rgba(25,47,154,.12);padding:0 0 var(--space-2);align-items:center}
.summary-row:last-child{border-bottom:0}
.qty-actions{display:inline-flex;align-items:center;gap:6px}
.product-actions{display:flex;justify-content:flex-end;align-items:center;margin-top:var(--space-2)}
.qty-actions button{width:42px;height:42px;min-height:42px;border-radius:999px;padding:0}
.footer-actions{display:flex;justify-content:flex-end;gap:var(--space-2);margin-top:var(--space-5);flex-wrap:wrap}
.empty{border:1px dashed var(--color-border);border-radius:var(--radius-lg);padding:var(--space-5);color:var(--color-muted);background:rgba(255,255,255,.62);line-height:1.5}
.notice{border-left:4px solid var(--color-primary);background:var(--color-primary-50);border-radius:var(--radius-md);padding:var(--space-3);margin:var(--space-3) 0;color:var(--color-primary-700);line-height:1.45}
.error{border-left-color:#b42318;background:#fff1ef;color:#7a271a}
.stepper{display:flex;gap:6px;margin:0 0 var(--space-5)}
.dot{height:8px;flex:1;border-radius:999px;background:#e2d5c4}
.dot.active{background:linear-gradient(90deg,var(--color-primary),var(--color-terracotta))}
.hero{display:grid;gap:var(--space-4)}
.hero h2{margin:0;font-size:clamp(27px,6vw,42px)}
.hero p{margin:0;color:var(--color-muted);line-height:1.55}
.hero-list{display:grid;gap:var(--space-2);margin:var(--space-2) 0 0;padding:0;list-style:none}
.hero-list li{display:flex;gap:var(--space-3);align-items:flex-start;border:1px solid var(--color-border);border-radius:var(--radius-lg);background:#fff;padding:var(--space-3) var(--space-4)}
.hero-index{display:inline-flex;align-items:center;justify-content:center;min-width:30px;height:30px;border-radius:999px;background:var(--color-gold-soft);color:var(--color-gold-accessible);font-weight:950}
.hero-form{margin-top:var(--space-3)}
.hero-actions{display:flex;justify-content:flex-end;gap:var(--space-2);flex-wrap:wrap;margin-top:var(--space-3)}
.cart-panel{position:sticky;top:24px;border:1px solid var(--color-border);border-radius:var(--radius-xl);background:#fff;box-shadow:var(--shadow-card);padding:var(--space-4)}
.cart-panel h3{margin:0 0 var(--space-3);font-size:18px;color:var(--color-primary)}
.sticky-cart{position:fixed;left:50%;bottom:calc(14px + env(safe-area-inset-bottom));transform:translateX(-50%);z-index:20;width:min(720px,calc(100% - 28px));display:flex;align-items:center;justify-content:space-between;gap:var(--space-3);border:1px solid rgba(25,47,154,.22);border-radius:999px;background:rgba(255,255,255,.96);box-shadow:var(--shadow-floating);padding:10px 10px 10px 18px}
.sticky-cart strong{color:var(--color-primary)}
.sticky-cart span{color:var(--color-muted);font-size:13px;font-weight:750}
.success-card{text-align:center;padding-block:var(--space-8)}
.success-card .pill{margin:var(--space-3) auto 0}
:focus-visible{outline:3px solid rgba(25,47,154,.34);outline-offset:3px}
[hidden]{display:none!important}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}.card,.primary,.secondary,.danger{transition:none}.card:hover,.primary:hover{transform:none}}
@media(max-width:980px){.order-menu-layout{grid-template-columns:1fr}.cart-panel{display:none}.order-category-rail{top:58px}.items{grid-template-columns:1fr 1fr}.order-shell{padding-inline:var(--space-3)}}
@media(max-width:720px){.order-shell{padding-top:var(--space-3)}.order-top{align-items:flex-start;border-radius:var(--radius-lg);padding:var(--space-3)}.brand-logo{width:50px;height:50px;border-radius:16px}.header-actions{width:100%;min-width:0;align-items:stretch;margin-top:var(--space-3)}.language-strip{justify-content:flex-start}.pill{width:100%;justify-content:center}.order-top{display:block}.brand h1{font-size:26px}.menu-heading-row{display:grid}.grid,.grid-2,.items{grid-template-columns:1fr}.panel{padding:var(--space-4);border-radius:var(--radius-lg)}.footer-actions,.hero-actions{justify-content:stretch}.footer-actions button,.hero-actions button{width:100%}.sticky-cart{border-radius:var(--radius-lg);align-items:stretch;flex-direction:column;padding:var(--space-3)}.sticky-cart .primary{width:100%}.order-search{top:0}.order-category-rail{top:58px}.category-heading{align-items:flex-start;flex-direction:column}}
@media(max-width:420px){.brand{align-items:flex-start}.brand-logo{width:46px;height:46px}.brand h1{font-size:23px}.panel h2{font-size:24px}.category-chip{max-width:78vw;overflow:hidden;text-overflow:ellipsis}.item-title{display:grid}.price{justify-self:start}}
"""


PUBLIC_RESTAURANT_ORDER_SCRIPT = """\
const app = document.getElementById('orderApp');
const token = new URLSearchParams(window.location.search).get('t') || '';
const DEFAULT_ENTRY_ORDER_URL = 'https://velox.nexlumeai.com/order?t=eyJob3RlbF9pZCI6MjE5NjYsInRhYmxlX25vIjoiMCIsInRva2VuX3ZlcnNpb24iOjEsInZlbnVlIjoiS2Fzc2FuZHJhIFJlc3RhdXJhbnQifQ.O3zPVyByH0n8XPivWQjsmzlk9eAwCgm6hIRCkwTPTLE';
const state = {step:'loading',cfg:null,lang:'tr',meal:'',cart:{},serviceType:'table_service',roomNumber:'',customerNote:'',allergyNote:'',search:'',activeCategory:'',submitting:false,success:null,error:''};
let searchRenderTimer = 0;
const i18n = {
  tr:{title:'Kassandra Restaurant Sipariş',lead:'QR ile masa siparişi',language:'Dil seçin',meal:'Hangi öğün için sipariş vermek istiyorsunuz?',breakfast:'Kahvaltı',lunch:'Öğle',dinner:'Akşam',continue:'Devam',back:'Geri',menu:'Menü',pdf:'PDF menüyü aç',pdfSecondary:'PDF menüleri ayrıca görüntüleyebilirsiniz.',add:'Ekle',cart:'Sepet',empty:'Sepetiniz boş.',noResults:'Aramanıza uygun ürün bulunamadı.',service:'Servis tipi',table:'Masa servisi',room:'Oda servisi',roomNo:'Oda numarası',note:'Sipariş notu',allergy:'Alerji / özel tercih',confirm1:'1. teyit: Sepetiniz doğru mu?',confirm2:'2. teyit: Siparişi restorana göndermek istiyor musunuz?',send:'Siparişi Gönder',pending:'Siparişiniz restorana iletildi, personel onayı bekleniyor.',staff:'Personel siparişi admin panelden kabul edecektir.',pricePending:'Güncel fiyat personel tarafından teyit edilir',total:'Toplam',tryAgain:'Tekrar deneyin',startTitle:'Siparişe devam edin',startBody:'Siparişe devam et butonuyla restoran menüsüne geçebilirsiniz.',openLink:'Siparişe devam et',allCategories:'Tümü',breakfastOptionCount:'2 seçenek',searchPlaceholder:'Ürün veya kategori ara',categoryNavLabel:'Menü kategorileri',ingredientsLabel:'İçindekiler',details:'Detaylar',contentFallback:'İçerik bilgisi personel tarafından teyit edilir.',itemCount:'{count} ürün',tableNumberLabel:'Masa',decreaseQuantity:'Adedi azalt',increaseQuantity:'Adedi artır',loadingTitle:'Yükleniyor...',loadingBody:'Sipariş ekranı hazırlanıyor.',submitError:'İşlem tamamlanamadı.',configError:'Sipariş ekranı açılamadı.'},
  en:{title:'Kassandra Restaurant Order',lead:'Table ordering by QR',language:'Choose language',meal:'Which meal period would you like?',breakfast:'Breakfast',lunch:'Lunch',dinner:'Dinner',continue:'Continue',back:'Back',menu:'Menu',pdf:'Open PDF menu',pdfSecondary:'You can also view the PDF menus.',add:'Add',cart:'Cart',empty:'Your cart is empty.',noResults:'No matching items found.',service:'Service type',table:'Table service',room:'Room service',roomNo:'Room number',note:'Order note',allergy:'Allergy / dietary note',confirm1:'1st confirmation: Is your cart correct?',confirm2:'2nd confirmation: Send this order to the restaurant?',send:'Send Order',pending:'Your order has been sent to the restaurant and is waiting for staff approval.',staff:'Staff will accept it from the admin panel.',pricePending:'Ask staff for current price',total:'Total',tryAgain:'Try again',startTitle:'Scan the table QR code to begin',startBody:'This page starts the ordering flow when it is opened with a signed table link.',openLink:'Continue order',allCategories:'All',breakfastOptionCount:'2 options',searchPlaceholder:'Search products or categories',categoryNavLabel:'Menu categories',ingredientsLabel:'Ingredients',details:'Details',contentFallback:'Content details are confirmed by staff.',itemCount:'{count} items',tableNumberLabel:'Table',decreaseQuantity:'Decrease quantity',increaseQuantity:'Increase quantity',loadingTitle:'Loading...',loadingBody:'Preparing your order screen.',submitError:'The request could not be completed.',configError:'The order screen could not be opened.'},
  de:{title:'Kassandra Restaurant Bestellung',lead:'Tischbestellung per QR',language:'Sprache wählen',meal:'Für welche Mahlzeit möchten Sie bestellen?',breakfast:'Frühstück',lunch:'Mittagessen',dinner:'Abendessen',continue:'Weiter',back:'Zurück',menu:'Menü',pdf:'PDF-Menü öffnen',add:'Hinzufügen',cart:'Warenkorb',empty:'Ihr Warenkorb ist leer.',service:'Serviceart',table:'Tischservice',room:'Zimmerservice',roomNo:'Zimmernummer',note:'Bestellnotiz',allergy:'Allergie / besondere Präferenz',confirm1:'1. Bestätigung: Ist Ihr Warenkorb korrekt?',confirm2:'2. Bestätigung: Bestellung an das Restaurant senden?',send:'Bestellung senden',pending:'Ihre Bestellung wurde an das Restaurant übermittelt und wartet auf Bestätigung durch das Personal.',staff:'Das Personal nimmt die Bestellung im Admin-Panel an.',pricePending:'Preis nach Personalbestätigung',total:'Gesamt',tryAgain:'Erneut versuchen',startTitle:'Scannen Sie den Tisch-QR-Code, um zu beginnen',startBody:'Diese Seite startet den Bestellablauf, wenn sie mit einem signierten Tischlink geöffnet wird.',openLink:'Bestellung fortsetzen'},
  ru:{title:'Заказ в ресторане Kassandra',lead:'Заказ к столу по QR-коду',language:'Выберите язык',meal:'Для какого приема пищи вы хотите сделать заказ?',breakfast:'Завтрак',lunch:'Обед',dinner:'Ужин',continue:'Продолжить',back:'Назад',menu:'Меню',pdf:'Открыть PDF-меню',add:'Добавить',cart:'Корзина',empty:'Ваша корзина пуста.',service:'Тип обслуживания',table:'Обслуживание за столом',room:'Доставка в номер',roomNo:'Номер комнаты',note:'Комментарий к заказу',allergy:'Аллергия / особые предпочтения',confirm1:'1-е подтверждение: корзина верна?',confirm2:'2-е подтверждение: отправить заказ в ресторан?',send:'Отправить заказ',pending:'Ваш заказ отправлен в ресторан и ожидает подтверждения персоналом.',staff:'Персонал примет заказ в админ-панели.',pricePending:'Цена после подтверждения персоналом',total:'Итого',tryAgain:'Попробовать снова',startTitle:'Чтобы начать, отсканируйте QR-код на столе',startBody:'Эта страница запускает оформление заказа, когда открыта по подписанной ссылке стола.',openLink:'Продолжить заказ'},
  ar:{title:'طلب مطعم Kassandra',lead:'طلب الطاولة عبر رمز QR',language:'اختر اللغة',meal:'لأي وجبة تريد الطلب؟',breakfast:'الإفطار',lunch:'الغداء',dinner:'العشاء',continue:'متابعة',back:'رجوع',menu:'القائمة',pdf:'فتح قائمة PDF',add:'إضافة',cart:'السلة',empty:'سلتك فارغة.',service:'نوع الخدمة',table:'خدمة الطاولة',room:'خدمة الغرفة',roomNo:'رقم الغرفة',note:'ملاحظة الطلب',allergy:'حساسية / تفضيل خاص',confirm1:'التأكيد الأول: هل السلة صحيحة؟',confirm2:'التأكيد الثاني: هل تريد إرسال الطلب إلى المطعم؟',send:'إرسال الطلب',pending:'تم إرسال طلبك إلى المطعم وهو بانتظار موافقة الموظف.',staff:'سيقبل الموظف الطلب من لوحة الإدارة.',pricePending:'السعر بعد تأكيد الموظف',total:'الإجمالي',tryAgain:'حاول مرة أخرى',startTitle:'امسح رمز QR الخاص بالطاولة للبدء',startBody:'تبدأ هذه الصفحة مسار الطلب عند فتحها برابط طاولة موقّع.',openLink:'متابعة الطلب'},
  fr:{title:'Commande Kassandra Restaurant',lead:'Commande à table par QR',language:'Choisir la langue',meal:'Pour quel repas souhaitez-vous commander ?',breakfast:'Petit-déjeuner',lunch:'Déjeuner',dinner:'Dîner',continue:'Continuer',back:'Retour',menu:'Menu',pdf:'Ouvrir le menu PDF',add:'Ajouter',cart:'Panier',empty:'Votre panier est vide.',service:'Type de service',table:'Service à table',room:'Service en chambre',roomNo:'Numéro de chambre',note:'Note de commande',allergy:'Allergie / préférence spéciale',confirm1:'1re confirmation : votre panier est-il correct ?',confirm2:'2e confirmation : envoyer cette commande au restaurant ?',send:'Envoyer la commande',pending:'Votre commande a été envoyée au restaurant et attend l’approbation du personnel.',staff:'Le personnel acceptera la commande depuis le panneau admin.',pricePending:'Prix après confirmation du personnel',total:'Total',tryAgain:'Réessayer',startTitle:'Scannez le QR de la table pour commencer',startBody:'Cette page lance le parcours de commande lorsqu’elle est ouverte avec un lien de table signé.',openLink:'Continuer la commande'},
  nl:{title:'Kassandra Restaurant Bestelling',lead:'Tafelbestelling via QR',language:'Kies taal',meal:'Voor welke maaltijd wilt u bestellen?',breakfast:'Ontbijt',lunch:'Lunch',dinner:'Diner',continue:'Doorgaan',back:'Terug',menu:'Menu',pdf:'PDF-menu openen',add:'Toevoegen',cart:'Winkelmand',empty:'Uw winkelmand is leeg.',service:'Servicetype',table:'Tafelservice',room:'Roomservice',roomNo:'Kamernummer',note:'Bestelnotitie',allergy:'Allergie / speciale voorkeur',confirm1:'1e bevestiging: klopt uw winkelmand?',confirm2:'2e bevestiging: bestelling naar het restaurant sturen?',send:'Bestelling verzenden',pending:'Uw bestelling is naar het restaurant verzonden en wacht op goedkeuring van het personeel.',staff:'Het personeel accepteert de bestelling via het adminpaneel.',pricePending:'Prijs na bevestiging door personeel',total:'Totaal',tryAgain:'Opnieuw proberen',startTitle:'Scan de tafel-QR om te beginnen',startBody:'Deze pagina start de bestelstroom wanneer zij wordt geopend met een ondertekende tafellink.',openLink:'Bestelling voortzetten'},
  es:{title:'Pedido Kassandra Restaurant',lead:'Pedido de mesa por QR',language:'Elegir idioma',meal:'¿Para qué comida desea pedir?',breakfast:'Desayuno',lunch:'Almuerzo',dinner:'Cena',continue:'Continuar',back:'Atrás',menu:'Menú',pdf:'Abrir menú PDF',add:'Añadir',cart:'Carrito',empty:'Su carrito está vacío.',service:'Tipo de servicio',table:'Servicio de mesa',room:'Servicio a la habitación',roomNo:'Número de habitación',note:'Nota del pedido',allergy:'Alergia / preferencia especial',confirm1:'1.ª confirmación: ¿su carrito es correcto?',confirm2:'2.ª confirmación: ¿enviar este pedido al restaurante?',send:'Enviar pedido',pending:'Su pedido fue enviado al restaurante y espera aprobación del personal.',staff:'El personal aceptará el pedido desde el panel de administración.',pricePending:'Precio tras confirmación del personal',total:'Total',tryAgain:'Intentar de nuevo',startTitle:'Escanee el QR de la mesa para comenzar',startBody:'Esta página inicia el flujo de pedido cuando se abre con un enlace de mesa firmado.',openLink:'Continuar pedido'}
};
const categoryLabels = {
  tr:{'Starters':'Başlangıçlar','Hot Starters':'Sıcak Başlangıçlar','Salads':'Salatalar','Main Courses':'Ana Yemekler','Seafood':'Deniz Ürünleri','Pastas':'Makarnalar','Pizzas':'Pizzalar','Burgers & Wraps':'Burgerler ve Wrapler','Snacks':'Atıştırmalıklar','Light Bites':'Hafif Lezzetler','Power Bowls':'Kaseler','Main Plates':'Ana Tabaklar',"Children's Menu":'Çocuk Menüsü','Desserts':'Tatlılar','Cocktails':'Kokteyller','Classic Cocktails':'Klasik Kokteyller','Champagne & Sparkling':'Şampanya ve Köpüklü','White Wines':'Beyaz Şaraplar','Rose Wines':'Rose Şaraplar','Red Wines':'Kırmızı Şaraplar'},
  en:{'Starters':'Starters','Hot Starters':'Hot Starters','Salads':'Salads','Main Courses':'Main Courses','Seafood':'Seafood','Pastas':'Pastas','Pizzas':'Pizzas','Burgers & Wraps':'Burgers & Wraps','Snacks':'Snacks','Light Bites':'Light Bites','Power Bowls':'Power Bowls','Main Plates':'Main Plates',"Children's Menu":"Children's Menu",'Desserts':'Desserts','Cocktails':'Cocktails','Classic Cocktails':'Classic Cocktails','Champagne & Sparkling':'Champagne & Sparkling','White Wines':'White Wines','Rose Wines':'Rose Wines','Red Wines':'Red Wines'}
};
function t(key){return (i18n[state.lang]||i18n.en)[key]||i18n.en[key]||key}
function esc(value){return String(value??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;')}
function locale(){return {tr:'tr-TR',de:'de-DE',ru:'ru-RU',ar:'ar',fr:'fr-FR',nl:'nl-NL',es:'es-ES'}[state.lang]||'en-US'}
function money(value){if(value===null||value===undefined||value==='')return t('pricePending');const n=Number(value);return Number.isFinite(n)?new Intl.NumberFormat(locale(),{maximumFractionDigits:2}).format(n)+' ₺':esc(value)}
function languageCode(){return String(state.lang||'tr').split('-')[0]}
function setLanguage(lang){state.lang=lang;document.documentElement.lang=lang;document.documentElement.dir=lang==='ar'?'rtl':'ltr'}
function allItems(){if(!state.cfg)return[];if(state.meal==='breakfast')return state.cfg.breakfast_items||[];return state.cfg.catalog_items||[]}
function itemName(item){if(state.lang==='tr')return item.name_tr||item.name_en||item.menu_item_id;return item.name_en||item.name_tr||item.menu_item_id}
function itemDescription(item){const code=languageCode();const localized=item['description_'+code];if(localized)return localized;if(code==='en')return item.description_en||item.description_tr||'';if(code==='tr')return item.description_tr||'';return ''}
function itemIngredients(item){const localized=item.ingredients_i18n?.[languageCode()];if(Array.isArray(localized)&&localized.length)return localized.filter(Boolean);return Array.isArray(item.ingredients)?item.ingredients.filter(Boolean):[]}
function itemSummary(item){const description=itemDescription(item);if(description)return description;const ingredients=itemIngredients(item);if(ingredients.length)return ingredients.slice(0,4).join(', ');return t('contentFallback')}
function itemDetails(item){const ingredients=itemIngredients(item);if(ingredients.length<=4)return '';return ingredients.join(', ')}
function cartRows(){const byId=Object.fromEntries(allItems().map(item=>[item.menu_item_id,item]));return Object.entries(state.cart).map(([id,row])=>({...row,item:byId[id]})).filter(row=>row.item)}
function cartCount(){return cartRows().reduce((sum,row)=>sum+row.quantity,0)}
function totalText(){let total=0;let hasMissing=false;for(const row of cartRows()){if(row.item.price_try===null||row.item.price_try===undefined){hasMissing=true;continue}total+=Number(row.item.price_try)*row.quantity}return hasMissing?money(null):money(total)}
function formatItemCount(count){return t('itemCount').replace('{count}',String(count))}
function brandLogoConfig(){const cfg=state.cfg||{};const brand=cfg.brand||cfg.restaurant_brand||{};const logo=cfg.logo||brand.logo||{};const url=cfg.logo_url||cfg.restaurant_logo_url||brand.logo_url||logo.url||logo.src||'';const alt=cfg.logo_alt||brand.logo_alt||logo.alt||cfg.venue||t('title');return {url:String(url||''),alt:String(alt||t('title'))}}
function logoMarkup(){const logo=brandLogoConfig();if(logo.url)return `<span class="brand-logo"><img src="${esc(logo.url)}" alt="${esc(logo.alt)}" loading="lazy"></span>`;const letter=(state.cfg?.venue||t('title')||'K').trim().charAt(0)||'K';return `<span class="brand-logo" aria-hidden="true">${esc(letter)}</span>`}
function categoryKey(item){return `${item.menu_type||state.meal||'menu'}::${item.category||t('menu')}`}
function categoryLabel(key){const parts=String(key||'').split('::');const raw=parts[1]&&parts[1]!==t('menu')?parts[1]:parts[0]||t('menu');return (categoryLabels[state.lang]||categoryLabels.en)[raw]||raw}
function categoriesFor(items){const seen=new Map();for(const item of items){const key=categoryKey(item);if(!seen.has(key))seen.set(key,{key,label:categoryLabel(key),count:0});seen.get(key).count+=1}return Array.from(seen.values())}
function normalizedSearch(){return state.search.trim().toLowerCase()}
function itemMatchesSearch(item,query){if(!query)return true;const haystack=[itemName(item),itemDescription(item),item.category,item.menu_type,...itemIngredients(item),...(item.tags||[]),...(item.dietary_tags||[])].join(' ').toLowerCase();return haystack.includes(query)}
function visibleItems(){const query=normalizedSearch();return allItems().filter(item=>(!state.activeCategory||categoryKey(item)===state.activeCategory)&&itemMatchesSearch(item,query))}
function languageSelector(){if(!state.cfg)return '';return `<div class="language-strip" aria-label="${esc(t('language'))}">${(state.cfg.supported_languages||[]).map(lang=>`<button class="language-chip ${lang.code===state.lang?'active':''}" data-lang="${esc(lang.code)}" aria-pressed="${lang.code===state.lang?'true':'false'}">${esc(lang.code.toUpperCase())}</button>`).join('')}</div>`}
function header(){const place=state.cfg?`${esc(t('tableNumberLabel'))} ${esc(state.cfg.table_no)} · ${esc(state.cfg.venue)}`:'-';return `<div class="order-top"><div class="brand">${logoMarkup()}<div class="brand-copy"><h1>${esc(t('title'))}</h1><p>${esc(t('lead'))}</p></div></div><div class="header-actions">${languageSelector()}<span class="pill">${place}</span></div></div>`}
function stepper(active){return `<div class="stepper" aria-hidden="true">${[1,2,3,4,5].map(n=>`<span class="dot ${n<=active?'active':''}"></span>`).join('')}</div>`}
function mealTabs(){return `<div class="meal-tabs" aria-label="${esc(t('meal'))}">${['breakfast','lunch','dinner'].map(meal=>`<button class="meal-tab ${meal===state.meal?'active':''}" data-meal="${meal}" aria-pressed="${meal===state.meal?'true':'false'}">${esc(t(meal))}</button>`).join('')}</div>`}
function render(){if(state.error)return app.innerHTML=`${header()}<div class="panel notice error">${esc(state.error)}<div class="footer-actions"><button class="secondary" data-action="reload">${esc(t('tryAgain'))}</button></div></div>`;if(state.step==='loading')return app.innerHTML=`<div class="panel"><h2>${esc(t('loadingTitle'))}</h2><div class="empty">${esc(t('loadingBody'))}</div></div>`;if(state.step==='entry')return renderEntry();if(state.step==='language')return renderLanguage();if(state.step==='meal')return renderMeal();if(state.step==='menu')return renderMenu();if(state.step==='service')return renderService();if(state.step==='confirm1')return renderConfirm(1);if(state.step==='confirm2')return renderConfirm(2);if(state.step==='success')return renderSuccess();}
function renderEntry(){app.innerHTML=`${header()}<section class="panel hero"><h2>${esc(t('startTitle'))}</h2><p>${esc(t('startBody'))}</p><form id="entryForm" class="hero-form" aria-label="${esc(t('openLink'))}"><div class="hero-actions"><button class="primary" type="submit">${esc(t('openLink'))}</button></div></form></section>`}
function renderLanguage(){app.innerHTML=`${header()}<section class="panel">${stepper(1)}<h2>${esc(t('language'))}</h2><div class="grid">${(state.cfg.supported_languages||[]).map(lang=>`<button class="card ${lang.code===state.lang?'active':''}" data-lang="${esc(lang.code)}" aria-pressed="${lang.code===state.lang?'true':'false'}"><strong>${esc(lang.label)}</strong><small>${esc(lang.code)}</small></button>`).join('')}</div><div class="footer-actions"><button class="primary" data-step="meal">${esc(t('continue'))}</button></div></section>`}
function renderMeal(){app.innerHTML=`${header()}<section class="panel">${stepper(2)}<h2>${esc(t('meal'))}</h2><div class="grid">${['breakfast','lunch','dinner'].map(meal=>`<button class="card ${meal===state.meal?'active':''}" data-meal="${meal}" aria-pressed="${meal===state.meal?'true':'false'}"><strong>${esc(t(meal))}</strong><small>${meal==='breakfast'?esc(t('breakfastOptionCount')):esc(t('menu'))}</small></button>`).join('')}</div><div class="footer-actions"><button class="secondary" data-step="language">${esc(t('back'))}</button><button class="primary" data-step="menu" ${state.meal?'':'disabled'}>${esc(t('continue'))}</button></div></section>`}
function productCard(item){const count=state.cart[item.menu_item_id]?.quantity||0;const details=itemDetails(item);return `<article class="card product-card"><div class="item-title"><b>${esc(itemName(item))}</b><span class="price">${money(item.price_try)}</span></div><p class="product-content">${esc(itemSummary(item))}</p>${details?`<details class="product-details"><summary>${esc(t('details'))}</summary><p><strong>${esc(t('ingredientsLabel'))}:</strong> ${esc(details)}</p></details>`:''}<div class="product-actions">${count?`<span class="qty-actions" aria-label="${esc(itemName(item))}"><button class="secondary" data-dec="${esc(item.menu_item_id)}" aria-label="${esc(itemName(item))} ${esc(t('decreaseQuantity'))}">-</button><strong>${count}</strong><button class="secondary" data-inc="${esc(item.menu_item_id)}" aria-label="${esc(itemName(item))} ${esc(t('increaseQuantity'))}">+</button></span>`:`<button class="primary" data-add="${esc(item.menu_item_id)}" aria-label="${esc(itemName(item))} ${esc(t('add'))}">${esc(t('add'))}</button>`}</div></article>`}
function renderCategorySections(items){const categories=categoriesFor(items);if(!items.length)return `<div class="empty">${esc(t('noResults'))}</div>`;return categories.map(category=>{const rows=items.filter(item=>categoryKey(item)===category.key);return `<section class="category-section" id="cat-${esc(category.key)}"><div class="category-heading"><h3>${esc(category.label)}</h3><span>${esc(formatItemCount(rows.length))}</span></div><div class="items">${rows.map(productCard).join('')}</div></section>`}).join('')}
function renderStickyCart(){const rows=cartRows();if(!rows.length)return '';return `<div class="sticky-cart" role="status" aria-live="polite"><div><strong>${esc(formatItemCount(cartCount()))}</strong><br><span>${esc(t('total'))}: ${totalText()}</span></div><button class="primary" data-step="service">${esc(t('continue'))}</button></div>`}
function renderMenu(){if(!state.meal)return renderMeal();const items=allItems();const filtered=visibleItems();const categories=categoriesFor(allItems());const mealCfg=state.cfg.meal_periods?.[state.meal]||{};const pdfs=(mealCfg.pdf_keys||[]).map(key=>state.cfg.pdf_menus?.[key]).filter(Boolean);const activeExists=categories.some(category=>category.key===state.activeCategory);const rail=[{key:'',label:t('allCategories'),count:items.length},...categories];app.innerHTML=`${header()}<section class="panel">${stepper(3)}<div class="menu-heading-row"><h2>${esc(t('menu'))}</h2>${mealTabs()}</div>${pdfs.length?`<div class="pdf-strip"><span>${esc(t('pdfSecondary'))}</span>${pdfs.map(pdf=>`<a class="secondary pdf-link" href="${esc(pdf.url)}" target="_blank" rel="noopener">${esc(pdf.label)} · ${esc(t('pdf'))}</a>`).join('')}</div>`:''}<div class="order-menu-layout"><div class="order-menu-main"><div class="order-search"><input id="menuSearch" value="${esc(state.search)}" placeholder="${esc(t('searchPlaceholder'))}" aria-label="${esc(t('searchPlaceholder'))}"></div><nav class="order-category-rail" aria-label="${esc(t('categoryNavLabel'))}">${rail.map(category=>`<button class="category-chip ${category.key===(activeExists?state.activeCategory:'')?'active':''}" data-cat="${esc(category.key)}" aria-pressed="${category.key===(activeExists?state.activeCategory:'')?'true':'false'}">${esc(category.label)} <small>${category.count}</small></button>`).join('')}</nav>${renderCategorySections(filtered)}<div class="footer-actions"><button class="secondary" data-step="meal">${esc(t('back'))}</button><button class="primary" data-step="service" ${cartRows().length?'':'disabled'}>${esc(t('continue'))}</button></div></div><aside class="cart-panel" aria-label="${esc(t('cart'))}">${renderCart()}</aside></div></section>${renderStickyCart()}`}
function renderCart(){const rows=cartRows();if(!rows.length)return `<h3>${esc(t('cart'))}</h3><div class="empty">${esc(t('empty'))}</div>`;return `<h3>${esc(t('cart'))}</h3><div class="summary">${rows.map(row=>`<div class="summary-row"><span>${row.quantity}x ${esc(itemName(row.item))}</span><span class="qty-actions"><button class="secondary" data-dec="${esc(row.item.menu_item_id)}" aria-label="${esc(itemName(row.item))} ${esc(t('decreaseQuantity'))}">-</button><button class="secondary" data-inc="${esc(row.item.menu_item_id)}" aria-label="${esc(itemName(row.item))} ${esc(t('increaseQuantity'))}">+</button></span></div>`).join('')}<div class="summary-row"><strong>${esc(t('total'))}</strong><strong>${totalText()}</strong></div></div>`}
function renderService(){app.innerHTML=`${header()}<section class="panel">${stepper(4)}<h2>${esc(t('service'))}</h2><div class="grid-2"><button class="card ${state.serviceType==='table_service'?'active':''}" data-service="table_service" aria-pressed="${state.serviceType==='table_service'?'true':'false'}"><strong>${esc(t('table'))}</strong><small>${esc(t('tableNumberLabel'))} ${esc(state.cfg.table_no)}</small></button><button class="card ${state.serviceType==='room_service'?'active':''}" data-service="room_service" aria-pressed="${state.serviceType==='room_service'?'true':'false'}"><strong>${esc(t('room'))}</strong><small>${esc(t('roomNo'))}</small></button></div><form id="serviceForm"><div class="field" ${state.serviceType==='room_service'?'':'hidden'}><label>${esc(t('roomNo'))}</label><input name="roomNumber" value="${esc(state.roomNumber)}" maxlength="32" autocomplete="off"></div><div class="field"><label>${esc(t('note'))}</label><textarea name="customerNote" maxlength="500">${esc(state.customerNote)}</textarea></div><div class="field"><label>${esc(t('allergy'))}</label><textarea name="allergyNote" maxlength="500">${esc(state.allergyNote)}</textarea></div><div class="footer-actions"><button class="secondary" type="button" data-step="menu">${esc(t('back'))}</button><button class="primary" type="submit">${esc(t('continue'))}</button></div></form></section>`}
function renderConfirm(number){app.innerHTML=`${header()}<section class="panel">${stepper(5)}<h2>${esc(number===1?t('confirm1'):t('confirm2'))}</h2>${renderCart()}<div class="notice">${esc(t('staff'))}</div><div class="footer-actions"><button class="secondary" data-step="${number===1?'service':'confirm1'}">${esc(t('back'))}</button><button class="primary" data-action="${number===1?'confirm-once':'submit'}" ${state.submitting?'disabled':''}>${esc(number===1?t('continue'):t('send'))}</button></div></section>`}
function renderSuccess(){app.innerHTML=`${header()}<section class="panel success-card"><h2>${esc(t('pending'))}</h2><p class="notice">${esc(t('staff'))}</p><p class="pill">${esc(state.success?.order_id||'')}</p></section>`}
app.addEventListener('click',event=>{const node=event.target.closest('button,a');if(!node)return;if(node.dataset.lang){setLanguage(node.dataset.lang);render();return}if(node.dataset.meal){const nextMeal=node.dataset.meal;if(state.meal!==nextMeal){state.meal=nextMeal;state.cart={};state.search='';state.activeCategory=''}render();return}if(node.dataset.cat!==undefined){state.activeCategory=node.dataset.cat;render();return}if(node.dataset.service){state.serviceType=node.dataset.service;render();return}if(node.dataset.step){state.step=node.dataset.step;render();return}if(node.dataset.add){state.cart[node.dataset.add]={quantity:(state.cart[node.dataset.add]?.quantity||0)+1};render();return}if(node.dataset.inc){if(state.cart[node.dataset.inc])state.cart[node.dataset.inc].quantity+=1;render();return}if(node.dataset.dec){const row=state.cart[node.dataset.dec];if(row){row.quantity-=1;if(row.quantity<=0)delete state.cart[node.dataset.dec]}render();return}if(node.dataset.action==='confirm-once'){state.step='confirm2';render();return}if(node.dataset.action==='submit'){submitOrder();return}if(node.dataset.action==='reload'){window.location.reload();}});
app.addEventListener('input',event=>{if(event.target.id==='menuSearch'){state.search=event.target.value;window.clearTimeout(searchRenderTimer);searchRenderTimer=window.setTimeout(()=>{render();const search=document.getElementById('menuSearch');if(search){search.focus();search.setSelectionRange(search.value.length,search.value.length)}},120);}});
app.addEventListener('submit',event=>{event.preventDefault();if(event.target.id==='entryForm'){window.location.href=DEFAULT_ENTRY_ORDER_URL;return}const form=new FormData(event.target);state.roomNumber=String(form.get('roomNumber')||'').trim();state.customerNote=String(form.get('customerNote')||'').trim();state.allergyNote=String(form.get('allergyNote')||'').trim();if(state.serviceType==='room_service'&&!state.roomNumber){event.target.roomNumber.focus();return}state.step='confirm1';render();});
async function submitOrder(){state.submitting=true;render();const items=cartRows().map(row=>({menu_item_id:row.item.menu_item_id,quantity:row.quantity}));try{const response=await fetch('/api/v1/public/restaurant-order/orders',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token,language_code:state.lang,meal_period:state.meal,service_type:state.serviceType,items,customer_note:state.customerNote||null,allergy_note:state.allergyNote||null,room_number:state.serviceType==='room_service'?state.roomNumber:null,customer_confirmation_count:2})});const payload=await response.json().catch(()=>({}));if(!response.ok)throw new Error(payload.detail||t('submitError'));state.success=payload;state.step='success'}catch(error){state.error=error.message||t('submitError')}finally{state.submitting=false;render();}}
async function init(){if(!token){state.step='entry';return render()}try{const response=await fetch('/api/v1/public/restaurant-order/config?token='+encodeURIComponent(token));const payload=await response.json().catch(()=>({}));if(!response.ok)throw new Error(payload.detail||t('configError'));state.cfg=payload;setLanguage(payload.default_language||'tr');state.step='language'}catch(error){state.error=error.message||t('configError')}render();}
init();
"""
