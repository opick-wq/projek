pipeline {
    agent any

    environment {
        IMAGE_NAME = "flask-api"
        IMAGE_TAG = "latest"
        REGISTRY = "" // isi jika pakai docker registry, contoh: docker.io/username
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup Python & Install Dependencies') {
            steps {
                sh '''
                python3 -m venv .venv
                . .venv/bin/activate
                pip install --upgrade pip
                pip install -r requirements.txt
                '''
            }
        }

        stage('Linting') {
            steps {
                sh '''
                . .venv/bin/activate
                flake8 --max-line-length=120 --exclude=.venv .
                '''
            }
        }

        stage('Testing') {
            steps {
                sh '''
                . .venv/bin/activate
                pytest --junitxml=reports/junit.xml
                '''
            }
            post {
                always {
                    junit 'reports/junit.xml'
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
                '''
            }
        }

        // Optional, kalau kamu mau push ke registry:
        /*
        stage('Push Docker Image') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'docker-hub', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh '''
                    echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                    docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
                    docker push ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
                    '''
                }
            }
        }
        */

        stage('Deploy to Kubernetes') {
            steps {
                sh '''
                kubectl set image deployment/${IMAGE_NAME}-deployment ${IMAGE_NAME}-container=${IMAGE_NAME}:${IMAGE_TAG} -n flask-api-dev
                '''
            }
        }
    }

    post {
        failure {
            echo "Pipeline gagal, cek log untuk detailnya."
        }
        success {
            echo "Pipeline selesai sukses!"
        }
    }
}
