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

image_folder = r"/var/www/thinkdiff-web/vang247_xyz/image_tintuc/"
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

def click_see_more(driver, element):
    try:
        btns = element.find_elements(By.XPATH, ".//div[@role='button'][contains(., 'Xem thêm') or contains(., 'See more')]")
        for btn in btns:
            if btn.is_displayed():
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(1)
                return True
    except: pass
    return False

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
    print("Starting Login process...")
    browser.get("http://facebook.com")
    browser.maximize_window()
    time.sleep(2)
    try:
        wait = WebDriverWait(browser, 15)
        email_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
        email_field.send_keys(email)
        pass_field = browser.find_element(By.NAME, "pass")
        pass_field.send_keys(password)
        pass_field.send_keys(Keys.ENTER)
        print("Login submitted. Waiting...")
        time.sleep(10)
    except Exception as e:
        print(f"Login error: {e}")

# ==========================================
# 4. MAIN CRAWL FUNCTION (FULL LOGIC)
# ==========================================

def crawl_page():
    # --- SETUP ---
    option = Options()
    option.add_argument("--disable-infobars")
    option.add_argument("start-maximized")
    option.add_argument("--disable-extensions")
    option.add_experimental_option("prefs", {"profile.default_content_setting_values.notifications": 1})

    try:
        service = Service("./chromedriver")
        driver = webdriver.Chrome(service=service, options=option)
    except:
        driver = webdriver.Chrome(options=option)
    
    driver.set_page_load_timeout(180)

    # --- LOGIN ---
    try:
        _login(driver, EMAIL, PASSWORD)
    except Exception as e:
        driver.quit()
        return

    # --- NAVIGATE ---
    group_url = "https://www.facebook.com/groups/385914624891314?sorting_setting=CHRONOLOGICAL"
    print(f"Navigating to: {group_url}")
    driver.get(group_url)
    time.sleep(5)

    crawled_count = 0 
    target_count = 5
    index = 0
    
    while True:
        if crawled_count >= target_count:
            print(f"Đã lấy đủ {target_count} bài viết. Stop.")
            break

        # Tìm Posts
        try:
            post_elements = driver.find_elements(By.XPATH, '//div[@role="feed"]//div[@role="article"]')
            if not post_elements:
                post_elements = driver.find_elements(By.XPATH, '//div[contains(@class, "x1yztbdb")]')
        except: post_elements = []

        print(f"DEBUG: Found {len(post_elements)} posts in DOM.")
        
        if index >= len(post_elements):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            print("Scrolling...")
            time.sleep(5)
            new_elements = driver.find_elements(By.XPATH, '//div[@role="feed"]//div[@role="article"]')
            if len(new_elements) <= index:
                print("No more posts loaded.")
                break
            continue

        post_element = post_elements[index]
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", post_element)
        time.sleep(2)

        try:
            # 1. TRÍCH XUẤT USER & CONTENT
            username_text = "Unknown User"
            try:
                # Tìm thẻ User (Header)
                header_el = post_element.find_element(By.XPATH, ".//strong | .//h2//a | .//h3//a")
                username_text = header_el.text.strip()
            except: pass

            click_see_more(driver, post_element)
            content_text = ""
            try:
                content_el = post_element.find_element(By.XPATH, ".//div[@data-ad-rendering-role='story_message']")
                content_text = content_el.text.strip()
            except:
                try:
                    candidates = post_element.find_elements(By.XPATH, ".//div[@dir='auto']")
                    longest = ""
                    for c in candidates:
                        txt = c.text.strip()
                        if len(txt) > len(longest) and txt != username_text and "Bình luận" not in txt:
                            longest = txt
                    content_text = longest
                except: pass
            
            if not content_text: content_text = "No content"

            # 2. INSERT POST
            post_id_hash = generate_post_id(username_text, content_text)
            
            if post_id_hash not in seen_posts:
                seen_posts.add(post_id_hash)
                crawled_count += 1
                
                print(f"\n--- Processing Post {crawled_count}/{target_count} ---")
                print(f"User: {username_text}")
                print(f"Content: {content_text[:50]}...")
                
                insert_user_to_db(username_text)
                user_id = get_user_id(username_text) or 0
                
                provinces_id = get_provinces_id_from_title(content_text)
                district_id = get_district_id_from_title(content_text)
                
                db_post_id = insert_into_forumposts(
                    user_id=user_id, group_id=38, title="", content=content_text, 
                    post_time=datetime.now(), ip_posted="", post_latitude=0, post_longitude=0, 
                    time_view=0, district_id=district_id, provinces_id=provinces_id
                )
                
                # Ảnh Post
                try:
                    imgs = post_element.find_elements(By.TAG_NAME, "img")
                    for img in imgs:
                        src = img.get_attribute("src")
                        w = int(img.get_attribute("width") or 0)
                        if src and "https" in src and "emoji" not in src and w > 100:
                            path = download_image(src, os.path.join(image_folder, f"img_{uuid.uuid4()}.jpg"))
                            if path and db_post_id:
                                insert_into_forumphotos(db_post_id, f"[img]{path}[/img]", datetime.now())
                except: pass

                if db_post_id:
                    # 3. XỬ LÝ COMMENT
                    print("--- Bắt đầu xử lý bình luận ---")
                    
                    # B1: Mở panel (Click nút đếm hoặc nút action)
                    open_comments_panel(driver, post_element)

                    # B2: Check Popup
                    comment_container = post_element
                    is_popup = False
                    try:
                        dialog = driver.find_element(By.XPATH, "//div[@role='dialog']")
                        if dialog.is_displayed():
                            print("  -> Popup detected.")
                            comment_container = dialog
                            is_popup = True
                    except: pass

                    # B3: Chuyển sang 'Tất cả bình luận' (Quan trọng!)
                    switch_to_all_comments(driver, comment_container)

                    # B4: Mở rộng
                    expand_all_comments(driver, comment_container)

                    # B5: Quét & Insert
                    all_comments = comment_container.find_elements(By.XPATH, ".//div[@role='article']")
                    print(f"  -> Tìm thấy {len(all_comments)} bình luận.")

                    for c_elem in all_comments:
                        try:
                            # User
                            c_user = ""
                            try:
                                # Tìm thẻ có class đặc biệt của user name hoặc thẻ link
                                user_el = c_elem.find_element(By.XPATH, ".//span[contains(@class, 'xt0psk2')] | .//a[contains(@href, 'user') or contains(@href, 'profile')]//span")
                                c_user = user_el.text.strip()
                            except:
                                # Fallback Aria
                                aria = c_elem.get_attribute("aria-label") or ""
                                if "Bình luận" in aria or "Comment" in aria:
                                    c_user = aria.split(" vào ")[0].replace("Bình luận của ", "").replace("Comment by ", "").replace("Bình luận dưới tên ", "")
                            
                            if not c_user or len(c_user) > 50: 
                                # Thử lấy dòng text đầu tiên (nguy hiểm nhưng cần thiết)
                                lines = c_elem.text.split('\n')
                                if lines: c_user = lines[0]

                            if len(c_user) > 50: continue

                            # Text
                            c_text = ""
                            try:
                                c_text = c_elem.find_element(By.XPATH, ".//div[@dir='auto']").text.strip()
                            except: pass
                            
                            # Image
                            c_img_url = None
                            try:
                                c_imgs = c_elem.find_elements(By.TAG_NAME, "img")
                                for ci in c_imgs:
                                    src = ci.get_attribute("src")
                                    if src and "emoji" not in src and int(ci.get_attribute("width") or 0) > 100:
                                        c_img_url = src
                                        break
                            except: pass

                            if c_text or c_img_url:
                                # print(f"    + {c_user}: {c_text[:15]}...")
                                insert_user_to_db(c_user)
                                c_user_id = get_user_id(c_user)
                                if c_user_id:
                                    c_id = insert_comment(db_post_id, c_user_id, c_text)
                                    if c_img_url and c_id:
                                        insert_comment_photo(c_id, c_img_url)

                        except Exception: continue

                    # Đóng Popup
                    if is_popup:
                        webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                        time.sleep(1)

            else:
                print(f"Skipping seen post.")

        except Exception as e:
            print(f"Error post {index}: {e}")
            import traceback
            traceback.print_exc()
        
        index += 1

if __name__ == "__main__":
    crawl_page()