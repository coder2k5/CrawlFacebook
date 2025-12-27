import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def _login(browser, email, password):
    browser.get("http://facebook.com")
    browser.maximize_window()
    time.sleep(3)

    wait = WebDriverWait(browser, 15)
    wait.until(EC.presence_of_element_located((By.NAME, "email"))).send_keys(email)
    wait.until(EC.presence_of_element_located((By.NAME, "pass"))).send_keys(password)

    try:
        login_button = wait.until(EC.element_to_be_clickable((By.ID, 'loginbutton')))
    except:
        login_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]')))

    login_button.click()
    time.sleep(5)
