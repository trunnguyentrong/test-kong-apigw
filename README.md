# Kong API Gateway Demo

Demo project sử dụng Kong API Gateway với 2 microservices backend (foo và bar) trên Kubernetes.

## Kiến trúc

```
Client → Kong API Gateway (Port 31965)
         ├─ /foo → Foo Microservice (FastAPI)
         └─ /bar → Bar Microservice (FastAPI)
         ↓
    PostgreSQL Database
```

## Thành phần

- **Kong Gateway 3.4**: API Gateway với database mode (PostgreSQL)
- **Foo Microservice**: FastAPI service trả về JSON message
- **Bar Microservice**: FastAPI service trả về JSON message
- **PostgreSQL 13**: Database lưu trữ config của Kong

## Yêu cầu

- Kubernetes cluster (k3s, minikube, hoặc bất kỳ K8s cluster nào)
- kubectl đã được cấu hình
- Docker (nếu muốn build images mới)
- Docker Hub account (nếu muốn push images)

## Cài đặt và chạy

### 1. Deploy toàn bộ stack lên Kubernetes

```bash
kubectl apply -f k8s/kong.yaml
```

Lệnh này sẽ tạo:
- Namespace `test-kong`
- PostgreSQL database
- Kong migration job (bootstrap database)
- Kong Gateway (2 replicas)
- Foo và Bar microservices
- Kong configuration job (tạo services và routes)

### 2. Kiểm tra trạng thái

```bash
# Kiểm tra tất cả pods
kubectl get pods -n test-kong

# Đợi cho đến khi tất cả pods ở trạng thái Running/Completed
# foo-deployment-xxx: Running
# bar-deployment-xxx: Running
# kong-xxx: Running
# postgres-xxx: Running
# kong-migration-xxx: Completed
# kong-configure-xxx: Completed
```

### 3. Lấy thông tin Kong Proxy

```bash
# Xem service details
kubectl get svc -n test-kong kong-proxy

# Output mẫu:
# NAME         TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)
# kong-proxy   NodePort   10.43.163.15   <none>        80:31965/TCP,443:31753/TCP

# Lấy IP của node
kubectl get nodes -o wide
```

### 4. Test APIs

#### Cách 1: Qua NodePort (từ bên ngoài cluster)

```bash
# Thay <NODE_IP> bằng IP của Kubernetes node
# Thay <NODE_PORT> bằng port được map (ví dụ: 31965)

curl http://<NODE_IP>:<NODE_PORT>/foo
# Response: {"msg":"Hello from the foo microservice"}

curl http://<NODE_IP>:<NODE_PORT>/bar
# Response: {"msg":"Hello from the bar microservice"}

# Ví dụ thực tế:
curl http://103.143.206.222:31965/foo
curl http://103.143.206.222:31965/bar
```

#### Cách 2: Port-forward (từ local machine)

```bash
# Terminal 1: Port-forward Kong proxy
kubectl port-forward -n test-kong svc/kong-proxy 8080:80

# Terminal 2: Test APIs
curl http://localhost:8080/foo
curl http://localhost:8080/bar
```

#### Cách 3: Test bằng browser

Mở browser và truy cập:
- `http://<NODE_IP>:<NODE_PORT>/foo`
- `http://<NODE_IP>:<NODE_PORT>/bar`

## Quản lý Kong

### Kong Admin API

Kong Admin API cho phép quản lý services, routes, plugins, etc.

```bash
# Port-forward Kong Admin
kubectl port-forward -n test-kong svc/kong-admin 8001:8001

# Xem danh sách services
curl http://localhost:8001/services

# Xem danh sách routes
curl http://localhost:8001/routes

# Xem Kong status
curl http://localhost:8001/status

# Thêm plugin (ví dụ: rate limiting)
curl -X POST http://localhost:8001/services/foo-service/plugins \
  --data "name=rate-limiting" \
  --data "config.minute=100"
```

## Build và Deploy Images mới

### 1. Build Docker images

```bash
# Build foo service
docker build -t <your-dockerhub>/foo-microservice:latest -f foo/Dockerfile foo/

# Build bar service
docker build -t <your-dockerhub>/bar-microservice:latest -f bar/Dockerfile bar/
```

### 2. Push lên Docker Hub

```bash
# Login Docker Hub
docker login --username <your-username>

# Push images
docker push <your-dockerhub>/foo-microservice:latest
docker push <your-dockerhub>/bar-microservice:latest
```

### 3. Cập nhật Kubernetes manifests

Sửa file `k8s/kong.yaml`, thay đổi image names:

```yaml
# Foo deployment
image: <your-dockerhub>/foo-microservice:latest

# Bar deployment
image: <your-dockerhub>/bar-microservice:latest
```

### 4. Redeploy

```bash
# Apply changes
kubectl apply -f k8s/kong.yaml

# Hoặc restart deployments
kubectl rollout restart deployment/foo-deployment -n test-kong
kubectl rollout restart deployment/bar-deployment -n test-kong
```

## Troubleshooting

### Kiểm tra logs

```bash
# Kong logs
kubectl logs -n test-kong -l app=kong --tail=100

# Foo service logs
kubectl logs -n test-kong -l app=foo --tail=50

# Bar service logs
kubectl logs -n test-kong -l app=bar --tail=50

# PostgreSQL logs
kubectl logs -n test-kong -l app=postgres --tail=50

# Kong configuration job logs
kubectl logs -n test-kong kong-configure-xxx
```

### Lỗi thường gặp

#### 1. Pods không start được

```bash
# Kiểm tra pod events
kubectl describe pod -n test-kong <pod-name>

# Kiểm tra image pull errors
kubectl get events -n test-kong --sort-by='.lastTimestamp'
```

#### 2. Kong trả về 404

```bash
# Kiểm tra Kong routes đã được tạo chưa
kubectl port-forward -n test-kong svc/kong-admin 8001:8001
curl http://localhost:8001/routes

# Nếu chưa có routes, chạy lại kong-configure job
kubectl delete job -n test-kong kong-configure
kubectl apply -f k8s/kong.yaml
```

#### 3. Database connection errors

```bash
# Kiểm tra PostgreSQL
kubectl exec -n test-kong deployment/postgres -- psql -U kong -d kong -c "\dt"

# Restart Kong nếu cần
kubectl rollout restart deployment/kong -n test-kong
```

## Dọn dẹp

Xóa toàn bộ resources:

```bash
kubectl delete namespace test-kong
```

## Cấu trúc thư mục

```
test-kong-apigw/
├── foo/
│   ├── foo.py              # FastAPI foo service
│   ├── Dockerfile          # Dockerfile cho foo
│   └── requirements.txt    # Python dependencies
├── bar/
│   ├── bar.py              # FastAPI bar service
│   ├── Dockerfile          # Dockerfile cho bar
│   └── requirements.txt    # Python dependencies
├── k8s/
│   └── kong.yaml           # Kubernetes manifests
└── README.md               # File này
```

## Tính năng Kong có thể mở rộng

Kong hỗ trợ nhiều plugins và tính năng:

- **Authentication**: Key Auth, OAuth 2.0, JWT, Basic Auth
- **Security**: IP Restriction, ACL, CORS, Bot Detection
- **Traffic Control**: Rate Limiting, Request Size Limiting
- **Analytics**: Logging, Monitoring, Request Transformer
- **Transformations**: Request/Response Transformer, Correlation ID

Xem thêm: https://docs.konghq.com/hub/

## Tech Stack

- **Kong**: 3.4
- **PostgreSQL**: 13
- **Python**: 3 (Alpine)
- **FastAPI**: 0.104.1
- **Uvicorn**: 0.24.0
- **Kubernetes**: v1.33+

## License

MIT

## Contributors

- Initial setup by trungnt1205
- Fixed and enhanced by hungdo26
