pipeline {
    agent any

    environment {
        DOCKER_IMAGE_NAME = 'flask-api'
        DOCKER_IMAGE_TAG = "${env.BUILD_NUMBER}"
        K8S_NAMESPACE = "flask-api-dev"
        VENV_PATH = ".venv"
    }

    stages {
        stage('Linting') {
            steps {
                script {
                    echo 'Running Python linting...'
                    sh '''
                        python3 -m venv ${VENV_PATH}
                        . ${VENV_PATH}/bin/activate
                        pip install --upgrade pip
                        pip install flake8
                        flake8 --max-line-length=120 --exclude=${VENV_PATH} app.py || true
                    '''
                    echo 'Linting complete.'
                }
            }
        }

        stage('Testing') {
            steps {
                script {
                    echo 'Running Python tests...'
                    sh '''
                        python3 -m venv ${VENV_PATH}
                        . ${VENV_PATH}/bin/activate
                        pip install --upgrade pip
                        pip install pytest
                        mkdir -p reports
                        pytest --junitxml=reports/junit.xml || true
                    '''
                }
            }
            post {
                always {
                    junit 'reports/junit.xml'
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    echo "Building Docker image ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}..."
                    sh '''
                        eval $(minikube docker-env)
                        docker build -t ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG} .
                        docker tag ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG} ${DOCKER_IMAGE_NAME}:latest
                        eval $(minikube docker-env -u)
                    '''
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                script {
                    echo "Deploying ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG} to namespace ${K8S_NAMESPACE}..."
                    sh """
                        kubectl set image deployment/${DOCKER_IMAGE_NAME}-deployment \
                            ${DOCKER_IMAGE_NAME}-container=${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG} \
                            -n ${K8S_NAMESPACE}
                        kubectl apply -f kubernetes/flask-api-service.yaml -n ${K8S_NAMESPACE}
                        kubectl rollout status deployment/${DOCKER_IMAGE_NAME}-deployment \
                            -n ${K8S_NAMESPACE} --timeout=5m
                    """
                }
            }
        }

        stage('Post-Deployment Test') {
            steps {
                script {
                    echo "Running post-deployment tests..."
                    def ip = sh(script: 'minikube ip', returnStdout: true).trim()
                    def port = "30007"

                    echo "Testing / endpoint..."
                    def home = sh(script: "curl -s http://${ip}:${port}/", returnStdout: true).trim()
                    if (!home.contains("Selamat datang")) {
                        error "Home endpoint test failed: ${home}"
                    }

                    echo "Testing /status endpoint..."
                    def status = sh(script: "curl -s http://${ip}:${port}/status", returnStdout: true).trim()
                    if (!status.contains('"status": "ok"')) {
                        error "Status endpoint test failed: ${status}"
                    }

                    echo "Testing /metrics endpoint..."
                    def metrics = sh(script: "curl -s http://${ip}:${port}/metrics", returnStdout: true).trim()
                    if (!metrics.contains("http_requests_total")) {
                        error "Metrics endpoint test failed."
                    }

                    echo "All endpoint tests passed."
                }
            }
        }
    }

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
            deleteDir()
        }
    }
}
