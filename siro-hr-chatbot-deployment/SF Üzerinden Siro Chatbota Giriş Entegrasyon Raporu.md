# **SuccessFactors Üzerinden Siro HR Chatbot Uygulamasına Giriş Entegrasyon Raporu**

## **1\. Amaç**

Bu raporun amacı, Siro HR Chatbot uygulamasının SuccessFactors uygulaması içerisinden hem normal çalışan kullanıcılar hem de admin kullanıcıları tarafından nasıl açılacağını ve bunun için SuccessFactors tarafında hangi yazılımsal güncellemelerin yapılması gerektiğini açıklamaktır.

Siro HR Chatbot uygulamasında iki farklı kullanıcı tipi bulunmaktadır:

1. Normal çalışan kullanıcılar  
2. Admin kullanıcılar

Normal çalışan kullanıcılar chatbot uygulamasına doğrudan kullanıcı adı ve şifre ile giriş yapmayacaktır. Çalışan kullanıcılar zaten SuccessFactors sisteminde oturum açmış durumda olduğu için chatbot uygulamasına SuccessFactors üzerinden yönlendirilecektir.

Admin kullanıcılar ise SuccessFactors üzerinde tanımlanacak ayrı bir admin bağlantısı üzerinden chatbot admin giriş sayfasına yönlendirilecektir.

---

## **2\. Genel Giriş Mimarisi**

Siro HR Chatbot uygulaması iki ana parçadan oluşmaktadır:

* Frontend uygulaması  
* Backend API uygulaması

Örnek production adresleri aşağıdaki gibi düşünülmelidir:

```
FRONTEND_API = https://siro-chatbot.siro.energy
BACKEND_API  = https://siro-chatbot-api.siro.energy
```

Admin giriş URL’i:

```
https://siro-chatbot.siro.energy/admin-login
```

Normal kullanıcılar için giriş süreci ise doğrudan frontend URL’ine gidilerek yapılmaz. Normal kullanıcı girişinde SuccessFactors, chatbot backend API’sine bir POST request göndermelidir.

Normal kullanıcı giriş endpoint’i:

```
POST https://siro-chatbot-api.siro.energy/api/sf-login
```

---

## **3\. Normal Kullanıcı Giriş Akışı**

Normal çalışan kullanıcılar için giriş akışı aşağıdaki gibidir:

1. Kullanıcı kendi bilgisayarında SuccessFactors uygulamasına giriş yapar.  
2. SuccessFactors içerisinde “Siro HR Chatbot” bağlantısına veya butonuna tıklar.  
3. SuccessFactors, giriş yapan kullanıcının personel numarasını, yani PERNR bilgisini alır.  
4. SuccessFactors, chatbot backend API’sine güvenli bir POST request gönderir.  
5. Backend, gelen isteğin gerçekten SuccessFactors tarafından gönderildiğini kontrol eder.  
6. Backend, kullanıcı için kısa süreli ve tek kullanımlık geçici giriş token’ı oluşturur.  
7. Backend, SuccessFactors’a bir `redirect_url` döner.  
8. SuccessFactors, kullanıcının tarayıcısını bu `redirect_url` adresine yönlendirir.  
9. Backend callback endpoint’i token’ı doğrular.  
10. Backend, PERNR bilgisiyle SAP çalışan servisine istek atar.  
11. SAP üzerinde çalışan aktifse kullanıcı chatbot sisteminde bulunur veya otomatik oluşturulur.  
12. Backend, kullanıcı için chatbot access token üretir.  
13. Backend kullanıcıyı frontend callback sayfasına yönlendirir.  
14. Frontend token’ı kaydeder ve kullanıcıyı chatbot ekranına gönderir.

Sonuç olarak kullanıcı, SuccessFactors üzerinden otomatik olarak chatbot uygulamasına giriş yapmış olur.

---

## **4\. SuccessFactors Tarafında Normal Kullanıcı İçin Yapılması Gereken Yazılım Güncellemesi**

SuccessFactors tarafında normal çalışan kullanıcılar için bir chatbot bağlantısı, butonu veya menü öğesi eklenmelidir.

Bu buton doğrudan şu adrese gitmemelidir:

```
https://siro-chatbot.siro.energy/chat
```

Çünkü normal kullanıcıların chatbot sistemine güvenli şekilde giriş yapabilmesi için önce backend tarafında oturum token’ı oluşturulmalıdır.

Bu nedenle SuccessFactors tarafında yapılması gereken işlem şudur:

Kullanıcı chatbot butonuna bastığında, SuccessFactors sistemi backend API’ye aşağıdaki POST request’i göndermelidir:

```
POST https://siro-chatbot-api.siro.energy/api/sf-login
Content-Type: application/json
```

Request body:

```json
{
  "pernr": "<GIRIS_YAPAN_KULLANICININ_PERSONEL_NUMARASI>",
  "api_key": "<SUCCESSFACTORS_CHATBOT_API_KEY>"
}
```

Örnek:

```json
{
  "pernr": "30000228",
  "api_key": "********"
}
```

Burada:

* `pernr`: SuccessFactors’a giriş yapan çalışanın personel numarasıdır.  
* `api_key`: SuccessFactors ile chatbot backend’i arasında kullanılan güvenlik anahtarıdır.  
* `api_key` frontend tarafında veya kullanıcının tarayıcısında görünmemelidir.  
* Bu istek mümkünse SuccessFactors’ın backend/server-side mekanizması üzerinden gönderilmelidir.  
* API key client-side JavaScript içine yazılmamalıdır.

Backend başarılı cevap döndüğünde response şu yapıda olacaktır:

```json
{
  "redirect_url": "https://siro-chatbot-api.siro.energy/auth/callback?token=TEMPORARY_TOKEN",
  "expires_in_seconds": 90,
  "message": "Geçici giriş bağlantısı oluşturuldu."
}
```

SuccessFactors bu cevaptaki `redirect_url` değerini almalı ve kullanıcının tarayıcısını bu adrese yönlendirmelidir.

Örneğin:

```
https://siro-chatbot-api.siro.energy/auth/callback?token=TEMPORARY_TOKEN
```

Bu URL kullanıcı tarafından manuel oluşturulmamalıdır. Backend tarafından üretilen tek kullanımlık geçici token ile oluşturulmalıdır.

---

## **5\. Normal Kullanıcı İçin Güvenlik Kuralları**

Normal kullanıcı girişinde aşağıdaki kurallara dikkat edilmelidir:

1. Kullanıcı frontend `/chat` sayfasına doğrudan gönderilmemelidir.  
2. SuccessFactors önce backend `/api/sf-login` endpoint’ine POST request göndermelidir.  
3. Request içinde giriş yapan kullanıcının doğru PERNR bilgisi yer almalıdır.  
4. API key sadece SuccessFactors sistemi ve backend arasında kullanılmalıdır.  
5. API key tarayıcıda, frontend kodunda veya URL içinde görünmemelidir.  
6. Backend tarafından dönen `redirect_url` kısa süreli ve tek kullanımlık olmalıdır.  
7. Kullanıcı bu `redirect_url` ile backend callback endpoint’ine yönlendirilmelidir.  
8. Backend callback tamamlandıktan sonra kullanıcı frontend `/auth/callback` sayfasına yönlendirilir.  
9. Frontend callback sayfası access token’ı alır ve kullanıcıyı `/chat` sayfasına gönderir.

Bu akış sayesinde normal çalışan kullanıcılar için ayrıca chatbot şifresi tutulmasına gerek kalmaz.

---

## **6\. Normal Kullanıcı İçin Beklenen Teknik Akış**

Normal kullanıcı chatbot butonuna tıkladığında SuccessFactors tarafında uygulanması gereken akış özetle şu şekildedir:

```
SuccessFactors kullanıcıyı tanır
        ↓
Kullanıcının PERNR bilgisini alır
        ↓
POST BACKEND_API/api/sf-login isteği gönderir
        ↓
Backend redirect_url döner
        ↓
SuccessFactors kullanıcıyı redirect_url adresine yönlendirir
        ↓
Backend SAP çalışan bilgisini kontrol eder
        ↓
Backend chatbot token üretir
        ↓
Backend kullanıcıyı frontend /auth/callback sayfasına yönlendirir
        ↓
Frontend kullanıcıyı /chat sayfasına alır
```

---

## **7\. Admin Kullanıcı Giriş Akışı**

Admin kullanıcıların giriş akışı normal çalışanlardan farklıdır.

Admin kullanıcılar için SuccessFactors tarafında ayrı bir admin chatbot bağlantısı tanımlanmalıdır.

Admin giriş URL’i:

```
https://siro-chatbot.siro.energy/admin-login
```

Admin kullanıcı bu linke tıkladığında doğrudan chatbot frontend uygulamasındaki admin login sayfasına gider.

Admin girişinde SuccessFactors’ın backend’e PERNR göndermesine gerek yoktur.

Admin kullanıcılar chatbot admin giriş ekranında kendi admin e-posta ve şifreleriyle giriş yapar.

Admin login endpoint’i frontend tarafından çağrılır:

```
POST https://siro-chatbot-api.siro.energy/admin/login
Content-Type: application/json
```

Request body:

```json
{
  "email": "admin@siro.com",
  "password": "******"
}
```

Başarılı girişte backend admin access token döner. Frontend bu token’ı kaydeder ve admin kullanıcıyı admin dashboard sayfasına yönlendirir.

---

## **8\. SuccessFactors Tarafında Admin Kullanıcı İçin Yapılması Gereken Yazılım Güncellemesi**

SuccessFactors tarafında admin kullanıcılar için ayrı bir bağlantı, menü öğesi veya tile oluşturulmalıdır.

Bu bağlantı şu URL’e yönlendirmelidir:

```
https://siro-chatbot.siro.energy/admin-login
```

Bu bağlantı sadece yetkili admin kullanıcılar tarafından görülebilmelidir.

Admin linki için SuccessFactors tarafında yapılması gerekenler:

1. “Siro HR Chatbot Admin Panel” isimli bir menü öğesi veya tile oluşturulmalıdır.  
2. Bu menü öğesi yalnızca ilgili admin rolüne sahip kullanıcılara gösterilmelidir.  
3. Link doğrudan frontend admin giriş sayfasına gitmelidir:

```
https://siro-chatbot.siro.energy/admin-login
```

4.   
   Admin girişinde SuccessFactors tarafından backend’e PERNR gönderilmesine gerek yoktur.  
5. Admin kullanıcılar chatbot sisteminde tanımlı admin hesabı ile giriş yapacaktır.  
6. Admin kullanıcı giriş yaptıktan sonra chatbot admin dashboard ekranına yönlendirilir.

---

## **9\. Normal Kullanıcı ve Admin Girişleri Arasındaki Fark**

| Özellik | Normal Kullanıcı | Admin Kullanıcı |
| ----- | ----- | ----- |
| Giriş başlangıcı | SuccessFactors chatbot butonu | SuccessFactors admin chatbot linki |
| Kullanılan URL | Backend `/api/sf-login` POST request | Frontend `/admin-login` |
| PERNR gerekir mi? | Evet | Hayır |
| API key gerekir mi? | Evet | Hayır |
| Kullanıcı şifre girer mi? | Hayır | Evet |
| SAP çalışan kontrolü yapılır mı? | Evet | Hayır |
| Son ekran | `/chat` | Admin dashboard |

---

## **10\. SuccessFactors Ekibinden Beklenen Değişiklikler**

SuccessFactors tarafında aşağıdaki yazılım güncellemeleri yapılmalıdır:

### **10.1 Normal Kullanıcı Chatbot Butonu**

SuccessFactors içinde normal çalışanlar için bir chatbot butonu, linki veya tile eklenmelidir.

Bu buton kullanıcıya şu şekilde görünebilir:

```
Siro HR Chatbot
```

Butona tıklandığında SuccessFactors şu işlemleri yapmalıdır:

1. Giriş yapan kullanıcının PERNR bilgisini almalıdır.  
2. Backend API’ye POST request göndermelidir.  
3. Backend’den dönen `redirect_url` değerini almalıdır.  
4. Kullanıcının tarayıcısını bu `redirect_url` adresine yönlendirmelidir.

POST request:

```
POST https://siro-chatbot-api.siro.energy/api/sf-login
Content-Type: application/json
```

Body:

```json
{
  "pernr": "<CURRENT_USER_PERNR>",
  "api_key": "<SUCCESSFACTORS_CHATBOT_API_KEY>"
}
```

### **10.2 Admin Chatbot Linki**

SuccessFactors içinde admin kullanıcılar için ayrı bir link veya tile eklenmelidir.

Bu link sadece admin yetkisine sahip kullanıcılara görünmelidir.

Admin linki:

```
https://siro-chatbot.siro.energy/admin-login
```

Bu link için backend’e POST request gönderilmesine gerek yoktur.

---

## **11\. Backend Tarafında Beklenen Endpoint’ler**

Chatbot backend tarafında SuccessFactors ile iletişim için aşağıdaki endpoint kullanılacaktır:

```
POST /api/sf-login
```

Bu endpoint’in tam production URL’i:

```
https://siro-chatbot-api.siro.energy/api/sf-login
```

Bu endpoint aşağıdaki bilgileri bekler:

```json
{
  "pernr": "30000228",
  "api_key": "********"
}
```

Başarılı response:

```json
{
  "redirect_url": "https://siro-chatbot-api.siro.energy/auth/callback?token=TEMPORARY_TOKEN",
  "expires_in_seconds": 90,
  "message": "Geçici giriş bağlantısı oluşturuldu."
}
```

SuccessFactors bu response içindeki `redirect_url` değerine kullanıcıyı yönlendirmelidir.

---

## **12\. Frontend Tarafında Beklenen Route’lar**

Chatbot frontend uygulamasında aşağıdaki route’lar kullanılacaktır:

```
/auth/callback
/chat
/admin-login
/admin
```

Normal kullanıcılar doğrudan `/chat` sayfasına gönderilmemelidir.

Normal kullanıcı girişinde backend callback tamamlandıktan sonra kullanıcı otomatik olarak frontend `/auth/callback` sayfasına yönlendirilir. Bu sayfa token’ı kaydeder ve kullanıcıyı `/chat` sayfasına alır.

Admin kullanıcılar ise doğrudan şu sayfaya gönderilir:

```
https://siro-chatbot.siro.energy/admin-login
```

---

## **13\. Önemli Güvenlik Notları**

1. Normal kullanıcıların PERNR bilgisi URL içinde açık şekilde gönderilmemelidir.  
2. PERNR bilgisi backend’e POST body içinde gönderilmelidir.  
3. API key URL içinde gönderilmemelidir.  
4. API key frontend uygulamasında tutulmamalıdır.  
5. API key sadece SuccessFactors sistemi ve chatbot backend’i arasında kullanılmalıdır.  
6. Normal kullanıcılar için oluşturulan geçici token kısa süreli ve tek kullanımlık olmalıdır.  
7. Production ortamında tüm URL’ler HTTPS olmalıdır.  
8. Admin giriş linki sadece yetkili kullanıcılara görünmelidir.  
9. Normal kullanıcılar admin giriş sayfasına yönlendirilmemelidir.  
10. Admin kullanıcılar normal kullanıcı SSO akışını kullanmak zorunda değildir.

---

## **14\. Örnek Production Değerleri**

Aşağıdaki değerler örnek production ortamı için kullanılabilir:

```
FRONTEND_API = https://siro-chatbot.siro.energy
BACKEND_API  = https://siro-chatbot-api.siro.energy
```

Normal kullanıcı SuccessFactors entegrasyon endpoint’i:

```
POST https://siro-chatbot-api.siro.energy/api/sf-login
```

Admin giriş URL’i:

```
https://siro-chatbot.siro.energy/admin-login
```

Frontend callback URL’i:

```
https://siro-chatbot.siro.energy/auth/callback
```

Chatbot kullanıcı ekranı:

```
https://siro-chatbot.siro.energy/chat
```

---

## **15\. Sonuç**

SuccessFactors tarafında iki ayrı giriş yöntemi tanımlanmalıdır.

Normal kullanıcılar için SuccessFactors, chatbot backend API’sine PERNR ve güvenli API key içeren bir POST request göndermelidir. Backend bu request sonucunda geçici bir giriş linki üretir ve SuccessFactors kullanıcıyı bu linke yönlendirir. Böylece çalışan kullanıcılar chatbot sistemine ayrıca şifre girmeden, SuccessFactors oturumları üzerinden giriş yapabilir.

Admin kullanıcılar için ise SuccessFactors tarafında ayrı bir admin linki tanımlanmalıdır. Bu link doğrudan chatbot frontend admin giriş sayfasına yönlendirmelidir:

```
https://siro-chatbot.siro.energy/admin-login
```

Bu yapı sayesinde normal kullanıcı ve admin kullanıcı girişleri birbirinden ayrılmış, güvenli ve yönetilebilir bir entegrasyon sağlanmış olur.

