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
import traceback

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
# 1. CONFIGURATION & CREDENTIALS
# ==========================================
EMAIL = ""
PASSWORD = ""
try:
    with open('facebook_credentials.txt', 'r') as file:
        lines = file.readlines()
        if len(lines) >= 2:
            line1 = lines[0].strip()
            line2 = lines[1].strip()
            if '"' in line1:
                EMAIL = line1.split('"')[1]
                PASSWORD = line2.split('"')[1]
            else:
                EMAIL = line1
                PASSWORD = line2
except FileNotFoundError:
    print("Warning: 'facebook_credentials.txt' not found.")

# CẤU HÌNH THƯ MỤC LƯU ẢNH POST
# Lấy đường dẫn thư mục hiện tại chứa file scraper.py
current_dir = os.path.dirname(os.path.abspath(__file__))
post_image_folder = os.path.join(current_dir, "img", "img_posts")

if not os.path.exists(post_image_folder):
    os.makedirs(post_image_folder)

# image_folder = r"/var/www/thinkdiff-web/vang247_xyz/image_tintuc/"

image_folder = os.path.join(current_dir, "img", "img_comments")

if not os.path.exists(image_folder):
    os.makedirs(image_folder)

seen_posts = set()

# ==========================================
# 2. DATABASE FUNCTIONS (GIỮ NGUYÊN)
# ==========================================
def connect_to_database():
    return mysql.connector.connect(
        host="localhost",      
        user='phpmyadmin',
        password='Sonhehe89!',
        database='gold_silver', 
    )

def xoa_dau(txt: str) -> str:
    if not txt: return ""
    BANG_XOA_DAU = str.maketrans(
        "ÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬĐÈÉẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴáàảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ",
        "A"*17 + "D" + "E"*11 + "I"*5 + "O"*17 + "U"*11 + "Y"*5 + "a"*17 + "d" + "e"*11 + "i"*5 + "o"*17 + "u"*11 + "y"*5
    )
    if not unicodedata.is_normalized("NFC", txt):
        txt = unicodedata.normalize("NFC", txt)
    return txt.translate(BANG_XOA_DAU)

def get_provinces_id_from_title(title_text):
    if not title_text: return None
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
    if not title_text: return None
    try:
        connection = connect_to_database()
        cursor = connection.cursor()
        cursor.execute("SELECT DistrictID FROM Districts WHERE LOWER(DistrictName) LIKE LOWER(%s)", ('%' + title_text + '%',))
        result = cursor.fetchone()
        connection.close()
        if result: return result[0]
    except: pass
    return None

def insert_user_to_db(username):
    if not username or username == "Unknown User": return
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
            cursor.execute(insert_query, ("", username, password_hashed, email, 0, 0, 0, 0, 0))
            connection.commit()
    except: pass
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def get_user_id(username):
    try:
        connection = connect_to_database()
        cursor = connection.cursor()
        cursor.execute("SELECT UserID FROM Users WHERE Username = %s", (username,))
        result = cursor.fetchone()
        connection.close()
        return result[0] if result else None
    except: return None

def insert_into_forumposts(user_id, group_id, title, content, post_time, ip_posted, post_latitude, post_longitude, time_view, district_id, provinces_id):
    try:
        connection = connect_to_database()
        cursor = connection.cursor()
        cursor.execute("SELECT PostID FROM ForumPosts WHERE Content = %s LIMIT 1", (content,))
        existing_post = cursor.fetchone()
        if existing_post:
            connection.close()
            return existing_post[0]

        insert_query = """
            INSERT INTO ForumPosts (UserID, GroupID, Title, Content, PostTime, IPPosted, PostLatitude, PostLongitude, UpdatePostAt, timeView, district_id, provinces_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NULL, %s, %s, %s)
        """
        values = (user_id, group_id, title, content, post_time, ip_posted, post_latitude, post_longitude, time_view, district_id, provinces_id)
        cursor.execute(insert_query, values)
        connection.commit()
        post_id = cursor.lastrowid
        connection.close()
        return post_id
    except Exception as e:
        print(f"Error insert post: {e}")
        return None

def insert_into_forumphotos(post_id, photo_url, upload_time):
    try:
        connection = connect_to_database()
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM ForumPhotos WHERE PhotoURL = %s", (photo_url,))
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO ForumPhotos (PostID, PhotoURL, uploadTime) VALUES (%s, %s, %s)", (post_id, photo_url, upload_time))
            connection.commit()
        connection.close()
    except: pass

def insert_comment(post_id, user_id, content):
    try:
        connection = connect_to_database()
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM Comments WHERE idPost = %s AND idUser = %s AND content = %s LIMIT 1", (post_id, user_id, content.strip()))
        if result := cursor.fetchone():
            connection.close()
            return result[0]
        cursor.execute("INSERT INTO Comments (idPost, idUser, content, actionAt) VALUES (%s, %s, %s, NOW())", (post_id, user_id, content.strip()))
        connection.commit()
        cid = cursor.lastrowid
        connection.close()
        return cid
    except: return None

def insert_comment_photo(comment_id, photo_url):
    try:
        local_path = download_image(photo_url, os.path.join(image_folder, f"cmt_{uuid.uuid4()}.jpg"))
        if not local_path: return
        formatted_path = f"[img]{local_path}[/img]"
        connection = connect_to_database()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO CommentPhotos (CommentID, PhotoURL, UploadTime) VALUES (%s, %s, NOW())", (comment_id, formatted_path))
        connection.commit()
        connection.close()
    except: pass

def generate_post_id(username, content):
    unique_string = f"{username}_{content}"
    return hashlib.md5(unique_string.encode()).hexdigest()

def download_image(image_url, save_path):
    try:
        if not image_url: return None
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            with open(save_path, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            return save_path
    except: pass
    return None

# ==========================================
# 3. SELENIUM HELPER FUNCTIONS (CỰC MẠNH)
# ==========================================
def click_see_more(driver, post_element):
    try:
        buttons = post_element.find_elements(
            By.XPATH,
            ".//div[@role='button' and (contains(., 'Xem thêm') or contains(., 'See more'))]"
        )
        for btn in buttons:
            if btn.is_displayed():
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(0.5)
    except:
        pass

def open_comments_panel(driver, post_element):
    """
    Tìm mọi cách để mở panel bình luận:
    1. Click nút Action 'Bình luận'
    2. Click dòng chữ '188 bình luận'
    3. Chuyển filter sang 'Tất cả bình luận'
    """
    has_clicked = False
    
    # 1. Click vào dòng chữ đếm số bình luận (VD: "290 bình luận")
    # Đây là cách hiệu quả nhất để mở comment
    try:
        count_btns = post_element.find_elements(By.XPATH, ".//span[contains(text(), 'bình luận') or contains(text(), 'comment')]")
        # Click cái cuối cùng (thường là dòng tổng kết ở góc phải)
        if count_btns:
            target = count_btns[-1]
            if target.is_displayed():
                driver.execute_script("arguments[0].click();", target)
                # print("  -> Đã click vào dòng đếm bình luận.")
                time.sleep(3)
                has_clicked = True
    except: pass

    # 2. Nếu chưa được, Click nút Action Bar
    if not has_clicked:
        try:
            action_btns = post_element.find_elements(By.XPATH, ".//div[@role='button'][contains(., 'Bình luận') or contains(., 'Comment')]")
            for btn in reversed(action_btns): # Nút action thường ở cuối list
                if btn.is_displayed():
                    driver.execute_script("arguments[0].click();", btn)
                    # print("  -> Đã click nút Action bình luận.")
                    time.sleep(3)
                    has_clicked = True
                    break
        except: pass
    
    return has_clicked

def switch_to_all_comments(driver, container):
    """Chuyển filter từ 'Phù hợp nhất' sang 'Tất cả bình luận'"""
    try:
        # Tìm nút Filter (thường có chữ Phù hợp nhất / Most relevant)
        filter_btn = None
        candidates = container.find_elements(By.XPATH, ".//span[contains(text(), 'Phù hợp nhất') or contains(text(), 'Most relevant')]")
        
        # Lội ngược lên tìm role=button cha
        for cand in candidates:
            try:
                parent = cand.find_element(By.XPATH, "./ancestor::div[@role='button'][1]")
                if parent.is_displayed():
                    filter_btn = parent
                    break
            except: pass
        
        if filter_btn:
            driver.execute_script("arguments[0].click();", filter_btn)
            time.sleep(2)
            
            # Chọn 'Tất cả bình luận' trong Menu vừa hiện ra
            # Menu thường nằm ở cuối body (role=menu hoặc role=menuitem)
            all_comments_opts = driver.find_elements(By.XPATH, "//span[contains(text(), 'Tất cả bình luận') or contains(text(), 'All comments')]")
            for opt in all_comments_opts:
                if opt.is_displayed():
                    driver.execute_script("arguments[0].click();", opt)
                    print("  -> Đã chuyển sang 'Tất cả bình luận'")
                    time.sleep(3)
                    return True
    except: pass
    return False

def expand_all_comments(driver, container_element):
    """Click 'Xem thêm bình luận' (View more comments)"""
    print("  -> Đang quét mở rộng...")
    
    keywords = [
        "Xem thêm bình luận", "View more comments", 
        "Xem các bình luận trước", "View previous comments",
        "Xem tất cả", "View all",
        "phản hồi", "replies", "reply", "trả lời",
    ]
    
    # Tìm mọi thẻ chứa text, không quan tâm cấu trúc
    xpath_query = " | ".join([f".//*[contains(text(), '{kw}')]" for kw in keywords])

    max_retries = 10 
    for _ in range(max_retries):
        try:
            # Tìm tất cả các thẻ chứa text này
            elements = container_element.find_elements(By.XPATH, xpath_query)
            if not elements: break
            
            clicked_any = False
            for el in elements:
                try:
                    if el.is_displayed():
                        # Trick: Click chính nó, hoặc click cha nó nếu nó là span
                        driver.execute_script("arguments[0].click();", el)
                        time.sleep(1)
                        clicked_any = True
                except: continue
            
            if not clicked_any: break
        except: break

def _login(browser, email, password):
    """
    Hàm login được lấy nguyên văn logic từ scraper.py
    (Đã cập nhật thêm trường hợp nút Log in là div)
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
    
    # Wait for login button - try different selectors (robust logic)
    try:
        # 1. Try ID first (older Facebook version)
        login_button = wait.until(EC.element_to_be_clickable((By.ID, 'loginbutton')))
    except:
        try:
            # 2. Try button with name='login'
            login_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@name="login"]')))
        except:
            try:
                # 3. Try any button type='submit'
                login_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]')))
            except:
                # 4. [MỚI] Try div role='button' chứa text 'Log in' (trường hợp mới thêm)
                login_button = wait.until(EC.element_to_be_clickable((
                    By.XPATH, 
                    "//div[@role='button'][.//span[contains(text(), 'Log in')]]"
                )))
    
    login_button.click()
    print("Login button clicked. Waiting for redirection...")
    time.sleep(10) # Chờ load sau login

def scroll_inside_popup(driver, popup_element):
    """
    Scroll thông minh trong Popup:
    - Duyệt qua TOÀN BỘ các thẻ div.
    - Tìm thẻ nào có khả năng cuộn (scrollHeight > clientHeight).
    - CHỌN THẺ CÓ SCROLLHEIGHT LỚN NHẤT (Đây chính là container chứa comment).
    - Cuộn thẻ đó xuống đáy.
    """
    print("  -> 📜 Đang cuộn comment trong Popup...")
    
    max_scroll_attempts = 15 
    
    for i in range(max_scroll_attempts):
        # Dùng JS để tìm đúng thẻ div "bự" nhất để cuộn
        scrolled = driver.execute_script("""
            var popup = arguments[0];
            var divs = popup.getElementsByTagName('div');
            var targetDiv = null;
            var maxScrollHeight = 0;

            for (var i = 0; i < divs.length; i++) {
                var d = divs[i];
                
                // Điều kiện:
                // 1. Có nội dung ẩn (scrollHeight > clientHeight)
                // 2. Chiều cao hiển thị đủ lớn (> 100px) để tránh mấy cái nút/icon
                // 3. Không phải thanh cuộn ảo (data-thumb)
                if (d.scrollHeight > d.clientHeight && d.clientHeight > 100 && !d.getAttribute('data-thumb')) {
                    
                    // Logic mới: So sánh để tìm thằng có nội dung dài nhất
                    if (d.scrollHeight > maxScrollHeight) {
                        maxScrollHeight = d.scrollHeight;
                        targetDiv = d;
                    }
                }
            }

            if (targetDiv) {
                // Scroll mượt hơn một chút thay vì set thẳng tắp
                targetDiv.scrollTop = targetDiv.scrollHeight;
                return true;
            }
            return false;
        """, popup_element)
        
        # Nếu JS không tìm thấy (hiếm khi xảy ra với logic mới), dùng phím END
        if not scrolled:
            try:
                actions = ActionChains(driver)
                actions.move_to_element(popup_element).click().send_keys(Keys.END).perform()
                time.sleep(0.5)
            except: pass

        time.sleep(2.5) # Tăng time sleep lên chút để Facebook kịp tải Ajax

        # Kết hợp mở rộng comment
        expand_all_comments(driver, popup_element)
    
    print("  -> ✅ Đã cuộn xong popup.")


# ==========================================
# 1. HÀM TÁCH RIÊNG: XỬ LÝ COMMENT
# ==========================================

def crawl_comments(driver, post_element, db_post_id):
    print("--- Bắt đầu xử lý bình luận ---")
    
    # B1: Mở panel
    has_opened = open_comments_panel(driver, post_element)
    
    # Chờ popup render
    if has_opened:
        time.sleep(3) 

    # B2: Xác định Container
    comment_container = post_element 
    is_popup = False
    
    try:
        # Tìm Dialog đang hiển thị
        dialogs = driver.find_elements(By.XPATH, "//div[@role='dialog']")
        for dialog in dialogs:
            if dialog.is_displayed():
                print("  -> 🟢 Đã bắt được Popup Dialog!")
                comment_container = dialog
                is_popup = True
                break
    except: pass

    # B3: Chuyển sang 'Tất cả bình luận'
    switch_to_all_comments(driver, comment_container)

    # B4: Mở rộng các bình luận
    if is_popup:
        # Gọi hàm scroll mới viết
        scroll_inside_popup(driver, comment_container)
    else:
        # Nếu không phải popup (hiển thị ngay trên feed), scroll trang chính nhẹ một chút
        driver.execute_script("window.scrollBy(0, 300);")
        time.sleep(1)
        expand_all_comments(driver, comment_container)

    # B5: Quét & Insert Database
    # Lọc kỹ để không lấy nhầm text của bài post gốc
    all_comments = comment_container.find_elements(By.XPATH, ".//div[@role='article'][.//div[@dir='auto']]")
    
    if len(all_comments) <= 1:
        all_comments = comment_container.find_elements(By.XPATH, ".//div[@aria-label and contains(@class, 'x1r8uery')]")

    print(f"  -> Tìm thấy {len(all_comments)} bình luận.")

    count_inserted = 0
    for c_elem in all_comments:
        try:
            # --- Lấy nội dung text ---
            c_text = ""
            try:
                text_div = c_elem.find_element(By.XPATH, ".//div[@dir='auto']")
                c_text = text_div.text.strip()
            except: 
                c_text = c_elem.text.strip()
            
            # Bỏ qua nếu text giống hệt bài post
            if len(c_text) > 20 and c_text in post_element.text:
                continue

            # --- Lấy tên User ---
            c_user = ""
            try:
                user_el = c_elem.find_element(By.XPATH, ".//span[contains(@class, 'xt0psk2')] | .//a[contains(@href, '/user/') or contains(@href, 'profile.php')]//span")
                c_user = user_el.text.strip()
            except:
                aria = c_elem.get_attribute("aria-label") or ""
                if "Bình luận" in aria or "Comment" in aria:
                    c_user = re.sub(r'^(Bình luận của|Comment by|Bình luận dưới tên)\s+', '', aria).split(" vào ")[0]
            
            if not c_user and c_text:
                lines = c_elem.text.split('\n')
                if lines: c_user = lines[0]

            if not c_user or len(c_user) > 50: continue 

            # --- Lấy ảnh comment ---
            c_img_url = None
            try:
                c_imgs = c_elem.find_elements(By.TAG_NAME, "img")
                for ci in c_imgs:
                    width = int(ci.get_attribute("width") or 0)
                    height = int(ci.get_attribute("height") or 0)
                    src = ci.get_attribute("src")
                    if src and "emoji" not in src and (width > 50 or height > 50):
                        c_img_url = src
                        break
            except: pass

            # --- Insert vào Database ---
            if c_text or c_img_url:
                insert_user_to_db(c_user)
                c_user_id = get_user_id(c_user)
                if c_user_id:
                    c_id = insert_comment(db_post_id, c_user_id, c_text)
                    if c_img_url and c_id:
                        insert_comment_photo(c_id, c_img_url)
                    count_inserted += 1

        except Exception: continue
            
    print(f"  -> Đã lưu {count_inserted} bình luận vào DB.")

    # ==========================================
    # PHẦN SỬA LỖI ĐÓNG POPUP (QUAN TRỌNG)
    # ==========================================
    if is_popup:
        print("  -> Đang đóng Popup...")
        # 1. Cố gắng click vào nút đóng (Close Button)
        try:
            # XPath tìm nút đóng dựa trên HTML bạn cung cấp
            close_btn = driver.find_element(By.XPATH, "//div[@role='dialog']//div[@aria-label='Close'][@role='button']")
            driver.execute_script("arguments[0].click();", close_btn)
            time.sleep(0.5)
        except:
            # Fallback: Nếu không tìm thấy nút, nhấn ESC
            try:
                webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            except: pass

        # 2. CHỜ CHO ĐẾN KHI POPUP BIẾN MẤT HẲN (BẮT BUỘC)
        # Nếu không có đoạn này, code chạy tiếp sẽ thấy dialog cũ và lấy lại comment cũ
        try:
            WebDriverWait(driver, 5).until(
                EC.invisibility_of_element_located((By.XPATH, "//div[@role='dialog']"))
            )
            print("  -> 🟢 Popup đã đóng hoàn toàn.")
        except TimeoutException:
            print("  -> 🔴 Cảnh báo: Popup kẹt! Thử nhấn ESC lần cuối.")
            webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(2)

# ==========================================
# 1. HÀM XỬ LÝ 1 BÀI VIẾT (CRAWL_POST)
# ==========================================

def crawl_post(driver, story_el, seen_posts):
    try:
        # --- 1. Scroll và Click xem thêm ---
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});",
            story_el
        )
        time.sleep(1.5)
        click_see_more(driver, story_el)

        # --- 2. Lấy Text (Giữ nguyên) ---
        text = ""
        for _ in range(8):
            text = story_el.text.strip()
            if len(text) >= 10:
                break
            time.sleep(1)

        if not text or len(text) < 10:
            print("  -> Skip: story_message chưa có text")
            return False

        # Chống trùng
        post_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
        if post_hash in seen_posts:
            print("  -> Skip: trùng bài")
            return False

        seen_posts.add(post_hash)

        # ===== DEBUG IN FULL =====
        print("\n================ POST =================")
        print(text)
        print("======================================\n")

        # --- 3. Insert Post vào DB (Giữ nguyên) ---
        username = "Facebook User"
        insert_user_to_db(username)
        user_id = get_user_id(username)

        post_time = datetime.now()
        post_id = insert_into_forumposts(
            user_id=user_id,
            group_id=1,
            title=text[:150],
            content=text,
            post_time=post_time,
            ip_posted="127.0.0.1",
            post_latitude=None,
            post_longitude=None,
            time_view=0,
            district_id=None,
            provinces_id=get_provinces_id_from_title(text)
        )

        if not post_id:
            print("  -> ❌ Không insert được post")
            return False

        print(f"  -> ✅ Insert PostID = {post_id}")

        # ====================================================
        # [SỬA LẠI] 4. LẤY ẢNH CỦA BÀI POST & TẢI VỀ
        # ====================================================
        try:
            # BƯỚC QUAN TRỌNG: Leo lên tìm thẻ cha bao trùm cả bài viết (Container)
            # Vì ảnh nằm NGOÀI story_el (text), nên phải đứng từ Container mới nhìn thấy ảnh
            post_container = None
            try:
                # Cách chuẩn: Tìm thẻ div có role='article' bao quanh story_el
                post_container = story_el.find_element(By.XPATH, "./ancestor::div[@role='article'][1]")
            except:
                try:
                    # Cách dự phòng: Leo lên 5-6 cấp cha (nếu Facebook đổi cấu trúc)
                    post_container = story_el.find_element(By.XPATH, "./../../../../..")
                except: pass
            
            # Nếu không tìm được container thì dùng tạm story_el (dù khả năng cao là xịt)
            search_scope = post_container if post_container else story_el

            # Tìm tất cả thẻ img trong phạm vi Container
            post_imgs = search_scope.find_elements(By.TAG_NAME, "img")
            
            valid_img_url = None
            
            for img in post_imgs:
                try:
                    # Lấy kích thước thực tế
                    width = int(img.get_attribute("width") or 0)
                    height = int(img.get_attribute("height") or 0)
                    src = img.get_attribute("src")
                    
                    # LOGIC LỌC ẢNH:
                    # 1. Có src và không phải emoji
                    # 2. Width > 150 (Ảnh trong HTML bạn gửi width=526 -> Thỏa mãn)
                    # 3. Loại bỏ Avatar (thường nằm trong thẻ post nhưng kích thước nhỏ hoặc vuông 40x40)
                    if src and "emoji" not in src and width > 150:
                        
                        # Kiểm tra kỹ hơn: Bỏ qua ảnh avatar user (thường width=height)
                        # Ảnh post thường hình chữ nhật hoặc size lớn hẳn
                        if width < 100 and height < 100: 
                            continue

                        valid_img_url = src
                        print(f"  -> 📸 Phát hiện ảnh Post (W:{width}): {src[:50]}...")
                        break 
                except: continue
            
            # Tải ảnh và Lưu DB
            if valid_img_url:
                file_name = f"post_{post_id}_{uuid.uuid4()}.jpg"
                save_path = os.path.join(post_image_folder, file_name)
                
                downloaded_path = download_image(valid_img_url, save_path)
                
                if downloaded_path:
                    print(f"  -> Đã tải ảnh về: {downloaded_path}")
                    # Insert vào DB
                    insert_into_forumphotos(post_id, valid_img_url, datetime.now()) # Lưu URL gốc
                    # Hoặc lưu đường dẫn local:
                    # insert_into_forumphotos(post_id, f"[img]{save_path}[/img]", datetime.now())

        except Exception as e:
            print(f"  -> Lỗi lấy ảnh post: {e}")

        # =========================
        # CRAWL COMMENT NGAY SAU POST
        # =========================
        post_article = None
        
        # Thử nhiều cách để tìm thẻ bao ngoài (Container) chứa cả nút Like/Comment
        xpaths_to_try = [
            "./ancestor::div[@role='article'][1]",       # Cách cũ (chuẩn)
            "./ancestor::div[@aria-posinset][1]",        # Cách tìm theo feed index
            "./ancestor::div[contains(@class, 'x1yztbdb')][1]", # Class bao ngoài phổ biến mới
            "./../../../../.."                           # Cách "cục súc": Leo lên 5 cấp cha
        ]

        for xpath in xpaths_to_try:
            try:
                post_article = story_el.find_element(By.XPATH, xpath)
                if post_article:
                    break
            except:
                continue
        
        if post_article:
            crawl_comments(driver, post_article, post_id)
        else:
            print("  -> ⚠️ Cảnh báo: Không tìm thấy thẻ bao bài viết (post container), bỏ qua comment.")


        return True
    except StaleElementReferenceException:
        print("  -> Skip: stale element")
        return False
    except Exception as e:
        print("❌ crawl_post error:", e)
        return False


# ===========================
# 2. HÀM CHÍNH (CRAWL_PAGE) 
# ===========================

def crawl_page():
    option = Options()
    option.add_argument("--disable-infobars")
    option.add_argument("start-maximized")
    option.add_argument("--disable-extensions")
    option.add_experimental_option(
        "prefs", {"profile.default_content_setting_values.notifications": 1}
    )

    try:
        driver = webdriver.Chrome(service=Service("./chromedriver"), options=option)
    except:
        driver = webdriver.Chrome(options=option)

    driver.set_page_load_timeout(180)

    # ===== LOGIN =====
    _login(driver, EMAIL, PASSWORD)

    group_url = "https://www.facebook.com/groups/385914624891314?sorting_setting=CHRONOLOGICAL"
    print("Navigating:", group_url)
    driver.get(group_url)

    # Chờ render ban đầu
    time.sleep(10)

    seen_posts = set()
    crawled_count = 0
    target_count = 5
    scroll_round = 0

    while crawled_count < target_count:
        # 👉 LẤY TRỰC TIẾP STORY_MESSAGE
        story_elements = driver.find_elements(
            By.XPATH,
            "//div[@data-ad-rendering-role='story_message']"
        )

        print(f"DEBUG: Found {len(story_elements)} story_message in round {scroll_round}")

        for story in story_elements:
            if crawled_count >= target_count:
                break

            is_new = crawl_post(driver, story, seen_posts)

            if is_new:
                crawled_count += 1
                print(f"✅ Progress {crawled_count}/{target_count}")

        # ===== SCROLL NHẸ SAU KHI QUÉT XONG =====
        scroll_round += 1
        print(f"↘ Đang scroll lần {scroll_round} để tìm bài mới...")


        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        time.sleep(10)

        # Chống scroll vô hạn
        if scroll_round >= 100:
            print(f"⛔ Đã scroll {scroll_round} lần mà không tìm đủ bài. Dừng để tránh lặp vô hạn.")
            break

    print(f"🎉 DONE crawl_page. Tổng bài lấy được: {crawled_count}")

if __name__ == "__main__":
    crawl_page()