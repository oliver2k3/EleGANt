# 💄 EleGANt Makeup Transfer - GUI Application

Giao diện đồ họa cho việc chuyển makeup giữa các ảnh sử dụng AI.

## ✨ Tính năng mới

### 📸 Hai loại output:
1. **Face Only**: Chỉ có khuôn mặt đã được makeup (như bản gốc)
2. **Full Image** ⭐: Ảnh gốc đầy đủ với makeup đã được áp dụng lên khuôn mặt (GIỮ NGUYÊN BỐI CẢNH)

## 🚀 Cách sử dụng

### 1. Chạy GUI (Khuyến nghị)

```bash
streamlit run app.py
```

Trình duyệt sẽ tự động mở tại `http://localhost:8501`

**Các bước:**
1. Upload ảnh source (không makeup) hoặc dùng ảnh mẫu
2. Upload ảnh reference (có makeup) hoặc dùng ảnh mẫu  
3. Click "Apply Makeup Transfer"
4. Xem thanh tiến trình và thời gian xử lý
5. Xem kết quả:
   - **4 ảnh so sánh**: Source | Reference | Face Only | Full Image
   - **Before & After**: So sánh full image
6. Download kết quả:
   - "Download Face Only" - Chỉ có mặt
   - "Download Full Image" - Ảnh đầy đủ (Khuyến nghị) ⭐

### 2. Chạy từ Command Line

#### Demo với 2 file cụ thể:
```bash
python3 scripts/demo.py --gpu cpu \
  --source-file assets/images/non-makeup/source_4.jpg \
  --reference-file assets/images/makeup/reference_2.png
```

**Output:**
- `result_source_4_comparison.png` - Ảnh so sánh 4 cột (Source | Reference | Face | Full)
- `result_source_4_full.png` - Chỉ có ảnh full image kết quả ⭐

#### Demo với toàn bộ thư mục:
```bash
python3 scripts/demo.py --gpu cpu \
  --source-dir assets/images/non-makeup \
  --reference-dir assets/images/makeup
```

## 📊 So sánh Output

### Face Only (Cũ):
- ✅ Chất lượng makeup cao
- ❌ Mất background/bối cảnh
- ❌ Chỉ có khuôn mặt

### Full Image (Mới) ⭐:
- ✅ Chất lượng makeup cao
- ✅ Giữ nguyên background/bối cảnh
- ✅ Ảnh hoàn chỉnh với toàn bộ khung hình
- ✅ Tự nhiên hơn cho việc chia sẻ

## 🎨 Ví dụ

```bash
# Test nhanh với ảnh mẫu
python3 scripts/demo.py --gpu cpu \
  --source-file assets/images/non-makeup/source_1.png \
  --reference-file assets/images/makeup/reference_3.png
```

Kết quả sẽ được lưu tại:
- `result/demo/result_source_1_comparison.png` - So sánh 4 ảnh
- `result/demo/result_source_1_full.png` - Full image với makeup

## 💡 Tips

1. **Sử dụng ảnh source chất lượng cao** để có kết quả tốt nhất
2. **Full Image output** phù hợp cho việc:
   - Chia sẻ trên mạng xã hội
   - So sánh before/after tự nhiên
   - Giữ nguyên ngữ cảnh của ảnh gốc
3. **Face Only output** phù hợp khi:
   - Chỉ muốn focus vào khuôn mặt
   - Tích hợp vào ứng dụng khác

## 🎯 Demo GUI Features

- ✅ Upload ảnh dễ dàng (PNG, JPG, JPEG)
- ✅ Preview ảnh trước khi xử lý
- ✅ Progress bar theo thời gian thực
- ✅ Đồng hồ đếm thời gian xử lý
- ✅ Hiển thị 4 ảnh so sánh
- ✅ Hiển thị Before/After full image
- ✅ Download cả 2 loại output
- ✅ Responsive design
- ✅ Ảnh mẫu tích hợp sẵn

## 📝 Technical Details

**Cơ chế hoạt động:**
1. Detect khuôn mặt trong ảnh source
2. Crop vùng mặt để xử lý
3. Áp dụng makeup transfer sử dụng EleGANt model
4. Tạo 2 outputs:
   - **Face**: Resize lại khuôn mặt đã makeup
   - **Full**: Paste khuôn mặt đã makeup về vị trí gốc trên ảnh đầy đủ

## 🐛 Troubleshooting

**Lỗi: "Processing failed"**
- Đảm bảo ảnh có khuôn mặt rõ ràng
- Thử với ảnh khác hoặc ảnh mẫu

**GUI không mở:**
```bash
# Kiểm tra Streamlit đã cài đặt
pip3 list | grep streamlit

# Chạy lại
streamlit run app.py
```

**Xử lý chậm:**
- Đang chạy trên CPU, có thể mất 10-30 giây/ảnh
- Nếu có GPU, sửa `--gpu cpu` thành `--gpu 0`

## 📄 License

Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License
