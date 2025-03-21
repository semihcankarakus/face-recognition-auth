# Yüz Tanıma ve Kimlik Doğrulama Sistemi

Bu proje, gerçek zamanlı yüz tanıma ve kullanıcı kaydı yapabilen bir web uygulamasıdır. Flask ve OpenCV kullanılarak geliştirilmiştir.

## Özellikler

- Gerçek zamanlı yüz tespiti ve tanıma
- Yeni kullanıcı kaydı
- WebSocket üzerinden video akışı
- Kayıtlı yüzlerin veritabanında saklanması
- Kullanıcı listesi görüntüleme

## Gereksinimler

```bash
flask==2.0.1
opencv-python==4.8.0.74
numpy==1.24.3
face-recognition==1.3.0
flask-socketio==5.1.1
pandas==2.0.2
python-engineio==4.2.1
python-socketio==5.4.0
cmake
dlib==19.24.0
```

## Kurulum

1. Projeyi klonlayın:
```bash
git clone https://github.com/KULLANICI_ADINIZ/REPO_ADINIZ.git
cd REPO_ADINIZ
```

2. Gerekli paketleri yükleyin:
```bash
pip install -r requirements.txt
```

3. Uygulamayı başlatın:
```bash
python app.py
```

4. Tarayıcınızda şu adresi açın:
```
http://localhost:5000
```

## Kullanım

1. Ana Sayfa:
   - Kamerayı başlatmak için "Başlat" butonuna tıklayın
   - Sistem otomatik olarak tanımlı yüzleri tespit edecek ve isimlerini gösterecektir

2. Yeni Kullanıcı Kaydı:
   - "Yeni Kullanıcı" sayfasına gidin
   - İsim girin
   - Yüzünüzü kameraya doğru konumlandırın
   - "Fotoğraf Çek" butonuna tıklayın

## Klasör Yapısı

```
project/
├── static/
├── templates/
│   ├── index.html
│   └── register.html
├── database/
│   ├── encodings/
│   └── users.csv
├── app.py
├── requirements.txt
└── README.md
```

## Güvenlik

- Uygulama, yüz tespiti için yüksek doğruluk oranına sahip face_recognition kütüphanesini kullanır
- Kayıtlı yüzler için tekrar kayıt engellenmiştir
- WebSocket bağlantıları güvenli bir şekilde yönetilir

## Katkıda Bulunma

1. Bu projeyi fork edin
2. Yeni bir branch oluşturun (`git checkout -b feature/yeniOzellik`)
3. Değişikliklerinizi commit edin (`git commit -am 'Yeni özellik: Açıklama'`)
4. Branch'inizi push edin (`git push origin feature/yeniOzellik`)
5. Pull Request oluşturun

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Daha fazla bilgi için `LICENSE` dosyasına bakın. 