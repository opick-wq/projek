from flask import Flask, jsonify, request, render_template
import time
from prometheus_client import generate_latest, Counter, Histogram, Gauge
import random
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Inisialisasi metrik Prometheus
REQUESTS_TOTAL = Counter(
    'http_requests_total',
    'Total HTTP Requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION_SECONDS = Histogram(
    'http_request_duration_seconds',
    'HTTP Request Duration in Seconds',
    ['method', 'endpoint']
)

# --- METRIK IN-FLIGHT ---
# Gauge ini akan naik saat request masuk dan turun saat selesai.
IN_FLIGHT_REQUESTS = Gauge(
    'http_in_flight_requests',
    'Number of HTTP requests currently in flight'
)

CUSTOM_GAUGE = Gauge(
    'app_custom_gauge',
    'Contoh Gauge Kustom Aplikasi'
)
CUSTOM_COUNTER = Counter(
    'app_custom_counter_total',
    'Contoh Counter Kustom Aplikasi'
)

@app.before_request
def before_request_hook():
    """
    Hook yang dijalankan sebelum setiap request.
    """
    # Catat waktu mulai request
    request.start_time = time.time()
    # [FIX] Naikkan (increment) counter untuk in-flight requests.
    # Baris ini sebelumnya di-nonaktifkan (commented out).
    IN_FLIGHT_REQUESTS.inc()

@app.after_request
def after_request_hook(response):
    """
    Hook yang dijalankan setelah setiap request, sebelum response dikirim.
    """
    # Dapatkan waktu mulai dari objek request
    duration = time.time() - request.start_time
    
    # Dapatkan nama endpoint yang sebenarnya atau path jika tidak diketahui
    endpoint_label = request.path 
    if request.url_rule:
        endpoint_label = request.url_rule.rule

    # Pastikan status_code adalah string untuk label Prometheus
    status_code_str = str(response.status_code)

    # Catat metrik durasi
    REQUEST_DURATION_SECONDS.labels(request.method, endpoint_label).observe(duration)

    # Catat total request dengan status_code yang sebenarnya
    REQUESTS_TOTAL.labels(request.method, endpoint_label, status_code_str).inc()

    # [FIX] Turunkan (decrement) counter untuk in-flight requests.
    # Baris ini sebelumnya di-nonaktifkan (commented out).
    IN_FLIGHT_REQUESTS.dec()

    return response

# Error handler untuk menangkap 500 internal server error
@app.errorhandler(500)
def internal_error(error):
    # after_request akan tetap dipanggil, jadi metrik akan tercatat di sana.
    app.logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal Server Error"}), 500

# Error handler untuk menangkap 404 Not Found
@app.errorhandler(404)
def not_found_error(error):
    # after_request akan tetap dipanggil, jadi metrik akan tercatat di sana.
    app.logger.error(f"Not found error: {request.path}")
    return jsonify({"error": "Not Found"}), 404


@app.route('/')
def home():
    """
    Endpoint utama untuk testing.
    """
    return render_template('index.html')


@app.route('/hello/<name>', methods=['GET'])
def hello(name):
    """
    Endpoint sapaan yang menerima nama.
    """
    # Untuk simulasi, jika nama adalah 'slow', buat request berjalan lama
    if name.lower() == "slow":
        sleep_time = 20  # Tidur selama 20 detik
    else:
        sleep_time = random.uniform(0.05, 0.5)

    time.sleep(sleep_time)
    message = f"Halo, {name}!"
    
    # Contoh memperbarui metrik kustom
    CUSTOM_GAUGE.set(random.randint(1, 100))
    CUSTOM_COUNTER.inc()
    
    return jsonify({"message": message})


@app.route('/status', methods=['GET'])
def status():
    """
    Endpoint untuk memeriksa status aplikasi.
    """
    app_status = {"status": "ok", "version": "1.0.0"}
    return jsonify(app_status)


@app.route('/metrics')
def metrics():
    """
    Endpoint untuk mengekspos metrik Prometheus.
    """
    return generate_latest(), 200, {'Content-Type': 'text/plain; version=0.0.4; charset=utf-8'}


if __name__ == '__main__':
    # Pastikan debug=False saat menjalankan di lingkungan produksi
    # agar tidak menangani exception secara internal.
    app.run(debug=False, host='0.0.0.0', port=5000)
