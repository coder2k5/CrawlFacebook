# config.py
import os

def load_credentials(filepath='facebook_credentials.txt'):
    """Đọc email và password từ file text."""
    try:
        with open(filepath, 'r') as file:
            # Giả định định dạng file cũ: dòng 1 là "email", dòng 2 là "pass"
            email = file.readline().split('"')[1]
            password = file.readline().split('"')[1]
            return email, password
    except FileNotFoundError:
        print(f"Error: File {filepath} not found.")
        exit(1)
    except IndexError:
        print("Error: Invalid credential file format.")
        exit(1)