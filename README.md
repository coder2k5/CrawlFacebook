Tạo môi trường ảo chạy project

# 1. Tạo môi trường ảo tên là 'venv' ngay tại thư mục hiện tại
python3 -m venv venv

# 2. Kích hoạt môi trường này lên (Bước này quan trọng nhất)
source venv/bin/activate

# 3. Cài các thư viện yêu cầu (tạo file requirements.txt nếu chưa có hoặc cài tay)
pip install selenium requests

# 4. Ngay tại terminal (đang có chữ (venv)) để cài đặt thiếu các thư viện cần thiết:
pip install mysql-connector-python bcrypt requests beautifulsoup4 selenium Pillow

# 5. Chạy dự án
python3 scraper.py