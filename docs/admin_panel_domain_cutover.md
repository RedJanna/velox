# Admin Panel Domain Cutover

Admin panel artik uygulama icinden `/admin` rotasinda sunulur ve public panel adresi `https://nexlumeai.com/admin` olarak beklenir.

## Uygulama ayarlari

Uretim ortaminda asagidaki degiskenleri doldurun:

```env
PUBLIC_BASE_URL=https://nexlumeai.com
ADMIN_PANEL_PATH=/admin
APP_TRUSTED_HOSTS=nexlumeai.com,www.nexlumeai.com
ADMIN_BOOTSTRAP_TOKEN=<tek-kullanimlik-guclu-token>
ADMIN_TOTP_ISSUER=NexlumeAI
```

Notlar:

- Uygulama root (`/`) istegini HTML istemciler icin otomatik olarak `/admin` rotasina yonlendirir.
- Uvicorn `--proxy-headers` ile calistigi icin reverse proxy veya Cloudflare arkasinda dogru host/scheme bilgisi korunur.
- `ADMIN_BOOTSTRAP_TOKEN` ayarlanirsa ilk admin hesabi public domain uzerinden de guvenli sekilde bootstrap edilebilir.
- Token tanimli degilse ilk bootstrap sadece yerel sunucu erisimi icin acik kalir.

## Cloudflare cutover

Cloudflare dashboard tarafinda disaridan yapilmasi gerekenler:

1. `nexlumeai.com` ve gerekiyorsa `www.nexlumeai.com` icin origin sunucusuna giden `A`, `AAAA` veya `CNAME` kaydini olusturun/guncelleyin.
2. Web trafigi icin kullanilan bu kayitlari `Proxied` modda tutun.
3. SSL/TLS modunu `Full (strict)` olarak ayarlayin.
4. Origin tarafinda `443 -> 8001` reverse proxy veya load balancer yonlendirmesini dogrulayin.
5. Origin proxy, `Host`, `X-Forwarded-For` ve `X-Forwarded-Proto` basliklarini uygulamaya iletsin.

## Ilk kurulum akisi

1. `https://nexlumeai.com/admin` sayfasini acin.
2. Eger sistemde henuz admin kullanicisi yoksa bootstrap formu gorunur.
3. Public domain uzerinden bootstrap yapilacaksa `ADMIN_BOOTSTRAP_TOKEN` ile ilk admin kullanicisini olusturun.
4. Donen TOTP secret veya `otpauth` URI ile authenticator uygulamasina kayit yapin.
5. Sonraki girislerde kullanici adi + sifre + 6 haneli OTP kodu kullanin.

## Dogrulama

Cutover sonrasi asagidaki kontrolleri yapin:

```bash
curl -fsS https://nexlumeai.com/api/v1/health
curl -fsS https://nexlumeai.com/api/v1/health/ready
curl -fsS https://nexlumeai.com/api/v1/admin/bootstrap/status
curl -I https://nexlumeai.com/
curl -I https://nexlumeai.com/admin
```
