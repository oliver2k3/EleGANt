# EleGANt - Docker Deployment Guide

Hướng dẫn chạy ứng dụng EleGANt Makeup Transfer trên Docker.

## Yêu Cầu

- Docker (phiên bản 20.10 trở lên)
- Docker Compose (phiên bản 1.29 trở lên)
- Ít nhất 4GB RAM khả dụng
- File checkpoint model: `ckpts/sow_pyramid_a5_e3d2_remapped.pth`

## Cài Đặt Nhanh

### 1. Clone repository (nếu chưa có)
```bash
git clone <repository-url>
cd EleGANt
```

### 2. Tải model checkpoint
Đảm bảo file `sow_pyramid_a5_e3d2_remapped.pth` đã được đặt trong thư mục `ckpts/`.

Nếu chưa có, tải về từ: https://drive.google.com/drive/folders/1xzIS3Dfmsssxkk9OhhAS4svrZSPfQYRe?usp=sharing

### 3. Build và chạy với Docker Compose
```bash
# Build image
docker-compose build

# Chạy container
docker-compose up -d

# Xem logs
docker-compose logs -f
```

### 4. Truy cập ứng dụng
Mở trình duyệt và truy cập: **http://localhost:8501**

## Các Lệnh Docker Hữu Ích

### Chạy container
```bash
# Chạy ở chế độ background
docker-compose up -d

# Chạy ở chế độ foreground (xem logs trực tiếp)
docker-compose up
```

### Dừng container
```bash
docker-compose down
```

### Xem logs
```bash
# Xem tất cả logs
docker-compose logs

# Xem logs realtime
docker-compose logs -f

# Xem 100 dòng logs cuối cùng
docker-compose logs --tail=100
```

### Restart container
```bash
docker-compose restart
```

### Build lại image
```bash
# Build lại khi có thay đổi code
docker-compose build --no-cache
docker-compose up -d
```

## Chạy với Docker (không dùng Docker Compose)

```bash
# Build image
docker build -t elegant-makeup-transfer .

# Run container
docker run -d \
  -p 8501:8501 \
  -v $(pwd)/ckpts:/app/ckpts \
  -v $(pwd)/result:/app/result \
  --name elegant-app \
  elegant-makeup-transfer

# Xem logs
docker logs -f elegant-app

# Dừng container
docker stop elegant-app

# Xóa container
docker rm elegant-app
```

## Cấu Hình

### Thay đổi port
Mặc định ứng dụng chạy trên port 8501. Để thay đổi, sửa file `docker-compose.yml`:

```yaml
ports:
  - "8080:8501"  # Chạy trên port 8080 thay vì 8501
```

### Sử dụng GPU (nếu có NVIDIA GPU)

Cập nhật `docker-compose.yml`:

```yaml
services:
  elegant-web:
    # ... các cấu hình khác ...
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

Và cập nhật `Dockerfile` để cài đặt CUDA version phù hợp.

## Xử Lý Sự Cố

### Container không khởi động
```bash
# Kiểm tra logs
docker-compose logs

# Kiểm tra status
docker-compose ps
```

### Port đã được sử dụng
Nếu port 8501 đã được sử dụng, thay đổi port trong `docker-compose.yml` hoặc dừng service đang dùng port đó.

### Model checkpoint không tìm thấy
Đảm bảo file `sow_pyramid_a5_e3d2_remapped.pth` tồn tại trong thư mục `ckpts/`:
```bash
ls -la ckpts/
```

### Out of memory
Tăng memory limit cho Docker trong Docker Desktop settings (ít nhất 4GB).

## Cấu Trúc Thư Mục Được Mount

```
./ckpts    -> /app/ckpts    # Model checkpoints
./result   -> /app/result   # Kết quả xử lý
./assets   -> /app/assets   # Ảnh mẫu và tài nguyên
```

## Production Deployment

### Sử dụng reverse proxy (Nginx)

Tạo file `nginx.conf`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Sử dụng HTTPS với Let's Encrypt

```bash
# Cài đặt certbot
sudo apt-get install certbot python3-certbot-nginx

# Tạo SSL certificate
sudo certbot --nginx -d yourdomain.com
```

## Giấy Phép

Ứng dụng này sử dụng giấy phép CC BY-NC-SA 4.0. Xem file LICENSE để biết thêm chi tiết.

## Liên Hệ & Hỗ Trợ

- Repository: https://github.com/Chenyu-Yang-2000/EleGANt
- Issues: https://github.com/Chenyu-Yang-2000/EleGANt/issues
