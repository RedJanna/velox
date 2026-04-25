# Local Demo Environment

Bu belge, backend ve admin panel degisikliklerinin canli ortama gitmeden once yerelde gorulmesi icin kullanilan demo akisini tanimlar.

## Amac

- Canli panel adresi olan `https://velox.nexlumeai.com/admin` etkilenmeden once degisiklikleri yerelde gormek
- Backend degisikliklerinin admin panel ve Chat Lab yuzeyine nasil yansidigini ayri bir demo adreste dogrulamak
- Canliya ozel public domain, Cloudflare Tunnel veya canli DB/Redis bagimliligi olmadan calismak

## Demo adresi

Yerel demo admin adresi:

```text
http://127.0.0.1:8011/admin
```

`APP_PORT` degerini `.env.demo.local` icinde degistirirseniz bu adres de degisir.

## Kurulum

1. Demo env dosyasini olusturun:

```bash
cp .env.demo.example .env.demo.local
```

2. `.env.demo.local` icindeki gerekli degerleri duzenleyin.

Minimum kritik alanlar:

- `OPENAI_API_KEY`
- `PHONE_HASH_SALT`
- `ADMIN_JWT_SECRET`
- `ADMIN_WEBHOOK_SECRET`
- Gerekli ise Elektra/WhatsApp test credential'lari

Guvenlik notu:

- `PUBLIC_BASE_URL` yerel adres olarak kalmali: `http://127.0.0.1:8011`
- `OPERATION_MODE=test` olarak kalmali
- `CLOUDFLARE_TUNNEL_TOKEN` bos kalmali

## Baslatma

```bash
bash scripts/up_local_demo.sh
```

Bu komut:

1. `velox-demo` compose project'ini ayaga kaldirir
2. Local demo stack'i build eder
3. App startup sirasinda migration runner'in tamamlanmasini bekler
4. `health` ve `/admin` ile temel dogrulamayi yapar
5. `health/ready` sonucu kirmizi ise bunu bilgi notu olarak gosterir

## Durdurma

```bash
bash scripts/down_local_demo.sh
```

## Mimari davranis

Demo stack:

- bagimsiz `docker-compose.demo.yml` ile calisir
- ayri compose project adi kullanir: `velox-demo`
- ayri Postgres volume kullanir: `pgdata_demo`
- ayri Redis volume kullanir: `redisdata_demo`
- `cloudflared` baslatmaz
- app container'ini stabil demo runtime ile calistirir; `uvicorn --reload` kapali tutulur
- schema olusumunu Postgres `initdb` hook'una degil app startup migration runner'ina birakir

Bu sayede:

- kod degisiklikleri bind mount uzerinden demo app'e yansir
- Python/route/admin panel degisiklikleri app restart sonrasi gorulur
- canliya bagli tunnel veya public domain akisi acilmaz

## Backend degisikliklerinin frontend'e yansimasi

Iki durum vardir:

### 1. Kod ve UI degisikligi

Ornek:

- FastAPI route degisikligi
- admin panel UI degisikligi
- embedded JS/CSS degisikligi
- repository/service mantigi degisikligi

Bu tip degisikliklerden sonra demo app'i yeniden baslatin ve tarayicida `http://127.0.0.1:8011/admin` sayfasini yenileyin:

```bash
docker compose --env-file .env.demo.local -f docker-compose.demo.yml -p velox-demo restart app
```

### 2. Schema / migration degisikligi

Ornek:

- yeni tablo
- yeni kolon
- yeni index
- yeni constraint

Demo app startup sirasinda migration'lari otomatik uygular. Cogu durumda yeni migration dosyasini kaydetmek veya app'i yeniden baslatmak yeterlidir:

```bash
docker compose --env-file .env.demo.local -f docker-compose.demo.yml -p velox-demo restart app
```

Eger app startup migration'i yarida kaldiysa veya elle catch-up gerekiyor ise fallback olarak su tek satir komut kullanilir:

```bash
docker compose --env-file .env.demo.local -f docker-compose.demo.yml -p velox-demo exec app python -m velox.db.migrate
```

## Dogrulama

```bash
curl -fsS http://127.0.0.1:8011/api/v1/health
curl -fsS http://127.0.0.1:8011/admin >/dev/null
curl -fsS http://127.0.0.1:8011/api/v1/health/ready
```

Not:

- `health` + `/admin` basariliysa demo panel acilmaya hazirdir.
- `health/ready` degeri demo env'de Elektra gibi opsiyonel entegrasyon credential'lari eksikse `503` kalabilir.
- Bu durum frontend yansimasini yerelde gormeyi tek basina engellemez; ancak ilgili entegrasyon akislari icin test credential'i girilmelidir.

## Canli ortamdan farki

Local demo:

- local port kullanir
- public hostname gerektirmez
- tunnel acmaz
- `OPERATION_MODE=test` ile daha guvenli calisir
- canli admin URL'sine dokunmaz

Canli ortam:

- mevcut public adresi kullanir
- production env ile ayri yonetilir
- local demo ile ayni compose project'i kullanmaz
