# VBPL Web Scraper

🕷️ Công cụ thu thập văn bản pháp luật từ [vbpl.vn](https://vbpl.vn) và upload lên Google Drive.

## Tính năng

- 📋 Thu thập thuộc tính văn bản (tên, số ký hiệu, ngày ban hành, cơ quan ban hành...)
- 🔗 Thu thập văn bản liên quan (văn bản căn cứ, văn bản hướng dẫn...)
- 📎 Tải file `.doc`, `.docx`, `.pdf` và upload lên Google Drive
- 📦 Tự động giải nén file `.zip`/`.rar` để lấy tài liệu bên trong
- 💾 Lưu dữ liệu dạng JSON

## Cài đặt

```bash
# Clone repo
git clone https://github.com/ntkhai268/vbpl.git
cd vbpl

# Cài đặt dependencies
pip install -r requirements.txt
```

## Cấu hình Google Drive

1. Tạo project trên [Google Cloud Console](https://console.cloud.google.com/)
2. Bật **Google Drive API**
3. Tạo **OAuth 2.0 Client ID** (Desktop app)
4. Tải file `credentials.json` và đặt vào thư mục project
5. Chạy lần đầu để xác thực (sẽ mở trình duyệt)

## Cấu hình thư mục lưu trữ

Mở file `config.py` để thay đổi cấu hình:

```python
# === Google Drive Configuration ===
# Thay đổi DRIVE_FOLDER_ID theo loại văn bản cần crawl
# Ví dụ: tạo các thư mục khác nhau trên Drive cho từng loại
DRIVE_FOLDER_ID = "1CM8EQglHrZjDCvpHA8hcxirIXjwvqg8g"  # Thay bằng ID thư mục của bạn

# Cách lấy Folder ID:
# 1. Mở thư mục trên Google Drive
# 2. Copy phần cuối URL: https://drive.google.com/drive/folders/{FOLDER_ID}
```

## Sử dụng

### Thu thập một văn bản theo ID

```bash
python main.py --id 32801
```

### Thu thập theo danh mục

```bash
# Thu thập tất cả Hiến pháp
python main.py --category "https://vbpl.vn/TW/Pages/vanban.aspx?idLoaiVanBan=15&dvid=13"

# Giới hạn số lượng (để test)
python main.py --category "https://vbpl.vn/TW/Pages/vanban.aspx?idLoaiVanBan=15&dvid=13" --max 5
```

### Thu thập theo danh mục (Đa luồng)

Tăng tốc độ thu thập bằng cách chạy nhiều luồng song song (mặc định 5).

```bash
# Sử dụng 10 luồng
python main.py --category "http://...cat_url..." --workers 10

# Sử dụng 10 luồng và giới hạn 20 văn bản
python main.py --category "http://...cat_url..." --workers 10 --max 20
```

### Không upload file lên Drive

```bash
python main.py --id 32801 --no-upload
```

## Tham số CLI

| Tham số | Mô tả |
|---------|-------|
| `--id`, `-i` | ID văn bản cần thu thập |
| `--category`, `-c` | URL danh mục cần thu thập |
| `--workers`, `-w` | Số luồng chạy song song (mặc định: 5) |
| `--max`, `-m` | Số lượng văn bản tối đa |
| `--no-upload` | Bỏ qua upload file lên Drive |

## Cấu trúc dữ liệu đầu ra

```json
{
  "_id": "32801",
  "thuoc_tinh": {
    "ten_van_ban": "Hiến pháp 2013",
    "so_ky_hieu": "",
    "ngay_ban_hanh": "28/11/2013",
    "loai_van_ban": "Hiến pháp",
    "co_quan_ban_hanh": "Quốc hội",
    ...
  },
  "van_ban_lien_quan": {
    "van_ban_can_cu": ["123", "456"],
    ...
  },
  "metadata_he_thong": {
    "ngay_crawl": "2026-01-21T15:00:00",
    "doc_url": "https://drive.google.com/...",
    "pdf_url": "https://drive.google.com/..."
  }
}
```

## Cấu trúc thư mục

```
vbpl/
├── main.py              # Entry point chính
├── config.py            # Cấu hình
├── crawler_list.py      # Thu thập danh sách ID từ danh mục
├── crawler_detail.py    # Thu thập chi tiết văn bản
├── drive_manager.py     # Upload file lên Google Drive
├── utils.py             # Các hàm tiện ích
├── credentials.json     # OAuth credentials (không commit)
├── token.json           # OAuth token (không commit)
├── data/                # Dữ liệu JSON đầu ra
└── temp/                # File tạm khi download
```

## License

MIT
