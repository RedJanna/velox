# Chat Lab Turkish Terminology

Bu belge, Chat Lab arayüzündeki kullanıcıya görünen metinler için standart terim setini tanımlar.
Amaç, aynı kavramın farklı yerlerde farklı Türkçe karşılıklarla görünmesini önlemektir.

## İlkeler

- Dil sade, profesyonel ve operasyon odaklı olmalıdır.
- Aynı kavram için tek Türkçe karşılık kullanılmalıdır.
- Geliştirici iç dili doğrudan arayüze taşınmamalıdır.
- Türkçe karakterler tam kullanılmalıdır; ASCII Türkçe kabul edilmez.
- Arayüz metninde gereksiz İngilizce bırakılmamalıdır.

## Standart Terimler

| Kavram | Standart Kullanım | Kaçınılacak Kullanımlar |
|---|---|---|
| Chat Lab | Chat Lab | Test Paneli |
| Diagnostics | Tanılama | Diagnostics |
| Feedback Studio | Geri Bildirim Alanı | Feedback Studio |
| Conversation state | Konuşma durumu | Conversation State |
| Intent | Niyet | Intent |
| Risk flags | Risk işaretleri | Risk Flags |
| Next step | Sonraki adım | Next Step |
| Role mapping | Rol eşleştirme | Role Mapping |
| Audit | Denetim İzi | Audit |
| Imports | İçe Aktarımlar | Importlar |
| Export | Dışa Aktarım | Export |
| Reset | Sıfırla | Reset |
| Read only | Salt okunur | Read only |
| Human queue / handoff | Temsilci / İnsan devri | İnsan |
| AI draft / suggestion | Yapay zekâ taslağı / Yapay zekâ önerisi | AI draft, AI önerisi |
| Regenerate | Yeniden Oluştur | Yeniden İşle |
| Reject | Reddet | Gönderme |
| Approved example | Onaylı örnek | approved_examples |
| Gold standard | Referans yanıt | Altın Standart |
| Problem state | Dikkat Gerektiriyor | Sorunlu |
| Role issue | Niyet Kaçırma | Niyet Iskalama |

## Yazım Kuralları

- `yapay zekâ` küçük harfli genel kullanımdır.
- Buton ve sekme başlıklarında başlık biçimi kullanılabilir: `Yeniden Oluştur`, `Dışa Aktarım`.
- Durum rozetlerinde kısa ama açık ifadeler tercih edilir: `BEKLİYOR`, `REDDEDİLDİ`, `GÖNDERİLDİ`.
- Yöneticiye dönük hata mesajları da kullanıcı diliyle yazılmalıdır.

## Uygulama Notları

- Yeni UI metni eklenirken bu dosyadaki karşılıklar esas alınmalıdır.
- Backend `HTTPException.detail` ve toast mesajları da aynı sözlüğe uymalıdır.
- Kod içi anahtarlar ve veri şemaları İngilizce kalabilir; bu belge yalnızca kullanıcıya görünen metinler içindir.
