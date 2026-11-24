pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    environment {
        DOCKERHUB_NAMESPACE = 'pavinb'
        BACKEND_IMAGE = "pavinb/shopeasy-backend"
        FRONTEND_IMAGE = "pavinb/shopeasy-frontend"
        K8S_NAMESPACE = 'shopeasy'
    }

    stages {
        stage('Checkout SCM') {
            steps {
                checkout scm
            }
        }

        stage('Test Backend') {
            steps {
                sh '''
                    docker run --rm \
                      -v "$WORKSPACE/app:/app" \
                      -w /app \
                      python:3.12-slim \
                      sh -c "pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt &&  pytest -q"
                '''
            }
        }

        stage('Build Docker Images') {
            steps {
                sh '''
                    docker build -t ${BACKEND_IMAGE}:${BUILD_NUMBER} ./app
                    docker build -t ${FRONTEND_IMAGE}:${BUILD_NUMBER} ./frontend
                '''
            }
        }

        stage('Docker Hub Login and Push') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'docker',
                    usernameVariable: 'DOCKER_USERNAME',
                    passwordVariable: 'DOCKER_PASSWORD'
                )]) {
                    sh '''
                        set +x
                        echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
                        docker push ${BACKEND_IMAGE}:${BUILD_NUMBER}
                        docker push ${FRONTEND_IMAGE}:${BUILD_NUMBER}
                        docker logout
                    '''
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                sh '''
                    kubectl apply -f k8s/namespace.yaml
                    kubectl apply -f k8s/
                    kubectl set image deployment/shopeasy-backend backend=${BACKEND_IMAGE}:${BUILD_NUMBER} -n ${K8S_NAMESPACE}
                    kubectl set image deployment/shopeasy-frontend frontend=${FRONTEND_IMAGE}:${BUILD_NUMBER} -n ${K8S_NAMESPACE}
                '''
            }
        }

        stage('Verify Rollout') {
            steps {
                sh '''
                    kubectl rollout status deployment/shopeasy-backend -n ${K8S_NAMESPACE} --timeout=5m
                    kubectl rollout status deployment/shopeasy-frontend -n ${K8S_NAMESPACE} --timeout=5m
                    kubectl get pods,services -n ${K8S_NAMESPACE}
                '''
            }
        }
    }

    post {
        always {
            sh 'docker image prune -f || true'
        }
    }
}