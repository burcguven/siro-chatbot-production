# SIRO HR Chatbot Deployment

Bu repo, SIRO HR Chatbot uygulamasının Docker Compose ile çalıştırılması ve deployment sürecinde kullanılacak konfigürasyon dosyalarını içerir.

## İçerik

- `docker-compose.yml`: Backend ve frontend servislerini birlikte build edip çalıştırır.
- `.env.example`: Frontend build sırasında kullanılacak backend API adresi için örnek environment dosyasıdır.
- `docs/deployment-guide.md`: Dockerization ve deployment sürecinin teknik açıklamasını içerir.

## Beklenen Local Klasör Yapısı

Bu repo, backend ve frontend repoları ile aynı üst dizinde duracak şekilde hazırlanmıştır.

    Desktop/
    ├── siro_hr_chatbot/
    ├── siro_chatbot_FE/
    └── siro-hr-chatbot-deployment/

## Local Çalıştırma

Önce `.env.example` dosyasını `.env` olarak kopyalayın:

    cp .env.example .env

Ardından sistemi başlatın:

    docker compose up --build

Arka planda çalıştırmak için:

    docker compose up --build -d

Servisleri durdurmak için:

    docker compose down

## Local Erişim Adresleri

- Frontend: http://localhost:3000
- Backend Swagger: http://localhost:8000/docs

## Production Notu

Local ortamda `localhost` kullanılması beklenen bir durumdur. Production ortamında `VITE_CHATBOT_BACKEND_API` değeri gerçek backend API domain'i ile değiştirilmelidir.

Örnek:

    VITE_CHATBOT_BACKEND_API=https://api-chatbot.siro.com

Bu değer değiştirildikten sonra frontend image yeniden build edilmelidir.
