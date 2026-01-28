# EleGANt Makeup Transfer API

API server cho ứng dụng makeup transfer sử dụng EleGANt model.

## Cài đặt

```bash
pip install fastapi uvicorn
```

## Chạy API Server

```bash
python api.py
```

Server sẽ chạy tại: `http://localhost:8000`

## API Documentation

Khi server đang chạy, truy cập:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Endpoints

### 1. Health Check
```
GET /health
```

### 2. Transfer Makeup
```
POST /transfer
```

**Request Body:**
```json
{
  "source_images": [
    "path/to/source1.jpg",
    "path/to/source2.jpg"
  ],
  "reference_image": "path/to/reference.jpg",
  "session_id": "session_001",
  "output_folder": "result",
  "lip_intensity": 1.0,
  "skin_intensity": 1.0,
  "eye_intensity": 1.0,
  "save_face_only": false
}
```

**Parameters:**
- `source_images` (required): Danh sách đường dẫn các ảnh source (không makeup)
- `reference_image` (required): Đường dẫn ảnh reference (có makeup)
- `session_id` (required): Session ID để tạo folder riêng cho mỗi session
- `output_folder` (optional): Thư mục gốc lưu kết quả (mặc định: "result")
- `lip_intensity` (optional): Độ đậm son môi 0.0-1.5 (mặc định: 1.0)
- `skin_intensity` (optional): Độ đậm makeup da 0.0-1.5 (mặc định: 1.0)
- `eye_intensity` (optional): Độ đậm makeup mắt 0.0-1.5 (mặc định: 1.0)
- `save_face_only` (optional): True = chỉ lưu face, False = lưu full image (mặc định: False)

**Response:**
```json
{
  "success": true,
  "message": "Processed 2 out of 2 images successfully",
  "session_id": "session_001",
  "output_folder": "result/session_001",
  "total_images": 2,
  "successful": 2,
  "failed": 0,
  "processing_time": 5.23,
  "results": [
    {
      "index": 0,
      "source_path": "path/to/source1.jpg",
      "output_path": "result/session_001/source1_maked.jpg",
      "output_filename": "source1_maked.jpg",
      "result_type": "full_image",
      "processing_time": 2.45
    }
  ],
  "errors": null
}
```

### 3. Delete Session Folder
```
GET /delete/{session_id}?output_folder=result
```

**Parameters:**
- `session_id` (required): Session ID cần xóa
- `output_folder` (optional): Thư mục gốc (mặc định: "result")

**Response:**
```json
{
  "success": true,
  "message": "Session folder deleted successfully",
  "session_id": "session_001",
  "deleted_path": "result/session_001"
}
```

## Ví dụ sử dụng

### Python (requests)

```python
import requests

payload = {
    "source_images": [
        "assets/images/non-makeup/vFG112.png",
        "assets/images/non-makeup/vFG456.png"
    ],
    "reference_image": "assets/images/makeup/XMY-006.png",
    "session_id": "session_batch_001",
    "output_folder": "result",
    "lip_intensity": 1.2,
    "skin_intensity": 1.0,
    "eye_intensity": 1.0,
    "save_face_only": False
}

response = requests.post("http://localhost:8000/transfer", json=payload)
result = response.json()
print(result)

# Xóa session sau khi hoàn thành
delete_response = requests.get(f"http://localhost:8000/delete/{payload['session_id']}")
print(delete_response.json())
```

### cURL

```bash
curl -X POST "http://localhost:8000/transfer" \
  -H "Content-Type: application/json" \
  -d '{
    "source_images": ["path/to/source.jpg"],
    "reference_image": "path/to/reference.jpg",
    "session_id": "session_001",
    "output_folder": "result",
    "lip_intensity": 1.0,
    "skin_intensity": 1.0,
    "eye_intensity": 1.0,
    "save_face_only": false
  }'

# Xóa session
curl -X GET "http://localhost:8000/delete/session_001?output_folder=result"
```

### JavaScript (fetch)

```javascript
const payload = {
  source_images: ["path/to/source1.jpg", "path/to/source2.jpg"],
  reference_image: "path/to/reference.jpg",
  session_id: "session_001",
  output_folder: "result",
  lip_intensity: 1.0,
  skin_intensity: 1.0,
  eye_intensity: 1.0,
  save_face_only: false
};

fetch('http://localhost:8000/transfer', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(payload)
})
  .then(response => response.json())
  .then(data => {
    console.log(data);
    
    // Xóa session sau khi hoàn thành
    return fetch(`http://localhost:8000/delete/${payload.session_id}`);
  })
  .then(response => response.json())
  .then(data => console.log('Deleted:', data));
```

## Kết quả

File kết quả sẽ được lưu trong folder được tạo theo session_id:
- Cấu trúc folder: `{output_folder}/{session_id}/`
- Ví dụ: `result/session_001/`
- Tên file gốc: `image.jpg`
- Tên file kết quả: `image_maked.jpg`

## Quản lý Session

### Tạo Session và Xử lý
```python
import requests

# Tạo session_id unique
import uuid
session_id = str(uuid.uuid4())  # Ví dụ: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

# Hoặc sử dụng timestamp
import time
session_id = f"session_{int(time.time())}"  # Ví dụ: "session_1738072800"

# Gửi request
payload = {
    "source_images": ["image1.jpg", "image2.jpg"],
    "reference_image": "reference.jpg",
    "session_id": session_id,
    "output_folder": "result"
}
response = requests.post("http://localhost:8000/transfer", json=payload)
```

### Xóa Session
```python
# Xóa toàn bộ folder session và các file trong đó
response = requests.get(f"http://localhost:8000/delete/{session_id}")
print(response.json())
# Output: {"success": true, "message": "Session folder deleted successfully", ...}
```

## Xử lý nhiều file cùng lúc

API hỗ trợ xử lý nhiều file trong 1 request. Ví dụ xử lý 8 file:

```python
payload = {
    "source_images": [
        "path/to/image1.jpg",
        "path/to/image2.jpg",
        "path/to/image3.jpg",
        "path/to/image4.jpg",
        "path/to/image5.jpg",
        "path/to/image6.jpg",
        "path/to/image7.jpg",
        "path/to/image8.jpg"
    ],
    "reference_image": "path/to/reference.jpg",
    "session_id": "batch_session_001",
    "output_folder": "result"
}

response = requests.post("http://localhost:8000/transfer", json=payload)
print(f"Results saved in: {response.json()['output_folder']}")
# Output: Results saved in: result/batch_session_001

# Sau khi lấy kết quả, có thể xóa session
# requests.get(f"http://localhost:8000/delete/batch_session_001")
```

Response sẽ bao gồm:
- Tổng thời gian xử lý
- Thời gian xử lý từng ảnh
- Danh sách file kết quả
- Danh sách lỗi (nếu có)

## Lưu ý

- API tự động tạo folder output theo session_id nếu chưa tồn tại
- Cấu trúc folder: `{output_folder}/{session_id}/`
- Tên file kết quả = tên file gốc + hậu tố `_maked`
- Hỗ trợ các format ảnh: PNG, JPG, JPEG
- Model sẽ được load khi server khởi động (chỉ load 1 lần)
- Sử dụng `GET /delete/{session_id}` để xóa folder session và tất cả file trong đó
- Nên sử dụng session_id unique cho mỗi request (UUID hoặc timestamp)
