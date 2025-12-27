# FILE: crawler.py
import time
import math
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

def init_driver():
    option = Options()
    option.add_argument("--disable-infobars")
    option.add_argument("start-maximized")
    option.add_argument("--disable-extensions")
    # Tắt thông báo để tránh che khuất nút bấm
    option.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 1
    })
    
    # Lưu ý: Cập nhật đường dẫn chromedriver của bạn nếu cần
    service = Service("./chromedriver") 
    browser = webdriver.Chrome(service=service, options=option)
    browser.set_page_load_timeout(180)
    return browser

def login_facebook(browser, email, password):
    browser.get("http://facebook.com")
    time.sleep(3)
    
    wait = WebDriverWait(browser, 15)
    try:
        email_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
        email_field.send_keys(email)
        
        password_field = wait.until(EC.presence_of_element_located((By.NAME, "pass")))
        password_field.send_keys(password)
        
        # Thử nhiều loại nút đăng nhập khác nhau
        try:
            login_btn = wait.until(EC.element_to_be_clickable((By.ID, 'loginbutton')))
        except:
            try:
                login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@name="login"]')))
            except:
                login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]')))
        
        login_btn.click()
        time.sleep(5)
    except Exception as e:
        print(f"Lỗi đăng nhập: {e}")

def count_needed_scrolls(browser, infinite_scroll, num_of_post, is_group=False):
    if infinite_scroll:
        # Nếu vô tận, scroll thử 1 lần để lấy chiều dài
        lenOfPage = browser.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;"
        )
    else:
        # Nhóm thường load ít bài hơn mỗi lần scroll
        posts_per_scroll = 4 if is_group else 6
        lenOfPage = max(1, math.ceil(num_of_post / posts_per_scroll))
    
    print(f"Cần cuộn trang khoảng: {lenOfPage} lần")
    return lenOfPage

def scroll_page(browser, infinite_scroll, lenOfPage):
    lastCount = -1
    match = False
    
    current_scrolls = 0

    while not match:
        if infinite_scroll:
            lastCount = lenOfPage
        else:
            lastCount += 1
            current_scrolls += 1

        # Cuộn trang
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        print(f"Đang cuộn... ({current_scrolls}/{lenOfPage})")
        time.sleep(5) # Chờ load nội dung

        if infinite_scroll:
            lenOfPage = browser.execute_script("var lenOfPage=document.body.scrollHeight;return lenOfPage;")
            if lastCount == lenOfPage:
                match = True
        else:
            if current_scrolls >= lenOfPage:
                match = True

def click_element_via_js(browser, element):
    """Hàm phụ trợ: Click bằng Javascript để tránh bị lỗi element not interactable"""
    browser.execute_script("arguments[0].click();", element)

def expand_comments(browser):
    """
    Click 'Xem thêm bình luận' và chuyển sang chế độ 'Tất cả bình luận'.
    """
    print("\n--- BẮT ĐẦU QUY TRÌNH MỞ COMMENT ---")
    
    # BƯỚC 1: Chuyển bộ lọc sang "Tất cả bình luận"
    try:
        # Tìm nút dropdown có chữ "Phù hợp nhất" (Nằm trong div role=button)
        sort_menus = browser.find_elements(By.XPATH, '//span[contains(text(), "Phù hợp nhất")]/ancestor::div[@role="button"]')
        
        for menu in sort_menus:
            try:
                # Click mở menu
                click_element_via_js(browser, menu)
                time.sleep(2)
                
                # Chọn "Tất cả bình luận"
                all_comments_opts = browser.find_elements(By.XPATH, '//span[contains(text(), "Tất cả bình luận")]')
                for opt in all_comments_opts:
                    if opt.is_displayed():
                        click_element_via_js(browser, opt)
                        print("-> Đã chuyển sang chế độ 'Tất cả bình luận'")
                        time.sleep(3) # Chờ load lại trang
                        break
            except:
                continue
    except Exception as e:
        print(f"Không thao tác được bộ lọc comment: {e}")

    # BƯỚC 2: Click nút "Xem thêm bình luận" (Load more)
    print("-> Đang tìm nút 'Xem thêm bình luận'...")
    
    retry_count = 0
    max_retries = 3 # Thử lại 3 lần nếu không thấy nút nào (do mạng lag)
    
    while retry_count < max_retries:
        try:
            # Tìm tất cả các nút có chứa chữ khóa
            buttons = browser.find_elements(By.XPATH, '//div[@role="button"]//span[contains(text(), "Xem thêm") or contains(text(), "Xem các bình luận") or contains(text(), "Hiển thị thêm")]')
            
            # Lọc ra các nút đang hiển thị
            visible_buttons = [btn for btn in buttons if btn.is_displayed()]
            
            if not visible_buttons:
                retry_count += 1
                print(f"   ...Không thấy nút thêm, thử lại lần {retry_count}...")
                time.sleep(2)
                continue
            
            # Reset retry nếu tìm thấy nút
            retry_count = 0
            print(f"-> Tìm thấy {len(visible_buttons)} nút mở rộng. Đang click...")
            
            clicked_any = False
            for btn in visible_buttons:
                try:
                    click_element_via_js(browser, btn)
                    clicked_any = True
                    time.sleep(0.5) # Nghỉ xíu giữa các click
                except:
                    pass
            
            if not clicked_any:
                break
                
            time.sleep(3) # Chờ nội dung mới load ra sau khi click
            
        except Exception as e:
            print(f"Lỗi khi click xem thêm: {e}")
            break
            
    print("--- Đã mở rộng xong comment ---")

def crawl_content(page_url, num_of_post, email, password, infinite_scroll=False, scrape_comment=False):
    browser = init_driver()
    html_source = ""
    is_group = False
    
    try:
        print("Đăng nhập Facebook...")
        login_facebook(browser, email, password)
        
        is_group = "/groups/" in page_url
        print(f"Đang truy cập: {page_url} (Là Group: {is_group})")
        browser.get(page_url)
        time.sleep(5)
        
        # Scroll để load bài viết
        lenOfPage = count_needed_scrolls(browser, infinite_scroll, num_of_post, is_group)
        scroll_page(browser, infinite_scroll, lenOfPage)
        
        # Click mở rộng comment nếu được yêu cầu
        if scrape_comment:
            expand_comments(browser)
        
        # Lấy source HTML cuối cùng
        print("Đang lấy mã nguồn HTML...")
        html_source = browser.page_source
        
    except Exception as e:
        print(f"Crawler Error: {e}")
    finally:
        print("Đóng trình duyệt...")
        browser.quit()
        
    return html_source, is_group