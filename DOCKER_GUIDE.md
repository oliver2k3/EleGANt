# Docker Deployment Guide - EleGANt Makeup Transfer

## 📋 Tổng Quan

Dự án hỗ trợ Docker để triển khai dễ dàng với 2 services riêng biệt:
- **API Service** (Port 8000): FastAPI backend
- **Web UI Service** (Port 8501): Streamlit frontend

## 🚀 Bắt Đầu Nhanh

### Chạy Tất Cả Services

```bash
# Build và chạy cả API và Web UI
docker-compose up -d

# Xem logs
docker-compose logs -f

# Dừng tất cả services
docker-compose down
```

### Chạy Riêng Lẻ

#### Chỉ API Service
```bash
docker-compose up -d elegant-api

# Truy cập: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

#### Chỉ Web UI Service
```bash
docker-compose up -d elegant-web

# Truy cập: http://localhost:8501
```

## 🏗️ Build và Deploy

### Build Images

```bash
# Build tất cả services
docker-compose build

# Build riêng từng service
docker-compose build elegant-api
docker-compose build elegant-web

# Build với no cache
docker-compose build --no-cache
```

### Production Deployment

```bash
# Chạy ở chế độ production (detached)
docker-compose up -d

# Scale services (nếu cần)
docker-compose up -d --scale elegant-api=2
```

## 📦 Services

### 1. elegant-api
- **Container**: `elegant-makeup-api`
- **Port**: 8000
- **Endpoints**:
  - `GET /`: Health check
  - `GET /health`: Detailed health info
  - `POST /transfer`: Makeup transfer với cấu hình thủ công
  - `POST /transfer-preset`: Makeup transfer với preset
  - `GET /presets`: Liệt kê tất cả presets
  - `GET /delete/{session_id}`: Xóa session folder

### 2. elegant-web
- **Container**: `elegant-makeup-web`
- **Port**: 8501
- **Interface**: Streamlit web UI
- **Tính năng**: 
  - Upload ảnh gốc và tham khảo
  - Điều chỉnh độ đậm makeup
  - Lưu/tải presets
  - Xử lý batch nhiều ảnh

## 📁 Volumes

Các thư mục được mount để dữ liệu persistent:

```yaml
volumes:
  - ./result:/app/result      # Kết quả xử lý
  - ./ckpts:/app/ckpts        # Model checkpoints
  - ./presets:/app/presets    # Preset configurations
  - ./assets:/app/assets      # Assets và examples
```

## 🔧 Configuration

### Environment Variables

#### API Service
```bash
PYTHONUNBUFFERED=1
```

#### Web UI Service
```bash
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
PYTHONUNBUFFERED=1
```

### Custom Ports

Để thay đổi ports, sửa file `docker-compose.yml`:

```yaml
services:
  elegant-api:
    ports:
      - "3000:8000"  # Chạy API trên port 3000
  
  elegant-web:
    ports:
      - "3001:8501"  # Chạy Web UI trên port 3001
```

## 🐛 Troubleshooting

### Kiểm Tra Logs

```bash
# Tất cả services
docker-compose logs -f

# Chỉ API
docker-compose logs -f elegant-api

# Chỉ Web UI
docker-compose logs -f elegant-web

# Logs của 100 dòng cuối
docker-compose logs --tail=100
```

### Kiểm Tra Health

```bash
# API health
curl http://localhost:8000/health

# Web UI health
curl http://localhost:8501/_stcore/health
```

### Restart Services

```bash
# Restart tất cả
docker-compose restart

# Restart riêng lẻ
docker-compose restart elegant-api
docker-compose restart elegant-web
```

### Xóa và Rebuild

```bash
# Dừng và xóa containers
docker-compose down

# Xóa cả volumes (cẩn thận - mất data!)
docker-compose down -v

# Xóa images
docker-compose down --rmi all

# Rebuild từ đầu
docker-compose build --no-cache
docker-compose up -d
```

## 🌐 Networking

Các services giao tiếp qua `elegant-network`:

```bash
# Xem network
docker network ls | grep elegant

# Inspect network
docker network inspect elegant_elegant-network
```

## 📊 Resource Management

### Giới Hạn Resources

Thêm vào `docker-compose.yml`:

```yaml
services:
  elegant-api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### Monitoring

```bash
# Xem resource usage
docker stats elegant-makeup-api elegant-makeup-web

# Xem processes
docker-compose top
```

## 🔒 Security

### Best Practices

1. **Không expose ports không cần thiết**
2. **Sử dụng secrets cho sensitive data**
3. **Regular update base images**
4. **Scan for vulnerabilities**

```bash
# Scan image
docker scan elegant-makeup-api
```

## 📝 Examples

### Development Mode

```bash
# Chạy với live reload
docker-compose up

# Code changes sẽ tự động reload (nhờ volumes mount)
```

### Production Mode

```bash
# Chạy detached
docker-compose up -d

# Monitor
docker-compose logs -f

# Update khi có changes
docker-compose build
docker-compose up -d
```

### Testing

```bash
# Test API
curl -X POST http://localhost:8000/transfer-preset \
  -H "Content-Type: application/json" \
  -d '{
    "source_images": ["/app/assets/images/examples/source.jpg"],
    "preset_path": "presets/Natural Look",
    "session_id": "test_001"
  }'

# Test Web UI
open http://localhost:8501
```

## 🚢 Docker Hub

### Repository Information

Images được publish tại Docker Hub:
- **API**: `oliver9889/elegant-makeup:api-latest`
- **Web UI**: `oliver9889/elegant-makeup:web-latest`

### Pull Images từ Docker Hub

```bash
# Pull cả 2 images
make pull

# Hoặc pull thủ công
docker pull oliver9889/elegant-makeup:api-latest
docker pull oliver9889/elegant-makeup:web-latest
```

### Push Images lên Docker Hub

#### Bước 1: Login vào Docker Hub

```bash
# Sử dụng Makefile
make login

# Hoặc dùng docker CLI
docker login
```

Nhập username: `oliver9889` và password/token của bạn.

#### Bước 2: Build Images

```bash
# Build tất cả services
make build
```

#### Bước 3: Push lên Docker Hub

```bash
# Push images với latest tag
make push

# Hoặc build và push trong 1 lệnh
make build-push
```

### Versioning

#### Push với Version Tag

```bash
# Tag và push với version cụ thể
make push-version VERSION=1.0.0

# Images sẽ được tag là:
# - oliver9889/elegant-makeup:api-1.0.0
# - oliver9889/elegant-makeup:web-1.0.0
```

#### Tag Manually

```bash
# Tag API image
docker tag oliver9889/elegant-makeup:api-latest oliver9889/elegant-makeup:api-1.0.0

# Tag Web image
docker tag oliver9889/elegant-makeup:web-latest oliver9889/elegant-makeup:web-1.0.0

# Push versioned images
docker push oliver9889/elegant-makeup:api-1.0.0
docker push oliver9889/elegant-makeup:web-1.0.0
```

### Sử Dụng Images từ Docker Hub

Cập nhật `docker-compose.yml` để chỉ pull images thay vì build:

```yaml
services:
  elegant-api:
    image: oliver9889/elegant-makeup:api-latest
    # Comment out build section
    # build:
    #   context: .
    #   dockerfile: Dockerfile
```

Sau đó chạy:

```bash
make pull
make up
```

### Best Practices

1. **Luôn tag version khi release**:
   ```bash
   make push-version VERSION=1.0.0
   ```

2. **Sử dụng semantic versioning**: v1.0.0, v1.1.0, v2.0.0

3. **Giữ `latest` tag cho development**

4. **Production nên dùng version cụ thể**:
   ```yaml
   image: oliver9889/elegant-makeup:api-1.0.0
   ```

### CI/CD Integration

#### GitHub Actions Example

```yaml
name: Build and Push to Docker Hub

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      
      - name: Build and Push
        run: |
          make build
          make push
          make push-version VERSION=${GITHUB_REF#refs/tags/v}
```

## 🚢 Docker Hub (Optional)

### Push to Registry

```bash
# Login vào Docker Hub
make login

# Build images
make build

# Push lên Docker Hub
make push

# Hoặc build và push cùng lúc
make build-push

# Push với version tag
make push-version VERSION=1.0.0
```

### Pull và Chạy từ Docker Hub

```bash
# Pull images từ Docker Hub
make pull

# Chạy services
make up
```

Hoặc trực tiếp:

```bash
docker-compose pull
docker-compose up -d
```

## 📚 Commands Reference

| Command | Description |
|---------|-------------|
| `docker-compose up` | Chạy tất cả services |
| `docker-compose up -d` | Chạy detached mode |
| `docker-compose down` | Dừng và xóa containers |
| `docker-compose build` | Build images |
| `docker-compose logs` | Xem logs |
| `docker-compose ps` | Liệt kê containers |
| `docker-compose restart` | Restart services |
| `docker-compose exec` | Chạy command trong container |

### Useful Commands

```bash
# Vào shell của container
docker-compose exec elegant-api bash
docker-compose exec elegant-web bash

# Chạy Python trong container
docker-compose exec elegant-api python

# Copy files
docker cp local_file.txt elegant-makeup-api:/app/
docker cp elegant-makeup-api:/app/result ./local_result

# View container info
docker-compose exec elegant-api env
```

## 🎯 Quick Start Checklist

- [ ] Cài Docker và Docker Compose
- [ ] Clone repository
- [ ] Download model checkpoint vào `ckpts/`
- [ ] Build images: `docker-compose build`
- [ ] Start services: `docker-compose up -d`
- [ ] Kiểm tra health: `curl http://localhost:8000/health`
- [ ] Truy cập Web UI: `http://localhost:8501`
- [ ] Test API: `http://localhost:8000/docs`

## 💡 Tips

1. **Development**: Mount toàn bộ source code để live reload
2. **Production**: Sử dụng specific image tags thay vì `latest`
3. **Performance**: Sử dụng multi-stage builds để giảm image size
4. **Data**: Backup thường xuyên các volumes
5. **Monitoring**: Cài đặt logging và monitoring tools

## 🔥 GPU Support (Optional)

Nếu có NVIDIA GPU, thêm vào docker-compose.yml:

```yaml
services:
  elegant-api:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

## 📖 Reverse Proxy với Nginx

Tạo file `nginx.conf`:

```nginx
upstream api_backend {
    server localhost:8000;
}

upstream web_backend {
    server localhost:8501;
}

server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

server {
    listen 80;
    server_name app.yourdomain.com;

    location / {
        proxy_pass http://web_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

---

**Cập nhật**: 29/01/2026
**Version**: Docker Compose v3.8
