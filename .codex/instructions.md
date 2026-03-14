# Codex — Velox Proje Talimatlari

## Guvenlik Sinirlari (Claude Code Esdegeri)

Bu talimatlar, Codex'in Velox projesinde Claude Code ile ayni guvenlik
sinirlarinda calismasi icin zorunlu kurallardir.

### Yasak Islemler — Onay Olsa Bile Yapilmaz
- `.env`, `*.pem`, `*.key`, `credentials.*`, `secrets.*` dosyalarini OKUMA veya YAZMA
- Proje dizini disindaki herhangi bir dosyaya erisim
- `rm -rf`, `git reset --hard`, `git push --force` gibi geri donulemez komutlar
- Ag uzerinden proje dosyasi icerigi gonderme
- Yeni kullanici hesabi olusturma veya credential girisi

### Onay Gerektiren Islemler
- Her dosya yazma/silme islemi (`safe` profilde otomatik sorulur)
- `git commit`, `git push` islemleri
- Yeni bagimlilik yukleme (`pip install`, `npm install`)
- Docker container baslatma/durdurma
- Veritabani migration calistirma

### Dokumanstasyon Sorumlulugu
Kod degisikligi sonrasi `system_prompt_velox.md` §5 (Dokumantasyon
Senkronizasyon Politikasi) kurallarina uy:
- Degisikligin etkisini analiz et
- Etkilenen belgeleri gozden gecir
- Gerekiyorsa ayni commit icinde guncelle

### Kural Hiyerarsisi
1. `skills/security_privacy.md` — asla override edilemez
2. `skills/anti_hallucination.md` — kaynak dogrulama
3. Diger skill dosyalari
4. `system_prompt_velox.md` — AI agent davranis kurallari
5. `tasks/` — gorev dosyalari

Her gorev oncesi `SKILL.md` dosyasini oku ve ilgili skill'leri takip et.
