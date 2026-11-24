# ShopEasy – Intermediate DevOps E-Commerce Project

A learning/demo e-commerce application with a Flask API, PostgreSQL database, static frontend served by Nginx, Docker Compose, Jenkins CI/CD, and Kubernetes manifests.

> This is an educational starter project, not a production commerce system. Checkout creates a demo order only; it does not process payments or store payment-card data.

## Architecture

Browser -> Nginx frontend -> `/api/*` reverse proxy -> Flask API -> PostgreSQL

Jenkins checks out Git, runs backend tests, builds frontend/backend images, pushes versioned images to Docker Hub, applies Kubernetes manifests, updates deployments, and waits for rollout.

## Prerequisites

- Git
- Docker Engine/Desktop and Docker Compose
- Python 3.12 (optional for running tests locally)
- Jenkins with Docker CLI/daemon access
- Docker Hub account and a Jenkins username/password credential
- Minikube (or another Kubernetes cluster), `kubectl`
- Jenkins agent configured with access to the target cluster (`kubectl` context already configured)

## 1. Run locally

```bash
docker compose up --build
```

Open http://localhost:8080

The database is seeded with sample products on first startup. Add products to the cart and place a demo order. PostgreSQL data is persisted in the `postgres_data` Docker volume.

Stop:

```bash
docker compose down
```

Remove local database data too (destructive):

```bash
docker compose down -v
```

## 2. Run backend tests

```bash
cd backend
python -m pip install -r requirements.txt -r requirements-dev.txt
pytest -q
```

## 3. Push to GitHub

Create a repository and push the contents of this folder to its root:

```bash
git init
git add .
git commit -m "Initial ShopEasy DevOps project"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

## 4. Configure Jenkins

1. Install/enable Pipeline, Git and Credentials plugins.
2. Configure a Jenkins agent that can run Docker commands and `kubectl`.
3. In **Manage Jenkins -> Credentials**, create a Username with password credential:
   - ID: `docker`
   - Username: your Docker Hub username
   - Password: a Docker Hub access token (recommended), not your account password.
4. Set the Jenkins job as **Pipeline** -> **Pipeline script from SCM**, point it to the Git repository, branch `main`, script path `Jenkinsfile`.
5. The Jenkins agent must already have a valid kubeconfig and permission to deploy to the cluster. Do not put kubeconfig contents in Git.

Update the `DOCKERHUB_NAMESPACE` value near the top of `Jenkinsfile` to your Docker Hub username or organization.

## 5. Deploy to Minikube manually (optional)

Start Minikube:

```bash
minikube start
```

Build images and make them available to Minikube. One option is to build directly into Minikube's Docker daemon:

```bash
eval $(minikube docker-env)
docker build -t YOUR_DOCKERHUB_USERNAME/shopeasy-backend:dev ./backend
docker build -t YOUR_DOCKERHUB_USERNAME/shopeasy-frontend:dev ./frontend
```

Edit `k8s/backend-deployment.yaml` and `k8s/frontend-deployment.yaml` to use those image names and set `imagePullPolicy: IfNotPresent` for this local-only approach. Then:

```bash
kubectl apply -f k8s/
kubectl get pods,svc,pvc
minikube service shopeasy-frontend --url
```

For a remote Docker Hub deployment, push the images first and use `imagePullPolicy: Always` (or a suitable immutable tag).

## 6. Kubernetes credentials and secrets

`k8s/postgres-secret.yaml` contains demo-only credentials for local learning. Change them before using this project anywhere shared. For real deployments, create Kubernetes Secrets securely (or use an external secret manager) and never commit production credentials to Git.

The PostgreSQL PVC requires a StorageClass that can provision storage. Minikube normally provides a default StorageClass.

## 7. Useful checks

```bash
kubectl get deployments,pods,services
kubectl rollout status deployment/shopeasy-backend
kubectl rollout status deployment/shopeasy-frontend
kubectl logs deployment/shopeasy-backend
kubectl get pvc
```

Open the website through the Minikube service URL. The frontend Service is NodePort 30080.

## Notes / next improvements

- Add user authentication and authorization.
- Add database migrations (Alembic/Flask-Migrate) instead of `create_all`.
- Add image scanning (Trivy), code quality (SonarQube), and monitoring (Prometheus/Grafana).
- Add TLS/Ingress, resource limits tuned to load, backups, and managed secrets before production.
- Use immutable image tags and a controlled rollback strategy.
