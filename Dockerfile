# Temel imaj olarak Python kullanıyoruz
FROM python:3.9

# Çalışma dizinini ayarla
WORKDIR /app

# Gereksinimleri kopyala ve yükle
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Uygulama dosyalarını kopyala
COPY . .

# Uygulamanı çalıştır
CMD ["python", "app.py"]
