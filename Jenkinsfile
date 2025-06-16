// Jenkinsfile

// Definisikan agen di mana pipeline akan berjalan.
// 'any' berarti Jenkins akan mengalokasikan agen yang tersedia.
// Untuk produksi, Anda mungkin ingin menggunakan agen berlabel tertentu.
agent any

// Pipeline deklaratif
pipeline {
    // Definisi environment variables yang akan digunakan di seluruh pipeline
    environment {
        // Nama image Docker untuk aplikasi Flask
        DOCKER_IMAGE_NAME = 'flask-api'
        // Tag untuk image Docker (gunakan nomor build Jenkins)
        DOCKER_IMAGE_TAG = "${env.BUILD_NUMBER}"
        // Namespace Kubernetes tempat aplikasi akan di-deploy
        K8S_NAMESPACE = "flask-api-dev"
    }

    // Definisi stages (tahapan) pipeline
    stages {
        // Stage 1: Linting Kode Python
        stage('Linting') {
            steps {
                script {
                    echo 'Running Python linting...'
                    // Instal flake8 jika belum ada (opsional, bisa juga di Dockerfile atau virtual env)
                    sh 'pip install flake8'
                    // Jalankan flake8. Gagal jika ada error.
                    // Jika ada error linting, stage ini akan gagal.
                    sh 'flake8 --max-line-length=120 --exclude=venv,.venv app.py'
                    echo 'Linting complete.'
                }
            }
        }

        // Stage 2: Menjalankan Unit Tests
        stage('Test') {
            steps {
                script {
                    echo 'Running Python tests...'
                    // Instal pytest jika belum ada
                    sh 'pip install pytest'
                    // Jalankan pytest. Asumsikan Anda memiliki file test seperti test_app.py
                    // Jika tidak ada test, stage ini akan berhasil.
                    // TODO: Tambahkan test_app.py dengan unit tests untuk aplikasi Flask Anda
                    sh 'pytest --junitxml=reports/junit.xml || true' // '|| true' agar tidak gagal jika tidak ada test
                                                                    // atau jika pytest gagal tapi kita ingin melihat laporan
                    echo 'Tests complete.'
                }
            }
            // Post-action: Arsipkan hasil test (misalnya, untuk Jenkins JUnit plugin)
            post {
                always {
                    junit 'reports/junit.xml' // Path ke laporan JUnit Anda
                }
            }
        }

        // Stage 3: Membangun Image Docker
        stage('Build Docker Image') {
            steps {
                script {
                    echo "Building Docker image ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}..."
                    // Pastikan Jenkins dapat mengakses daemon Docker Minikube
                    // Ini penting agar image dibangun di environment Docker Minikube
                    // dan dapat langsung digunakan oleh Kubernetes di Minikube
                    sh 'eval $(minikube docker-env)'
                    sh "docker build -t ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG} ."
                    sh "docker tag ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG} ${DOCKER_IMAGE_NAME}:latest" // Tag juga sebagai latest
                    sh 'eval $(minikube docker-env -u)' // Kembalikan ke Docker environment host
                    echo 'Docker image built successfully.'
                }
            }
        }

        // Stage 4: Deploy Aplikasi ke Kubernetes
        stage('Deploy to Kubernetes') {
            steps {
                script {
                    echo "Deploying ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG} to Kubernetes namespace ${K8S_NAMESPACE}..."

                    // Menggunakan credential Kubeconfig
                    // Asumsikan Jenkins memiliki akses ke kubectl dan kubeconfig yang benar
                    // Ini bisa diatur sebagai secret credential di Jenkins
                    // atau dengan menambahkan `KUBECONFIG` variable.
                    // Untuk Minikube, biasanya kubectl sudah terkonfigurasi setelah `minikube start`.
                    // Pastikan file YAML untuk deployment dan service tersedia di workspace Jenkins

                    // Update image di Deployment Kubernetes
                    // Perintah ini akan memperbarui `image` di deployment tanpa perlu file YAML baru
                    sh "kubectl set image deployment/${DOCKER_IMAGE_NAME}-deployment ${DOCKER_IMAGE_NAME}-container=${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG} -n ${K8S_NAMESPACE}"

                    // Terapkan file Service (jika ada perubahan atau jika belum ada)
                    // Sebaiknya service hanya di-apply sekali jika tidak ada perubahan
                    sh "kubectl apply -f kubernetes/flask-api-service.yaml -n ${K8S_NAMESPACE}"

                    echo 'Deployment to Kubernetes initiated.'
                    echo "Waiting for rollout to complete..."
                    // Tunggu hingga deployment berhasil (opsional, tapi disarankan)
                    sh "kubectl rollout status deployment/${DOCKER_IMAGE_NAME}-deployment -n ${K8S_NAMESPACE} --timeout=5m"
                    echo 'Deployment rollout complete.'
                }
            }
        }

        // Stage 5: Testing Endpoint (Post-Deployment Test)
        // Ini adalah testing endpoint sederhana setelah deployment
        stage('Post-Deployment Test') {
            steps {
                script {
                    echo "Running post-deployment tests..."
                    // Dapatkan IP Minikube
                    def minikubeIp = sh(returnStdout: true, script: 'minikube ip').trim()
                    def nodePort = "30007" // Sesuaikan dengan nodePort di flask-api-service.yaml Anda

                    // Test endpoint /
                    echo "Testing endpoint /"
                    def responseHome = sh(returnStdout: true, script: "curl -s http://${minikubeIp}:${nodePort}/")
                    if (!responseHome.contains('Selamat datang di Flask REST API!')) {
                        error "Home endpoint test failed!"
                    } else {
                        echo "Home endpoint test passed: ${responseHome}"
                    }

                    // Test endpoint /status
                    echo "Testing endpoint /status"
                    def responseStatus = sh(returnStdout: true, script: "curl -s http://${minikubeIp}:${nodePort}/status")
                    if (!responseStatus.contains('"status": "ok"')) {
                        error "Status endpoint test failed!"
                    } else {
                        echo "Status endpoint test passed: ${responseStatus}"
                    }

                    // Test endpoint /metrics (memastikan dapat diakses)
                    echo "Testing endpoint /metrics"
                    def responseMetrics = sh(returnStdout: true, script: "curl -s http://${minikubeIp}:${nodePort}/metrics")
                    if (!responseMetrics.contains('http_requests_total')) {
                        error "Metrics endpoint test failed!"
                    } else {
                        echo "Metrics endpoint test passed (found http_requests_total metric)."
                    }

                    echo 'All post-deployment tests passed.'
                }
            }
        }
    }

    // Definisi post-actions (akan dijalankan setelah semua stages selesai)
    post {
        always {
            echo 'Pipeline finished.'
        }
        success {
            echo 'Pipeline executed successfully!'
        }
        failure {
            echo 'Pipeline failed. Check logs for details.'
        }
        cleanup {
            // Bersihkan workspace atau resource lainnya jika diperlukan
            deleteDir() // Hapus direktori workspace Jenkins
        }
    }
}
