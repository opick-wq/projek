from flask import Flask, jsonify, request, render_template
import time
from prometheus_client import generate_latest, Counter, Histogram, Gauge
import random
from flask_cors import CORS

# Inisialisasi aplikasi Flask
app = Flask(__name__)
CORS(app)

# --- Definisi Metrik Prometheus ---

# COUNTER: Menghitung total permintaan HTTP yang masuk.
# Labelnya adalah method (GET, POST), endpoint (misal, '/hello/<name>'),
# dan status_code (misal, '200', '404', '500').
REQUESTS_TOTAL = Counter(
    'http_requests_total',
    'Total HTTP Requests',
    ['method', 'endpoint', 'status_code']
)

# HISTOGRAM: Mengukur durasi (latensi) dari permintaan HTTP.
REQUEST_DURATION_SECONDS = Histogram(
    'http_request_duration_seconds',
    'HTTP Request Duration in Seconds',
    ['method', 'endpoint']
)

# GAUGE: Mengukur jumlah permintaan yang sedang diproses (in-flight).
# Nilainya akan naik saat permintaan masuk dan turun saat selesai.
IN_FLIGHT_REQUESTS = Gauge(
    'http_in_flight_requests',
    'Number of HTTP requests currently in flight'
)

# Contoh metrik kustom (tidak terkait langsung dengan permintaan)
CUSTOM_GAUGE = Gauge(
    'app_custom_gauge',
    'Contoh Gauge Kustom Aplikasi'
)
CUSTOM_COUNTER = Counter(
    'app_custom_counter_total',
    'Contoh Counter Kustom Aplikasi'
)


# --- Hooks Middleware ---


@app.before_request
def before_request_hook():
    """
    Hook yang dijalankan sebelum setiap request diproses.
    Fungsi ini digunakan untuk mencatat waktu mulai dan menaikkan gauge in-flight.
    """
    request.start_time = time.time()
    IN_FLIGHT_REQUESTS.inc()


@app.after_request
def after_request_hook(response):
    """
    Hook yang dijalankan setelah setiap request selesai diproses, sebelum dikirim ke klien.
    Ini adalah tempat terpusat untuk mencatat metrik karena fungsi ini akan selalu
    dijalankan untuk SEMUA respons, termasuk yang berasal dari error handler (404, 500).
    """
    # Hitung durasi request
    duration = time.time() - request.start_time

    # Dapatkan nama endpoint yang terdaftar di Flask (misal: '/hello/<name>')
    # Jika endpoint tidak cocok (misal, 404), gunakan path URL mentah.
    endpoint_label = request.path
    if request.url_rule:
        endpoint_label = request.url_rule.rule

    # Dapatkan status code dari objek 'response' yang diberikan oleh Flask.
    # Ini akan secara dinamis berisi 200, 404, 500, dll.
    status_code_str = str(response.status_code)

    # Catat metrik durasi untuk endpoint ini
    REQUEST_DURATION_SECONDS.labels(method=request.method, endpoint=endpoint_label).observe(duration)

    # INILAH BAGIAN KUNCINYA:
    # Naikkan (increment) counter untuk total request dengan label yang dinamis.
    # Baik itu respons sukses (200) atau error (404/500), 'status_code_str' akan berisi
    # nilai yang benar, dan metrik yang sesuai akan bertambah.
    REQUESTS_TOTAL.labels(method=request.method, endpoint=endpoint_label, status_code=status_code_str).inc()

    # Turunkan gauge untuk in-flight requests karena request ini sudah selesai.
    IN_FLIGHT_REQUESTS.dec()

    return response


# --- Error Handlers ---


@app.errorhandler(500)
def internal_error(error):
    """
    Menangani error internal server (kode 500).
    Flask akan memanggil 'after_request_hook' setelah fungsi ini selesai,
    sehingga metrik untuk status 500 akan tercatat secara otomatis.
    """
    app.logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal Server Error"}), 500


@app.errorhandler(404)
def not_found_error(error):
    """
    Menangani error 'Not Found' (kode 404).
    Flask akan memanggil 'after_request_hook' setelah fungsi ini selesai,
    sehingga metrik untuk status 404 akan tercatat secara otomatis.
    """
    app.logger.warning(f"Not found error for path: {request.path}")
    return jsonify({"error": "Not Found"}), 404


# --- Endpoints Aplikasi ---


@app.route('/')
def home():
    """Endpoint halaman utama."""
    return render_template('index.html')


@app.route('/hello/<name>', methods=['GET'])
def hello(name):
    """Endpoint sapaan yang menerima nama."""
    if name.lower() == "slow":
        sleep_time = 5  # Tidur selama 5 detik untuk simulasi
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
    """Endpoint untuk memeriksa status aplikasi."""
    app_status = {"status": "ok", "version": "1.0.0"}
    return jsonify(app_status)


@app.route('/error', methods=['GET'])
def trigger_error():
    """Endpoint untuk sengaja memicu error 500."""
    # Ini akan menyebabkan TypeError, yang akan ditangani oleh @app.errorhandler(500)
    result = 1 / 0 # noqa: F841
    return "This will not be returned"


@app.route('/metrics')
def metrics():
    """Endpoint untuk mengekspos metrik Prometheus."""
    return generate_latest(), 200, {'Content-Type': 'text/plain; version=0.0.4; charset=utf-8'}


if __name__ == '__main__':
    # Pastikan debug=False di produksi agar error handler aplikasi yang digunakan.
    app.run(debug=False, host='0.0.0.0', port=5000)
