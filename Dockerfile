# Dockerfile
# Gunakan base image Python yang ringan
FROM python:3.9-slim-buster

# Atur direktori kerja di dalam container
WORKDIR /app

# Salin file requirements.txt dan instal dependensi
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Salin seluruh kode aplikasi
COPY . .

# Beri tahu Docker bahwa container akan mendengarkan di port 5000
EXPOSE 5000

# Perintah untuk menjalankan aplikasi Flask saat container dimulai
# Gunakan Gunicorn untuk produksi karena Flask's development server tidak cocok untuk produksi
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
