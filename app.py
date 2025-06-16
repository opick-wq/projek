from flask import Flask, jsonify, request
import time
from prometheus_client import generate_latest, Counter, Histogram, Gauge
import random
from flask_cors import CORS


app = Flask(__name__)
CORS(app)  # Menambahkan dua spasi sebelum inline comment


# Inisialisasi metrik Prometheus
# Counter untuk menghitung total request
REQUESTS_TOTAL = Counter(
    'http_requests_total',
    'Total HTTP Requests',
    ['method', 'endpoint', 'status_code']
)

# Histogram untuk melacak durasi respons
REQUEST_DURATION_SECONDS = Histogram(
    'http_request_duration_seconds',
    'HTTP Request Duration in Seconds',
    ['method', 'endpoint']
)

# Gauge untuk melacak jumlah concurrent requests (opsional, bisa lebih kompleks)
IN_FLIGHT_REQUESTS = Gauge(
    'http_in_flight_requests',
    'Number of HTTP requests currently in flight'
)

# Contoh metrik aplikasi kustom (bisa Anda sesuaikan)
CUSTOM_GAUGE = Gauge(
    'app_custom_gauge',
    'Contoh Gauge Kustom Aplikasi'
)
CUSTOM_COUNTER = Counter(
    'app_custom_counter_total',
    'Contoh Counter Kustom Aplikasi'
)


@app.route('/')
def home():
    """
    Endpoint utama untuk testing.
    """
    return jsonify({"message": "Selamat datang di Flask REST API!"})


@app.route('/hello/<name>', methods=['GET'])
def hello(name):
    """
    Endpoint sapaan yang menerima nama.
    """
    with IN_FLIGHT_REQUESTS.track_inprogress():
        start_time = time.time()
        status_code = 200
        try:
            # Simulasi pekerjaan yang membutuhkan waktu
            sleep_time = random.uniform(0.05, 0.5)  # Menambahkan dua spasi sebelum inline comment
            time.sleep(sleep_time)
            message = f"Halo, {name}!"
            return jsonify({"message": message})
        except Exception as e:
            status_code = 500
            app.logger.error(f"Error di /hello/{name}: {e}")
            return jsonify({"error": "Internal Server Error"}), 500
        finally:
            duration = time.time() - start_time
            REQUEST_DURATION_SECONDS.labels(request.method, '/hello/<name>').observe(duration)
            REQUESTS_TOTAL.labels(request.method, '/hello/<name>', status_code).inc()
            # Contoh memperbarui metrik kustom
            CUSTOM_GAUGE.set(random.randint(1, 100))
            CUSTOM_COUNTER.inc()


@app.route('/status', methods=['GET'])
def status():
    """
    Endpoint untuk memeriksa status aplikasi.
    """
    with IN_FLIGHT_REQUESTS.track_inprogress():
        start_time = time.time()
        status_code = 200
        try:
            # Logika sederhana untuk status
            app_status = {"status": "ok", "version": "1.0.0"}
            return jsonify(app_status)
        except Exception as e:
            status_code = 500
            app.logger.error(f"Error di /status: {e}")
            return jsonify({"error": "Internal Server Error"}), 500
        finally:
            duration = time.time() - start_time
            REQUEST_DURATION_SECONDS.labels(request.method, '/status').observe(duration)
            REQUESTS_TOTAL.labels(request.method, '/status', status_code).inc()


@app.route('/metrics')
def metrics():
    """
    Endpoint untuk mengekspos metrik Prometheus.
    """
    return generate_latest(), 200, {'Content-Type': 'text/plain; version=0.0.4; charset=utf-8'}


# Memastikan ada 2 baris kosong sebelum blok ini
if __name__ == '__main__':
    # Pastikan aplikasi berjalan di port 5000, sesuai dengan konfigurasi Kubernetes
    app.run(debug=True, host='0.0.0.0', port=5000)
