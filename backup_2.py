import mysql.connector
import bcrypt
import requests
import unicodedata
from datetime import datetime
from bs4 import BeautifulSoup
import re
import json
import os
import time
import random
import hashlib
from urllib.parse import urlparse
from PIL import Image
import uuid

# Selenium Imports
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException

# ==========================================
# 1. CONFIGURATION & CREDENTIALS (from scraper.py)
# ==========================================

# Cố gắng đọc file credentials, nếu không có thì gán rỗng (cần điền tay hoặc tạo file)
EMAIL = ""
PASSWORD = ""
try:
    with open('facebook_credentials.txt', 'r') as file:
        lines = file.readlines()
        if len(lines) >= 2:
            line1 = lines[0].strip()
            line2 = lines[1].strip()
            
            # Kiểm tra nếu file theo định dạng: email = "..."
            if '"' in line1:
                EMAIL = line1.split('"')[1]
                PASSWORD = line2.split('"')[1]
            else:
                # Nếu file chỉ chứa email và pass thuần túy
                EMAIL = line1
                PASSWORD = line2
                
except FileNotFoundError:
    print("Warning: 'facebook_credentials.txt' not found.")
except IndexError:
    print("Error: Check format of 'facebook_credentials.txt'.")

# Đường dẫn lưu ảnh (giữ nguyên từ file cũ)
image_folder = r"/var/www/thinkdiff-web/vang247_xyz/image_tintuc/"
if not os.path.exists(image_folder):
    os.makedirs(image_folder)

seen_posts = set()

# ==========================================
# 2. DATABASE & HELPER FUNCTIONS (from crawl_facebook_thongtin_vang.py)
# ==========================================

def connect_to_database():
    return mysql.connector.connect(
        host="localhost",      
        user='phpmyadmin',
        password='Sonhehe89!',
        database='gold_silver', 
    )

def xoa_dau(txt: str) -> str:
    BANG_XOA_DAU = str.maketrans(
        "ÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬĐÈÉẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴáàảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ",
        "A"*17 + "D" + "E"*11 + "I"*5 + "O"*17 + "U"*11 + "Y"*5 + "a"*17 + "d" + "e"*11 + "i"*5 + "o"*17 + "u"*11 + "y"*5
    )
    if not unicodedata.is_normalized("NFC", txt):
        txt = unicodedata.normalize("NFC", txt)
    return txt.translate(BANG_XOA_DAU)

def get_provinces_id_from_title(title_text):
    provinces_mapping = {
        'An Giang': 1, 'Bà Rịa - Vũng Tàu': 2, 'Bạc Liêu': 3, 'Bắc Kạn': 4, 'Bắc Giang': 5,
        'Bắc Ninh': 6, 'Bến Tre': 7, 'Bình Dương': 8, 'Bình Định': 9, 'Bình Phước': 10,
        'Bình Thuận': 11, 'Cà Mau': 12, 'Cao Bằng': 13, 'Cần Thơ': 14, 'Đà Nẵng': 15,
        'Đắk Lắk': 16, 'Đắk Nông': 17, 'Điện Biên': 18, 'Đồng Nai': 19, 'Đồng Tháp': 20,
        'Gia Lai': 21, 'Hà Giang': 22, 'Hà Nam': 23, 'Hà Nội': 24, 'Hà Tĩnh': 25,
        'Hải Dương': 26, 'Hải Phòng': 27, 'Hòa Bình': 28, 'Hồ Chí Minh': 29, 'HCM': 29,
        'Hậu Giang': 30, 'Hưng Yên': 31, 'Khánh Hòa': 32, 'Kiên Giang': 33, 'Kon Tum': 34,
        'Lai Châu': 35, 'Lào Cai': 36, 'Lạng Sơn': 37, 'Lâm Đồng': 38, 'Long An': 39,
        'Nam Định': 40, 'Nghệ An': 41, 'Ninh Bình': 42, 'Ninh Thuận': 43, 'Phú Thọ': 44,
        'Phú Yên': 45, 'Quảng Bình': 46, 'Quảng Nam': 47, 'Quảng Ngãi': 48, 'Quảng Ninh': 49,
        'Quảng Trị': 50, 'Sóc Trăng': 51, 'Sơn La': 52, 'Tây Ninh': 53, 'Thái Bình': 54,
        'Thái Nguyên': 55, 'Thanh Hóa': 56, 'Thừa Thiên Huế': 57, 'Tiền Giang': 58,
        'Trà Vinh': 59, 'Tuyên Quang': 60, 'Vĩnh Long': 61, 'Vĩnh Phúc': 62, 'Yên Bái': 63
    }
    title_text_lower = title_text.lower()
    for province_name, provinces_id in provinces_mapping.items():
        if province_name.lower() in title_text_lower:
            return provinces_id
    return None

def get_district_id_from_title(title_text):
    connection = connect_to_database()
    cursor = connection.cursor()
    cursor.execute("SELECT DistrictID FROM Districts WHERE LOWER(DistrictName) LIKE LOWER(%s)", ('%' + title_text + '%',))
    result = cursor.fetchone()
    connection.close()
    if result:
        return result[0]
    return None

def insert_user_to_db(username):
    cleaned_username = re.sub(r'\W+', '', username)
    cleaned_username = xoa_dau(cleaned_username)
    password_hashed = bcrypt.hashpw("123456".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    email = f"{cleaned_username}@gmail.com"

    try:
        connection = connect_to_database()
        cursor = connection.cursor()
        check_query = "SELECT COUNT(*) FROM Users WHERE Username = %s"
        cursor.execute(check_query, (username,))
        user_exists = cursor.fetchone()[0] > 0

        if not user_exists:
            insert_query = """
                INSERT INTO Users (Fullname, Username, Password, Email, Role, coin, Confirmed, Blocked, IsAnonymous)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            # Giản lược data cho ngắn gọn, logic giữ nguyên
            data = ("", username, password_hashed, email, 0, 0, 0, 0, 0)
            cursor.execute(insert_query, data)
            connection.commit()
            print(f"User {username} inserted successfully.")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def insert_into_forumposts(user_id, group_id, title, content, post_time, ip_posted, post_latitude, post_longitude, time_view, district_id, provinces_id):
    connection = connect_to_database()
    cursor = connection.cursor()

    check_exact_query = "SELECT PostID FROM ForumPosts WHERE Content = %s LIMIT 1"
    cursor.execute(check_exact_query, (content,))
    existing_post = cursor.fetchone()

    if existing_post:
        cursor.close()
        connection.close()
        return existing_post[0]

    suffix = '… See more'
    if content.endswith(suffix):
        truncated_content = content[:len(content) - len(suffix)].strip()
        truncated_escaped = truncated_content.replace('%', '\\%').replace('_', '\\_')
        like_pattern = f"{truncated_escaped}%"
        cursor.execute("SELECT PostID FROM ForumPosts WHERE Content LIKE %s LIMIT 1", (like_pattern,))
        truncated_post = cursor.fetchone()
        if truncated_post:
            cursor.close()
            connection.close()
            return truncated_post[0]

    insert_query = """
        INSERT INTO ForumPosts (UserID, GroupID, Title, Content, PostTime, IPPosted, PostLatitude, PostLongitude, UpdatePostAt, timeView, district_id, provinces_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NULL, %s, %s, %s)
    """
    values = (user_id, group_id, title, content, post_time, ip_posted, post_latitude, post_longitude, time_view, district_id, provinces_id)
    cursor.execute(insert_query, values)
    connection.commit()
    post_id = cursor.lastrowid
    cursor.close()
    connection.close()
    return post_id

def insert_into_forumphotos(post_id, photo_url, upload_time):
    connection = connect_to_database()
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM ForumPhotos WHERE PhotoURL = %s", (photo_url,))
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO ForumPhotos (PostID, PhotoURL, uploadTime) VALUES (%s, %s, %s)", (post_id, photo_url, upload_time))
        connection.commit()
    cursor.close()
    connection.close()

def update_forumposts_on_see_more(content_text):
    try:
        connection = connect_to_database()
        cursor = connection.cursor()
        suffix = "… See more"
        find_query = """
            SELECT PostID, Content FROM ForumPosts 
            WHERE Content LIKE %s AND %s LIKE CONCAT(TRIM(TRAILING %s FROM Content), '%%')
            ORDER BY LENGTH(Content) DESC LIMIT 1
        """
        cursor.execute(find_query, (f'%{suffix}', content_text, suffix))
        if result := cursor.fetchone():
            post_id, old_content = result
            base_content = old_content.rsplit(suffix, 1)[0].strip()
            if content_text.startswith(base_content):
                cursor.execute("UPDATE ForumPosts SET Content = %s, UpdatePostAt = NOW() WHERE PostID = %s", (content_text, post_id))
                connection.commit()
    except Exception as e:
        print(f"Update failed: {e}")
    finally:
        if connection: connection.close()

def generate_post_id(username, content):
    unique_string = f"{username}_{content}"
    return hashlib.md5(unique_string.encode()).hexdigest()

def download_image(image_url, save_path):
    try:
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            with open(save_path, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            return True
    except Exception as e:
        print(f"Failed to download image: {e}")
    return False

def get_user_id(username):
    try:
        with connect_to_database() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT UserID FROM Users WHERE Username = %s", (username,))
                result = cursor.fetchone()
                return result[0] if result else None
    except Exception:
        return None

def find_post_id_by_content(content):
    try:
        cleaned_content = content.strip()
        if cleaned_content.endswith("... See more") or cleaned_content.endswith("… See more"):
            cleaned_content = cleaned_content.rsplit("See more", 1)[0].strip()[:-1].strip()
        
        with connect_to_database() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT PostID FROM ForumPosts WHERE TRIM(Content) LIKE CONCAT(%s, '%%') ORDER BY PostID DESC LIMIT 1", (cleaned_content,))
                result = cursor.fetchone()
                return result[0] if result else None
    except Exception:
        return None

def insert_comment(post_id, user_id, content):
    try:
        with connect_to_database() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM Comments WHERE idPost = %s AND idUser = %s AND content = %s LIMIT 1", (post_id, user_id, content.strip()))
                if result := cursor.fetchone():
                    return result[0]
                cursor.execute("INSERT INTO Comments (idPost, idUser, content, actionAt) VALUES (%s, %s, %s, NOW())", (post_id, user_id, content.strip()))
                conn.commit()
                return cursor.lastrowid
    except Exception as e:
        print(f"Error insert comment: {e}")
        return None

def download_comment_image(photo_url, save_folder=r"/home/son/Documents/landinvest2/nhatot_batdongsan.com.vn/"):
    if not photo_url: return None
    try:
        os.makedirs(save_folder, exist_ok=True)
        response = requests.get(photo_url, stream=True)
        if response.status_code == 200:
            file_name = os.path.basename(urlparse(photo_url).path).split("?")[0]
            if not os.path.splitext(file_name)[1]: file_name += ".jpeg"
            file_path = os.path.join(save_folder, file_name)
            with open(file_path, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            if file_path.lower().endswith(".jfif"):
                try:
                    with Image.open(file_path) as img:
                        jpeg_path = file_path.rsplit('.', 1)[0] + ".jpeg"
                        img.convert("RGB").save(jpeg_path, "JPEG")
                        os.remove(file_path)
                        return jpeg_path
                except: pass
            return file_path
    except: return None

def insert_comment_photo(comment_id, photo_url):
    try:
        local_path = download_comment_image(photo_url)
        if not local_path: return None
        formatted_path = f"[img]{local_path}[/img]"
        with connect_to_database() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT PhotoID FROM CommentPhotos WHERE CommentID = %s AND PhotoURL = %s LIMIT 1", (comment_id, formatted_path))
                if result := cursor.fetchone(): return result[0]
                cursor.execute("INSERT INTO CommentPhotos (CommentID, PhotoURL, UploadTime) VALUES (%s, %s, NOW())", (comment_id, formatted_path))
                conn.commit()
                return cursor.lastrowid
    except: return None

# ==========================================
# 3. SELENIUM HELPER FUNCTIONS (Interaction)
# ==========================================

def click_see_more(driver, post_element):
    try:
        see_more_button = WebDriverWait(post_element, 5).until(
            EC.element_to_be_clickable((By.XPATH, ".//div[@role='button' and contains(text(), 'See more')]"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", see_more_button)
        time.sleep(1)
        see_more_button.click()
        time.sleep(2)
        return True
    except:
        return False

def click_comments(driver, post_element):
    try:
        comments_span = WebDriverWait(post_element, 5).until(
            EC.element_to_be_clickable((By.XPATH, 
                ".//span[contains(text(), 'comment') or contains(text(), 'bình luận')]")) # Adjusted for generic match
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", comments_span)
        comments_span.click()
        time.sleep(3)
        return True
    except:
        return False

# ==================================================================
# [THÊM MỚI] HÀM MỞ RỘNG BÌNH LUẬN
# ==================================================================
def expand_all_comments(driver, post_element):
    """
    Click nút 'Xem thêm bình luận' liên tục cho đến khi hết.
    """
    print("  -> Đang mở rộng bình luận...")
    max_clicks = 10 # Giới hạn số lần click để tránh treo
    clicks = 0
    while clicks < max_clicks:
        try:
            # Tìm nút xem thêm (dựa trên text tiếng Việt hoặc Anh)
            view_more_btns = post_element.find_elements(By.XPATH, 
                ".//div[@role='button'][contains(., 'Xem thêm bình luận') or contains(., 'View more comments')]"
            )
            
            if not view_more_btns:
                # Tìm nút dạng "Xem các bình luận trước"
                view_more_btns = post_element.find_elements(By.XPATH, 
                    ".//span[contains(text(), 'Xem thêm') or contains(text(), 'View more')]"
                )

            if not view_more_btns:
                break # Không còn nút nào để bấm

            # Click nút đầu tiên tìm thấy
            btn = view_more_btns[0]
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(3) # Chờ load ajax
            clicks += 1
        except Exception:
            break
# ==========================================
# 4. LOGIN LOGIC (FROM SCRAPER.PY)
# ==========================================

def _login(browser, email, password):
    """
    Hàm login được lấy nguyên văn logic từ scraper.py
    """
    print("Starting Login process...")
    browser.get("http://facebook.com")
    browser.maximize_window()
    time.sleep(3)
    
    # Wait for email field to be present
    wait = WebDriverWait(browser, 15)
    email_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
    email_field.clear()
    email_field.send_keys(email)
    
    # Wait for password field and fill it
    password_field = wait.until(EC.presence_of_element_located((By.NAME, "pass")))
    password_field.clear()
    password_field.send_keys(password)
    
    # Wait for login button - try different selectors (robust logic from scraper.py)
    try:
        # Try ID first (older Facebook version)
        login_button = wait.until(EC.element_to_be_clickable((By.ID, 'loginbutton')))
    except:
        # Try button with type='submit'
        try:
            login_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@name="login"]')))
        except:
            # Try any submit button
            login_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]')))
    
    login_button.click()
    print("Login button clicked. Waiting for redirection...")
    time.sleep(10) # Chờ load sau login

# ==========================================
# 5. MAIN CRAWL FUNCTION
# ==========================================

def crawl_page():
    # --- SETUP DRIVER (Using scraper.py logic/options) ---
    option = Options()
    option.add_argument("--disable-infobars")
    option.add_argument("start-maximized")
    option.add_argument("--disable-extensions")
    # Tắt notification popup của Facebook
    option.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 1
    })

    # Khởi tạo Chrome Driver (giả định dùng chromedriver)
    # Nếu bạn dùng path cụ thể cho chromedriver, hãy sửa tham số service=Service('/path/to/chromedriver')
    try:
        service = Service("./chromedriver") # Hoặc đường dẫn tới chromedriver của bạn
        driver = webdriver.Chrome(service=service, options=option)
    except Exception:
        # Fallback nếu không tìm thấy driver cục bộ, thử dùng driver hệ thống
        driver = webdriver.Chrome(options=option)
    
    driver.set_page_load_timeout(180)

    # --- LOGIN ---
    try:
        _login(driver, EMAIL, PASSWORD)
    except Exception as e:
        print(f"Login failed: {e}")
        driver.quit()
        return

    # --- NAVIGATE TO GROUP ---
    group_url = "https://www.facebook.com/groups/385914624891314"
    print(f"Navigating to group: {group_url}")
    driver.get(group_url)
    time.sleep(5)

    # --- SCROLL & CRAWL LOOP (From crawl_facebook_thongtin_vang.py) ---
    index = 0
    scroll_pause_time = 2
    
    while True:
        # Tìm tất cả các bài post đang hiển thị trong DOM
        # Selector này cần được cập nhật thường xuyên do FB đổi class. 
        # Sử dụng selector từ file cũ, nhưng lưu ý class FB thường thay đổi.
        # Ở đây ta dùng XPath generic hơn cho feed unit.
        try:
            post_elements = driver.find_elements(By.XPATH, '//div[@role="feed"]//div[@role="article"]')
            if not post_elements:
                 # Fallback cho giao diện mới/khác
                post_elements = driver.find_elements(By.XPATH, '//div[contains(@class, "x1yztbdb")]')
        except:
            post_elements = []

        print(f"DEBUG: Tìm thấy {len(post_elements)} bài viết.")
        print(f"Total posts visible in DOM: {len(post_elements)}")
        
        if index >= len(post_elements):
            # Nếu đã duyệt hết list hiện tại, scroll xuống
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            print("Scrolled to bottom, waiting for new posts...")
            time.sleep(4)
            
            # Kiểm tra lại xem có load thêm được không
            new_elements = driver.find_elements(By.XPATH, '//div[@role="feed"]//div[@role="article"]')
            if len(new_elements) <= index:
                print("No new posts loaded. Stopping.")
                break
            continue

        # Lấy post hiện tại
        post_element = post_elements[index]
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", post_element)
        time.sleep(scroll_pause_time)

        try:
            # Parse nội dung bằng BeautifulSoup
            post_html = post_element.get_attribute("outerHTML")
            post = BeautifulSoup(post_html, "html.parser")
            
            date_time = datetime.now()
            content_text = ""
            username_text = "anonymous"
            
            # --- EXTRACT USERNAME ---
            # Cố gắng tìm thẻ a chứa profile link hoặc strong text
            user_tag = post.find("strong")
            if user_tag:
                username_text = user_tag.text.strip()
            
            # --- EXTRACT CONTENT ---
            # Tìm div chứa text content (class FB rất loạn, dùng logic tìm text dài nhất hoặc dir="auto")
            content_candidates = post.find_all("div", attrs={"dir": "auto"})
            if content_candidates:
                # Lấy text từ div đầu tiên có nội dung đáng kể
                for cand in content_candidates:
                    if len(cand.text) > 5:
                        content_text = cand.text.strip()
                        break
            
            if not content_text:
                content_text = "image only or content hidden"

            # --- HANDLE 'SEE MORE' ---
            content_text_seemore = content_text
            # Tìm nút See more trong post_element selenium hiện tại
            if "See more" in post_element.text or "Xem thêm" in post_element.text:
                if click_see_more(driver, post_element):
                    print("Clicked 'See more'")
                    # Parse lại sau khi click
                    post_html_after = post_element.get_attribute("outerHTML")
                    post_after = BeautifulSoup(post_html_after, "html.parser")
                    # Extract lại text đầy đủ
                    content_candidates_after = post_after.find_all("div", attrs={"dir": "auto"})
                    for cand in content_candidates_after:
                         if len(cand.text) > len(content_text):
                            content_text_seemore = cand.text.strip()
                            break

            # --- EXTRACT IMAGES ---
            image_links = []
            imgs = post.find_all("img")
            for img in imgs:
                src = img.get("src", "")
                # Lọc ảnh rác (emoji, icon nhỏ)
                if src and ("https://" in src) and ("emoji" not in src) and (int(img.get("height", 0) or 0) > 50):
                     image_links.append(src)

            # --- DOWNLOAD IMAGES ---
            local_image_links = []
            for idx, link in enumerate(image_links):
                image_name = f"image_{uuid.uuid4()}.jpg"
                save_path = os.path.join(image_folder, image_name)
                if download_image(link, save_path):
                    local_image_links.append(f"[img]{save_path}[/img]")
            
            # --- DATABASE OPERATIONS ---
            post_id_hash = generate_post_id(username_text, content_text)
            
            if post_id_hash not in seen_posts:
                seen_posts.add(post_id_hash)
                print(f"--- Processing Post {index + 1} ---")
                print(f"User: {username_text}")
                print(f"Content: {content_text[:50]}...")
                
                insert_user_to_db(username_text)
                user_id = get_user_id(username_text) or 0
                
                # Logic xác định tỉnh/huyện từ text
                provinces_id = get_provinces_id_from_title(content_text)
                district_id = get_district_id_from_title(content_text)
                
                db_post_id = insert_into_forumposts(
                    user_id=user_id,
                    group_id=38,
                    title="",
                    content=content_text, # Insert nội dung ngắn trước
                    post_time=date_time,
                    ip_posted="",
                    post_latitude=0,
                    post_longitude=0,
                    time_view=0,
                    district_id=district_id,
                    provinces_id=provinces_id
                )
                
                # Update nội dung đầy đủ nếu có see more
                if content_text_seemore != content_text:
                    update_forumposts_on_see_more(content_text_seemore)
                
                # Insert ảnh
                for img_code in local_image_links:
                    insert_into_forumphotos(db_post_id, img_code, datetime.now())

                # --- HANDLE COMMENTS (NEW LOGIC) ---
                print("--- Bắt đầu xử lý bình luận ---")
                
                # 1. Click nút bình luận để đảm bảo khung comment hiện ra (nếu chưa hiện)
                try:
                    click_comments(driver, post_element)
                except:
                    pass 
                
                # 2. Mở rộng toàn bộ bình luận (Load hết comment ẩn)
                expand_all_comments(driver, post_element)

                # 3. Quét dữ liệu
                try:
                    # Tìm các div comment dựa trên aria-label (Chuẩn theo HTML bạn gửi)
                    comment_elements = post_element.find_elements(By.XPATH, 
                        ".//div[@role='article'][contains(@aria-label, 'Bình luận') or contains(@aria-label, 'Comment')]"
                    )

                    print(f"  -> Tìm thấy {len(comment_elements)} bình luận.")

                    for c_elem in comment_elements:
                        try:
                            # --- A. LẤY TÊN USER ---
                            c_user = "Anonymous"
                            
                            # Cách 1: Lấy từ aria-label "Bình luận dưới tên [ABC] vào..."
                            aria_label = c_elem.get_attribute("aria-label")
                            if aria_label:
                                match = re.search(r"tên (.*?) vào", aria_label)
                                if match:
                                    c_user = match.group(1)
                            
                            # Cách 2 (Dự phòng): Tìm thẻ a có font đậm
                            if c_user == "Anonymous":
                                try:
                                    user_tag = c_elem.find_element(By.XPATH, ".//span[contains(@style, 'font-weight: bold')]//a")
                                    c_user = user_tag.text.strip()
                                except: pass

                            if not c_user or c_user == "Anonymous": continue

                            # --- B. LẤY NỘI DUNG TEXT ---
                            c_text = ""
                            try:
                                text_div = c_elem.find_element(By.CSS_SELECTOR, "div[dir='auto']")
                                c_text = text_div.text.strip()
                            except:
                                pass # Comment chỉ có ảnh

                            # --- C. LẤY ẢNH COMMENT ---
                            c_img_url = None
                            try:
                                imgs = c_elem.find_elements(By.TAG_NAME, "img")
                                for img in imgs:
                                    src = img.get_attribute("src")
                                    w = img.get_attribute("width") or 0
                                    # Lọc emoji (thường là png nhỏ hoặc link static)
                                    if src and "emoji" not in src and "static.xx.fbcdn" not in src and int(w) > 50:
                                        c_img_url = src
                                        break
                            except: pass

                            # --- D. LƯU VÀO DATABASE ---
                            if c_text or c_img_url:
                                print(f"    + {c_user}: {c_text[:30]}... [Img: {'Có' if c_img_url else 'Không'}]")
                                
                                # Tạo User
                                insert_user_to_db(c_user)
                                c_user_id = get_user_id(c_user)
                                
                                if c_user_id:
                                    # Lưu Comment vào bảng Comments (idPost, idUser, content)
                                    c_id = insert_comment(db_post_id, c_user_id, c_text)
                                    
                                    # Lưu Ảnh vào bảng CommentPhotos (CommentID, PhotoURL)
                                    if c_img_url and c_id:
                                        insert_comment_photo(c_id, c_img_url)

                        except Exception as inner_e:
                            # Lỗi ở 1 comment thì bỏ qua, chạy tiếp comment sau
                            continue

                except Exception as e:
                    print(f"Error extracting comments: {e}")

            else:
                print(f"Skipping seen post {index+1}")

        except Exception as e:
            print(f"Error processing post {index}: {e}")
        
        index += 1

if __name__ == "__main__":
    crawl_page()