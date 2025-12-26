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
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
# reuse login logic from scraper.py
from scraper import _login, EMAIL, PASSWORD
import hashlib
import unicodedata
from urllib.parse import urlparse
from PIL import Image  # Ensure Pillow is installed (pip install Pillow)
import uuid

seen_posts = set()

# Define the folder path for saving images
image_folder = r"/var/www/thinkdiff-web/vang247_xyz/image_tintuc/"

# Create the folder if it doesn't exist
if not os.path.exists(image_folder):
    os.makedirs(image_folder)

service = FirefoxService("/snap/bin/firefox.geckodriver")
options = webdriver.FirefoxOptions()
options = FirefoxOptions()
options.profile = webdriver.FirefoxProfile()

# options.add_argument("--disable-blink-features=AutomationControlled")
# options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
# options.add_argument("--headless")
# options.add_argument("--no-sandbox")
driver = webdriver.Firefox(options=options, service=service)
driver.maximize_window()

def get_provinces_id_from_title(title_text):
    provinces_mapping = {
        'An Giang': 1,
        'Bà Rịa - Vũng Tàu': 2,
        'Bạc Liêu': 3,
        'Bắc Kạn': 4,
        'Bắc Giang': 5,
        'Bắc Ninh': 6,
        'Bến Tre': 7,
        'Bình Dương': 8,
        'Bình Định': 9,
        'Bình Phước': 10,
        'Bình Thuận': 11,
        'Cà Mau': 12,
        'Cao Bằng': 13,
        'Cần Thơ': 14,
        'Đà Nẵng': 15,
        'Đắk Lắk': 16,
        'Đắk Nông': 17,
        'Điện Biên': 18,
        'Đồng Nai': 19,
        'Đồng Tháp': 20,
        'Gia Lai': 21,
        'Hà Giang': 22,
        'Hà Nam': 23,
        'Hà Nội': 24,
        'Hà Tĩnh': 25,
        'Hải Dương': 26,
        'Hải Phòng': 27,
        'Hòa Bình': 28,
        'Hồ Chí Minh': 29,
        'HCM': 29,
        'Hậu Giang': 30,
        'Hưng Yên': 31,
        'Khánh Hòa': 32,
        'Kiên Giang': 33,
        'Kon Tum': 34,
        'Lai Châu': 35,
        'Lào Cai': 36,
        'Lạng Sơn': 37,
        'Lâm Đồng': 38,
        'Long An': 39,
        'Nam Định': 40,
        'Nghệ An': 41,
        'Ninh Bình': 42,
        'Ninh Thuận': 43,
        'Phú Thọ': 44,
        'Phú Yên': 45,
        'Quảng Bình': 46,
        'Quảng Nam': 47,
        'Quảng Ngãi': 48,
        'Quảng Ninh': 49,
        'Quảng Trị': 50,
        'Sóc Trăng': 51,
        'Sơn La': 52,
        'Tây Ninh': 53,
        'Thái Bình': 54,
        'Thái Nguyên': 55,
        'Thanh Hóa': 56,
        'Thừa Thiên Huế': 57,
        'Tiền Giang': 58,
        'Trà Vinh': 59,
        'Tuyên Quang': 60,
        'Vĩnh Long': 61,
        'Vĩnh Phúc': 62,
        'Yên Bái': 63
    }
    
    title_text_lower = title_text.lower()  # Convert title to lowercase for case-insensitive comparison
    
    for province_name, provinces_id in provinces_mapping.items():
        if province_name.lower() in title_text_lower:  # Convert province name to lowercase as well
            return provinces_id
    
    # Default value if no match is found
    return None # You can set it to a default or NULL value

def get_district_id_from_title(title_text):
    # Extract district name from title and compare it to the districts in the database
    connection = connect_to_database()
    cursor = connection.cursor()
    
    # Query to get DistrictID based on the district name (case-insensitive comparison)
    cursor.execute("SELECT DistrictID FROM districts WHERE LOWER(DistrictName) LIKE LOWER(%s)", ('%' + title_text + '%',))
    result = cursor.fetchone()
    
    if result:
        district_id = result[0]
    else:
        district_id = None  # No match found
    
    return district_id

def normalize_content(content):
    # Normalize Unicode to NFC (e.g., combine diacritics)
    normalized = unicodedata.normalize('NFC', content)
    # Trim leading/trailing whitespace
    normalized = normalized.strip()
    # Replace multiple spaces/newlines with a single space
    normalized = ' '.join(normalized.split())
    return normalized

BANG_XOA_DAU = str.maketrans(
    "ÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬĐÈÉẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴáàảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ",
    "A"*17 + "D" + "E"*11 + "I"*5 + "O"*17 + "U"*11 + "Y"*5 + "a"*17 + "d" + "e"*11 + "i"*5 + "o"*17 + "u"*11 + "y"*5
)

def xoa_dau(txt: str) -> str:
    if not unicodedata.is_normalized("NFC", txt):
        txt = unicodedata.normalize("NFC", txt)
    return txt.translate(BANG_XOA_DAU)

def connect_to_database():
    return mysql.connector.connect(
        host="localhost",      
        user='phpmyadmin',
            password='Sonhehe89!',
            database='gold_silver', 
    )
    
def insert_user_to_db(username):
    # Clean username: Remove spaces and special characters
    cleaned_username = re.sub(r'\W+', '', username)
    cleaned_username = xoa_dau(cleaned_username)

    # Generate hashed password
    password_plain = "123456"
    password_hashed = bcrypt.hashpw(password_plain.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Generate email
    email = f"{cleaned_username}@gmail.com"

    # Define other fields
    phone = None
    gender = None
    birth_date = None
    birth_time = None
    province_id = None
    is_anonymous = 0
    registration_ip = None
    last_login_ip = None
    last_activity_time = None
    is_logged_in = None
    role = 0
    avatar_link = None
    bio = None
    current_add = None
    birth_place = None
    confirmed = 0
    blocked = 0
    create_at = None
    coin = 0

    # Database connection
    try:
        connection = connect_to_database()
        cursor = connection.cursor()

        # Check if user already exists
        check_query = "SELECT COUNT(*) FROM Users WHERE Username = %s"
        cursor.execute(check_query, (username,))
        user_exists = cursor.fetchone()[0] > 0

        if user_exists:
            print(f"User {username} already exists. Skipping insertion.")
        else:
            # Insert user into database
            insert_query = """
                INSERT INTO Users (Fullname, Username, Password, Email, Phone, Gender, BirthDate, BirthTime, ProvinceID, IsAnonymous, RegistrationIP, LastLoginIP, LastActivityTime, IsLoggedIn, Role, avatarLink, Bio, CurrentAdd, BirthPlace, Confirmed, Blocked, Create_at, coin)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            data = ("", username, password_hashed, email, phone, gender, birth_date, birth_time, province_id, is_anonymous, registration_ip, last_login_ip, last_activity_time, is_logged_in, role, avatar_link, bio, current_add, birth_place, confirmed, blocked, create_at, coin)

            cursor.execute(insert_query, data)
            connection.commit()
            print(f"User {username} inserted successfully.")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def check_post_exists(content):
    """Check if a post with the same content already exists in ForumPosts."""
    connection = connect_to_database()
    cursor = connection.cursor()
    
    check_query = "SELECT PostID FROM ForumPosts WHERE Content = %s LIMIT 1"
    cursor.execute(check_query, (content,))
    existing_post = cursor.fetchone()
    
    cursor.close()
    connection.close()
    
    return existing_post is not None  # Returns True if post exists, False otherwise


def insert_into_forumposts(user_id, group_id, title, content, post_time, ip_posted, post_latitude, post_longitude, time_view, district_id, provinces_id):
    """Insert data into ForumPosts table and return PostID. Avoid duplicates based on exact Content and truncated cases."""
    connection = connect_to_database()
    cursor = connection.cursor()

    # Check for exact content match
    check_exact_query = "SELECT PostID FROM ForumPosts WHERE Content = %s LIMIT 1"
    cursor.execute(check_exact_query, (content,))
    existing_post = cursor.fetchone()

    if existing_post:
        post_id = existing_post[0]
        cursor.close()
        connection.close()
        return post_id

    # Check for truncated content case where new content ends with '… See more'
    suffix = '… See more'
    if content.endswith(suffix):
        truncated_length = len(content) - len(suffix)
        truncated_content = content[:truncated_length].strip()

        # Escape special characters for LIKE query using default backslash escape
        truncated_escaped = truncated_content.replace('%', '\\%').replace('_', '\\_')
        like_pattern = f"{truncated_escaped}%"

        check_truncated_query = """
            SELECT PostID FROM ForumPosts
            WHERE Content LIKE %s
            LIMIT 1
        """
        cursor.execute(check_truncated_query, (like_pattern,))
        truncated_post = cursor.fetchone()

        if truncated_post:
            post_id = truncated_post[0]
            cursor.close()
            connection.close()
            return post_id

    # Insert new post if no duplicates found
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
    """Insert dữ liệu vào bảng ForumPhotos nếu PhotoURL chưa tồn tại."""
    connection = connect_to_database()
    cursor = connection.cursor()

    # Check if the PhotoURL already exists in the table
    check_query = """
        SELECT COUNT(*) FROM ForumPhotos WHERE PhotoURL = %s
    """
    cursor.execute(check_query, (photo_url,))
    result = cursor.fetchone()

    if result[0] == 0:  # If the PhotoURL does not exist
        insert_query = """
            INSERT INTO ForumPhotos (PostID, PhotoURL, uploadTime)
            VALUES (%s, %s, %s)
        """
        values = (post_id, photo_url, upload_time)
        cursor.execute(insert_query, values)
        connection.commit()
        print("Photo inserted successfully.")
    else:
        print("PhotoURL already exists. Skipping insertion.")

    cursor.close()
    connection.close()
            
def update_forumposts_on_see_more(content_text):
    """Update existing post when 'See More' is expanded."""
    connection = None
    cursor = None
    try:
        connection = connect_to_database()
        cursor = connection.cursor()

        # 1. Find matching post based on content relationship
        suffix = "… See more"
        find_query = """
            SELECT PostID, Content 
            FROM ForumPosts 
            WHERE 
                Content LIKE %s  -- Match posts ending with "… See more"
                AND %s LIKE CONCAT(TRIM(TRAILING %s FROM Content), '%%')
            ORDER BY LENGTH(Content) DESC
            LIMIT 1
        """
        cursor.execute(find_query, (f'%{suffix}', content_text, suffix))
        
        if result := cursor.fetchone():
            post_id, old_content = result
            
            # 2. Verify the new content contains the old content's base text
            base_content = old_content.rsplit(suffix, 1)[0].strip()
            if not content_text.startswith(base_content):
                return False

            # 3. Update post with full content
            update_query = """
                UPDATE ForumPosts 
                SET 
                    Content = %s,
                    UpdatePostAt = NOW(),
                    timeView = timeView + 1  -- Example of counter increment
                WHERE PostID = %s
            """
            cursor.execute(update_query, (content_text, post_id))
            connection.commit()
            return True
            
        return False

    except Exception as e:
        if connection:
            connection.rollback()
        raise RuntimeError(f"Content update failed: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        

def generate_post_id(username, content):
    """Generate a unique identifier for a post based on username and content."""
    unique_string = f"{username}_{content}"
    return hashlib.md5(unique_string.encode()).hexdigest()


def download_image(image_url, save_path):
    """Download an image from a URL and save it to the specified path."""
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

def click_see_more(driver, post_element):
    """Click the 'See more' button in a post if it exists."""
    try:
        # Wait for the "See more" button to be clickable
        see_more_button = WebDriverWait(post_element, 10).until(
            EC.element_to_be_clickable((By.XPATH, ".//div[@role='button' and contains(text(), 'See more')]"))
        )
        # Scroll the button into view and click it
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", see_more_button)
        time.sleep(1)  # Wait for the button to be fully visible
        see_more_button.click()
        time.sleep(2)  # Wait for the content to expand
        return True
    except Exception as e:
        print(f"No 'See more' button found or failed to click: {e}")
        return False
    
def click_comments(driver, post_element):
    """Click the comments span (e.g., '1 comment', '2 comments') if it exists."""
    try:
        # Wait for the comments span to be clickable
        comments_span = WebDriverWait(post_element, 10).until(
            EC.element_to_be_clickable((By.XPATH, 
                ".//span[number(substring-before(text(), ' ')) = number(substring-before(text(), ' ')) "
                "and contains(substring-after(text(), ' '), 'comment')]"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", comments_span)
        comments_span.click()
        time.sleep(2)  # Wait for comments to load
        return True
    except Exception as e:
        print(f"Comments span not found or failed to click: {e}")
        return False

def get_user_id(username):
    """Get UserID from database with error handling"""
    try:
        with connect_to_database() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT UserID FROM Users WHERE Username = %s", 
                    (username,)
                )
                result = cursor.fetchone()
                return result[0] if result else None
    except Exception as e:
        print(f"Database error getting UserID: {str(e)}")
        return None

def find_post_id_by_content(content):
    """Find the most recent PostID for full or truncated content ending with '... See more'."""
    try:
        cleaned_content = content.strip()
        
        # Remove "..." or "…" followed by "See more" if present
        if cleaned_content.endswith("... See more"):
            cleaned_content = cleaned_content.rsplit("... See more", 1)[0].strip()
        elif cleaned_content.endswith("… See more"):
            cleaned_content = cleaned_content.rsplit("… See more", 1)[0].strip()

        # Further: Trim potential partial words (e.g., "vùn" → "vùn")
        # Optionally split and remove the last partial word if needed:
        # cleaned_content = ' '.join(cleaned_content.split()[:-1])

        with connect_to_database() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT PostID FROM Forumposts 
                    WHERE TRIM(Content) LIKE CONCAT(%s, '%%')
                    ORDER BY PostID DESC 
                    LIMIT 1
                """, (cleaned_content,))
                result = cursor.fetchone()
                return result[0] if result else None
    except Exception as e:
        print(f"Database error finding PostID: {str(e)}")
        return None

def insert_comment(post_id, user_id, content):
    """Insert comment into database with duplicate checking and return the inserted comment ID"""
    try:
        cleaned_content = content.strip()
        
        with connect_to_database() as conn:
            with conn.cursor() as cursor:
                # Check for existing comment
                cursor.execute("""
                    SELECT id FROM Comments 
                    WHERE idPost = %s 
                    AND idUser = %s 
                    AND content = %s
                    LIMIT 1
                """, (post_id, user_id, cleaned_content))
                
                existing_comment = cursor.fetchone()
                if existing_comment:
                    print(f"Duplicate comment skipped: User {user_id} on Post {post_id}")
                    return existing_comment[0]  # Return existing comment ID
                
                # Insert new comment
                cursor.execute("""
                    INSERT INTO Comments (idPost, idUser, content, actionAt)
                    VALUES (%s, %s, %s, NOW())
                """, (post_id, user_id, cleaned_content))
                
                comment_id = cursor.lastrowid  # Get the last inserted ID
                
                conn.commit()
                return comment_id
                
    except Exception as e:
        print(f"Database error inserting comment: {str(e)}")
        return None  # Return None in case of an error

def download_comment_image(photo_url, save_folder=r"/home/son/Documents/landinvest2/nhatot_batdongsan.com.vn/"):
    """Download the comment image, convert .jfif to .jpeg, and save it in its original format (except .jfif)."""
    if not photo_url:
        return None
    
    try:
        # Ensure the folder exists
        os.makedirs(save_folder, exist_ok=True)

        # Send a GET request to download the image
        response = requests.get(photo_url, stream=True)
        
        # If the response is successful (status code 200)
        if response.status_code == 200:
            # Extract the filename from the URL (keep original extension)
            file_name = os.path.basename(urlparse(photo_url).path)
            
            # Clean the filename (in case there are query parameters)
            file_name = file_name.split("?")[0]  # Remove any URL parameters

            # Check if the file has an extension
            if not os.path.splitext(file_name)[1]:
                file_name += ".jpeg"  # Add .jpeg if no extension is found

            file_path = os.path.join(save_folder, file_name)

            # Save the image content to the specified file path
            with open(file_path, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)

            # Check if the downloaded file is a .jfif image and convert to .jpeg
            if file_path.lower().endswith(".jfif"):
                try:
                    # Open the .jfif image and save it as .jpeg
                    with Image.open(file_path) as img:
                        jpeg_path = file_path.rsplit('.', 1)[0] + ".jpeg"  # Change the extension to .jpeg
                        img.convert("RGB").save(jpeg_path, "JPEG")
                        os.remove(file_path)  # Remove the original .jfif file
                        return jpeg_path  # Return the path to the converted .jpeg image
                except Exception as e:
                    print(f"Error converting .jfif to .jpeg: {e}")
                    return None
            
            return file_path  # Return the original file path if not a .jfif image
        
        else:
            print(f"Failed to download image: {photo_url}")
            return None

    except Exception as e:
        print(f"Error downloading image: {str(e)}")
        return None


def insert_comment_photo(comment_id, photo_url):
    """Insert photo associated with a comment into CommentPhotos table with local image storage."""
    if not comment_id or not photo_url:
        print("Invalid comment ID or photo URL. Skipping insert.")
        return None

    try:
        # Download image and get local path
        local_photo_path = download_comment_image(photo_url)
        if not local_photo_path:
            return None  # Skip if download fails
        
        formatted_photo_path = f"[img]{local_photo_path}[/img]"

        with connect_to_database() as conn:
            with conn.cursor() as cursor:
                # Check for existing comment photo
                cursor.execute("""
                    SELECT PhotoID FROM CommentPhotos 
                    WHERE CommentID = %s AND PhotoURL = %s 
                    LIMIT 1
                """, (comment_id, formatted_photo_path))
                
                existing_photo = cursor.fetchone()
                if existing_photo:
                    print(f"Duplicate comment photo skipped: Comment {comment_id}, Photo {formatted_photo_path}")
                    return existing_photo[0]  # Return existing PhotoID
                
                # Insert new comment photo
                cursor.execute("""
                    INSERT INTO CommentPhotos (CommentID, PhotoURL, UploadTime)
                    VALUES (%s, %s, NOW())
                """, (comment_id, formatted_photo_path))
                
                photo_id = cursor.lastrowid  # Get the last inserted PhotoID
                
                conn.commit()
                return photo_id
                
    except Exception as e:
        print(f"Database error inserting comment photo: {str(e)}")
        return None  # Return None in case of an error


def crawl_page():
    # Use shared login routine from scraper.py (falls back to local method on failure)
    try:
        _login(driver, EMAIL, PASSWORD)
    except Exception as e:
        print(f"Login via scraper._login failed: {e}. Falling back to local login.")
        try:
            driver.get("https://www.facebook.com")
            time.sleep(5)
            email_field = driver.find_element(By.ID, "email")
            password_field = driver.find_element(By.ID, "pass")
            email_field.send_keys(EMAIL)
            time.sleep(1)
            password_field.send_keys(PASSWORD)
            time.sleep(1)
            password_field.send_keys(Keys.RETURN)
            time.sleep(10)
        except Exception as e2:
            print(f"Fallback login also failed: {e2}")

    group_url = "https://www.facebook.com/groups/385914624891314"
    driver.get(group_url)
    time.sleep(5)

    last_height = driver.execute_script("return document.body.scrollHeight")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    attempts = 0
    max_attempts = 3  # Stop after unsuccessful scrolls
    scroll_pause_time = 2
    
    # while attempts < max_attempts:
    #     # Scroll to the bottom
    #     driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
    #     # Add a short randomized delay to mimic human behavior
    #     time.sleep(2)
        
    #     # Calculate new scroll height and compare
    #     new_height = driver.execute_script("return document.body.scrollHeight")
    #     if new_height == last_height:
    #         attempts += 1
    #     else:
    #         attempts = 0  # Reset attempts if new content loaded
    #     last_height = new_height

    # Parse the page source with BeautifulSoup
    # soup = BeautifulSoup(driver.page_source, "html.parser")
    # posts = soup.find_all("div", class_="x1yztbdb x1n2onr6 xh8yej3 x1ja2u2z")

    # Iterate through posts using Selenium to interact with "See more" buttons
    index = 0
    while True:
        # post_elements = WebDriverWait(driver, 10).until(
        #     EC.presence_of_all_elements_located((By.XPATH, '//div[@class="x1yztbdb x1n2onr6 xh8yej3 x1ja2u2z"]'))
        # )
        post_elements = driver.find_elements(By.XPATH, '"xdj266r x14z9mp xat24cr x1lziwak x1vvkbs')
        print(f"Total posts found: {len(post_elements)}")
        if index >= len(post_elements):
            print("finished crawling!")
            break
        
        post_element = post_elements[index]
        driver.execute_script("arguments[0].scrollIntoView();", post_element)
        time.sleep(scroll_pause_time)  
        try: 
            post = BeautifulSoup(post_element.get_attribute("outerHTML"), "html.parser")
            child_div = None
            try:
                child_div = WebDriverWait(post_element, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-ad-rendering-role="story_message"]'))
                )
                # child_div = post_element.find_element(By.CSS_SELECTOR, 'div[data-ad-rendering-role="story_message"]')   
            except Exception as e:
                print("Child div not found:", e)
            
            date_time = datetime.now()
            # print(f"Post HTML: {post}")
            content_text = ""
            username_text = ""
            content_text_seemore = ""
            content_text_compare = ""
            # h3_username_wrapper = post.find("h3", id=":r4d:")
            # if h3_username_wrapper.text:
            username = post.find("span", class_="html-span xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x1hl2dhg x16tdsg8 x1vvkbs") 
            username2 = post.find("span", class_="html-span xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x1hl2dhg x16tdsg8 x1vvkbs x65f84u")
            if username:
                username_text = username.text.strip()
            elif username2:
                username2_text = username2.find("a")
                username_text = username2_text.text if username2_text else "anonymous"
            else:
                username_text = "anonymous"
            content_wrapper = post.find("div", attrs={"data-ad-rendering-role": "story_message"}, class_="html-div xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd")
            content_wrapper2 = post.find("div", class_="xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs x126k92a")
            if content_wrapper:
                content_special = content_wrapper.find("div", class_="xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs")
                content_normal1 = content_wrapper.find("div", class_="xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs x126k92a")
                content_normal2 = content_wrapper.find_all("div", class_="x11i5rnm xat24cr x1mh8g0r x1vvkbs xtlvy1s x126k92a")
                content_abnormal = content_wrapper.find_all("div", class_="html-div xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd")
                if content_special:
                    content_text = content_special.text.strip()
                elif content_normal1 or content_normal2:
                    if content_normal1:
                        content_text = content_normal1.text.strip() 
                    if content_normal2:
                        for div in content_normal2:
                            content_text += " " + div.text.strip()
                elif content_abnormal:
                    for div2 in content_abnormal:
                        content_text += " " + div2.text.strip()
                else:
                    content_text = "no content"
            elif content_wrapper2:
                content_text = content_wrapper2.text.strip()
            else:
                content_text = "no content"
            
            if child_div:
                if click_see_more(driver, post_element=child_div):
                    print("click see more success")
                    post_after = BeautifulSoup(post_element.get_attribute("outerHTML"), "html.parser")
                    # print(f"postafter HTML: {post_after}")
                    content_wrapper_seemore = post_after.find("div", attrs={"data-ad-rendering-role": "story_message"}, class_="html-div xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd")
                    content_wrapper2_seemore = post_after.find("div", class_="xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs x126k92a")
                    if content_wrapper_seemore:
                        content_special_seemore = content_wrapper_seemore.find("div", class_="xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs")
                        content_normal1_seemore = content_wrapper_seemore.find("div", class_="xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs x126k92a")
                        content_normal2_seemore = content_wrapper_seemore.find_all("div", class_="x11i5rnm xat24cr x1mh8g0r x1vvkbs xtlvy1s x126k92a")
                        content_abnormal_seemore = content_wrapper_seemore.find_all("div", class_="html-div xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd")
                        if content_special_seemore:
                            content_text_seemore = content_special_seemore.text.strip()
                        elif content_normal1_seemore or content_normal2_seemore:
                            if content_normal1_seemore:
                                content_text_seemore = content_normal1_seemore.text.strip() 
                            if content_normal2_seemore:
                                for div in content_normal2_seemore:
                                    content_text_seemore += " " + div.text.strip()
                        elif content_abnormal_seemore:
                            for div2 in content_abnormal_seemore:
                                content_text_seemore += " " + div2.text.strip()
                        else:
                            content_text_seemore = "no content"
                    elif content_wrapper2_seemore:
                        content_text_seemore = content_wrapper2_seemore.text.strip()
                    else:
                        content_text_seemore = "no content"

                    print(f"content_text_seemore: {content_text_seemore}")
                    
                
            image_links = []
            image_wrapper = post.find("div", class_="html-div xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x1n2onr6")
            if image_wrapper:
                image_miniwrappers = image_wrapper.find_all("div", class_="x10l6tqk x13vifvy")
                if image_miniwrappers:
                    for image_miniwrapper in image_miniwrappers:
                        image = image_miniwrapper.find("img")
                        if image:
                            image_link = image.get("src", "")
                            if image_link:  # Only append if the link is not empty
                                image_links.append(image_link)
            
            # Download images and replace links with local paths
            for idx, image_link in enumerate(image_links):
                image_name = f"image_{index + 1}_{idx + 1}.jpg"  # Unique name for each image
                image_path = os.path.join(image_folder, image_name)
                if download_image(image_link, image_path):
                    image_links[idx] = f"[img]{image_path}[/img]"
                else:
                    image_links[idx] = "[img]Failed to download image[/img]"
                        
            post_id = generate_post_id(username=username_text, content=content_text)
            if post_id not in seen_posts:
                seen_posts.add(post_id) # Mark this post as seen
                print(f"Post: {index + 1}")
                print(f"Username: {username_text}")
                print(f"Content: {content_text}")
                print(f"Date and Time: {date_time}")
                if image_links:
                    if len(image_links) == 1:
                        print(f"Image Link: {image_links[0]}")
                    else:
                        print("Image Links:")
                        for link in image_links:
                            print(link)
                else:
                    print("No images found.")
                insert_user_to_db(username_text)
                
                connection = connect_to_database()
                cursor = connection.cursor()

                # Lấy UserID từ bảng Users dựa trên Username
                cursor.execute("SELECT UserID FROM Users WHERE Username = %s LIMIT 1", (username_text,))
                user_result = cursor.fetchone()

                if user_result:
                    user_id = user_result[0]
                else:
                    print(f"Không tìm thấy UserID cho Username '{username_text}'. Gán giá trị user_id = 0.")
                    user_id = 0  # Gán giá trị mặc định nếu không tìm thấy UserID

                group_id = 38

                # if check_post_exists(content_text):
                #     print(f"Skipping duplicate post: '{content_text}'")
                #     continue  # Skip to next post if duplicate exists
                provinces_id = get_provinces_id_from_title(title_text=content_text)
                district_id = get_district_id_from_title(title_text=content_text)
                
                # Insert dữ liệu vào bảng ForumPosts và lấy PostID
                posts_id = insert_into_forumposts(
                    user_id=user_id,
                    group_id=group_id,
                    title="",
                    content=content_text,
                    post_time=date_time,
                    ip_posted="",
                    post_latitude=0,
                    post_longitude=0,
                    time_view=0,
                    district_id=district_id,
                    provinces_id=provinces_id
                )
                
                update_forumposts_on_see_more(content_text=content_text_seemore)
                
                for image_link in image_links:
                    insert_into_forumphotos(
                        post_id=posts_id,
                        photo_url=image_link,
                        upload_time=datetime.now()
                    )
                
            
            if click_comments(driver, post_element=post_element):
                print("click comments success")
                try:
                    close_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, '//div[@aria-label="Close" and @role="button"]'))
                    )
                except Exception as e:
                    print(f"An unexpected error occurred: {e}")
                    
                post_comment_selenium = driver.find_element(By.XPATH, "//div[@role='dialog' and contains(@class, 'x1n2onr6') and contains(@class, 'x1ja2u2z') and contains(@class, 'x1afcbsf') and contains(@class, 'xdt5ytf') and contains(@class, 'x1a2a7pz') and contains(@class, 'x71s49j') and contains(@class, 'x1qjc9v5') and contains(@class, 'xrjkcco') and contains(@class, 'x58fqnu') and contains(@class, 'x1mh14rs') and contains(@class, 'xfkwgsy') and contains(@class, 'x78zum5') and contains(@class, 'x1plvlek') and contains(@class, 'xryxfnj') and contains(@class, 'xcatxm7') and contains(@class, 'xrgej4m') and contains(@class, 'xh8yej3')]")
                post_comment = BeautifulSoup(post_comment_selenium.get_attribute("outerHTML"), "html.parser")
                content_wrapper_compare = post_comment.find("div", attrs={"data-ad-rendering-role": "story_message"}, class_="html-div xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd")
                content_wrapper2_compare = post_comment.find("div", class_="xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs x126k92a")
                if content_wrapper_compare:
                    content_special_compare = content_wrapper_compare.find("div", class_="xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs")
                    content_normal1_compare = content_wrapper_compare.find("div", class_="xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs x126k92a")
                    content_normal2_compare = content_wrapper_compare.find_all("div", class_="x11i5rnm xat24cr x1mh8g0r x1vvkbs xtlvy1s x126k92a")
                    content_abnormal_compare = content_wrapper_compare.find_all("div", class_="html-div xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd")
                    if content_special_compare:
                        content_text_compare = content_special_compare.text.strip()
                    elif content_normal1_compare or content_normal2_compare:
                        if content_normal1_compare:
                            content_text_compare = content_normal1_compare.text.strip() 
                        if content_normal2_compare:
                            for div in content_normal2_compare:
                                content_text_compare += " " + div.text.strip()
                    elif content_abnormal_compare:
                        for div2 in content_abnormal_compare:
                            content_text_compare += " " + div2.text.strip()
                    else:
                        content_text_compare = "no content"
                elif content_wrapper2_compare:
                    content_text_compare = content_wrapper2_compare.text.strip()
                else:
                    content_text_compare = "no content"
                
                print(f"Content compare: {content_text_compare}")
                
                try:
                    comment_wrapper = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, '//div[@class="html-div x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x1gslohp"]'))
                    )
                    # comment_wrapper = driver.find_element(By.XPATH, '//div[@class="html-div x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x1gslohp"]')
                except Exception as e:
                    print(f"comment_wrapper not found: {e}")
                soup3 = BeautifulSoup(comment_wrapper.get_attribute("outerHTML"), "html.parser")
                # print(f"soup3: {soup3}")
                comments = soup3.find_all("div", class_="x16hk5td x12rz0ws")
                if comments:
                    for comment in comments:
                        username_wrapper_comment = comment.find("span", class_="x3nfvp2")
                        username_comment = username_wrapper_comment.text.strip() if username_wrapper_comment else "anonymous"
                        comment_text_wrapper = comment.find("div", class_="xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs")
                        if comment_text_wrapper:
                            comment_link = comment_text_wrapper.find("a")
                            if comment_link:
                                continue
                            else:
                                comment_text = comment_text_wrapper.text.strip()
                        else:
                            comment_text = ""
                        
                        print(f"Username comment: {username_comment}")
                        insert_user_to_db(username_comment)
                        print(f"Content comment: {comment_text}")
                        print("--------------------------------")
                        
                        user_id = get_user_id(username_comment)
                        if not user_id:
                            print(f"Failed to get UserID for {username_comment}")
                            continue
                        
                        post_id = find_post_id_by_content(content_text_compare)
                        if not post_id:
                            print(f"Failed to find PostID for content: {content_text_compare}...")
                            continue
                        
                        comment_id = insert_comment(post_id, user_id, comment_text)
                        if comment_id:
                            print(f"Inserted comment by {username_comment}")
                        else:
                            print(f"Failed to insert comment by {username_comment}")
                            
                        comment_img = None
                        comment_image_wrapper = comment.find("div", class_="x78zum5 xv55zj0 x1vvkbs")
                        if comment_image_wrapper:
                            comment_image = comment_image_wrapper.find("img")
                            if comment_image:
                                comment_img = comment_image.get("src")
                        
                        if comment_img:
                            comment_photo_id = insert_comment_photo(comment_id, comment_img)
                            if comment_photo_id:
                                print(f"Inserted/Found comment photo with ID: {comment_photo_id}, {comment_img}")
                        
                    time.sleep(2)   
                    close_button.click()
                else:
                    print("No comments found")
                    close_button.click()
                    
            else:
                print("click comments failed")
            
            index += 1 
            print(f"total post elements: {len(post_elements)}")
            if index >= len(post_elements)-6 and index <= len(post_elements)-1:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                print("Scroll to bottom!")
                time.sleep(4)
            
        except Exception as e:
            print(e)
    

if __name__ == "__main__":
    crawl_page()
