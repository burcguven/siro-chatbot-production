# SIRO HR Chatbot Deployment Guide

Bu dosya, SIRO HR Chatbot uygulamasının Docker Compose ile çalıştırılması için kısa bir özet sunar.

Detaylı Dockerization ve deployment dokümanı PDF olarak aynı klasörde yer alacaktır:

`docs/SIRO_HR_Chatbot_Dockerization_and_Deployment.pdf`

## Servisler

| Servis | Açıklama | Local Adres |
|---|---|---|
| Backend | FastAPI tabanlı API ve RAG pipeline servisi | http://localhost:8000 |
| Frontend | React/Vite arayüzü, Nginx üzerinden servis edilir | http://localhost:3000 |
| Backend Swagger | Backend API dokümantasyonu | http://localhost:8000/docs |

## Beklenen Klasör Yapısı

Bu deployment reposu, backend ve frontend repoları ile aynı üst dizinde bulunmalıdır:

    Desktop/
    ├── siro_hr_chatbot/
    ├── siro_chatbot_FE/
    └── siro-hr-chatbot-deployment/

## Environment Kullanımı

Gerçek `.env` dosyası Git'e eklenmez. Local çalıştırma için önce örnek dosya kopyalanır:

    cp .env.example .env

Local ortam için beklenen değer:

    VITE_CHATBOT_BACKEND_API=http://localhost:8000

Production ortamında bu değer gerçek backend API domain'i ile değiştirilmelidir.

Örnek:

    VITE_CHATBOT_BACKEND_API=https://api-chatbot.siro.com

## Local Çalıştırma

Sistemi build edip başlatmak için:

    docker compose up --build

Arka planda çalıştırmak için:

    docker compose up --build -d

Çalışan container'ları görmek için:

    docker ps

Logları görüntülemek için:

    docker compose logs -f

Sistemi durdurmak için:

    docker compose down

## Kalıcı Veri

Backend tarafında iki klasör volume olarak bağlanmıştır:

| Klasör | Amaç |
|---|---|
| uploaded_documents | Admin panelinden yüklenen dokümanları kalıcı tutar |
| faiss_index_3b | FAISS index dosyalarını kalıcı tutar |

## Production Notu

Production deployment için domain, DNS, reverse proxy ve SSL ayarları yapılmalıdır. Local ortamda kullanılan localhost adresleri production ortamında gerçek domain veya subdomain adresleri ile değiştirilir.

Detaylı açıklamalar için PDF dokümanına bakılmalıdır.
