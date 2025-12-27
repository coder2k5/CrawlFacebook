# config.py
import os

CREDENTIALS_FILE = 'facebook_credentials.txt'
EMAIL = ""
PASSWORD = ""

if os.path.exists(CREDENTIALS_FILE):
    with open(CREDENTIALS_FILE, 'r') as file:
        try:
            EMAIL = file.readline().split('"')[1]
            PASSWORD = file.readline().split('"')[1]
        except IndexError:
            print("Lỗi định dạng file credentials")
else:
    print(f"Không tìm thấy file {CREDENTIALS_FILE}")