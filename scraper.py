import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup as bs

from crawl.config import EMAIL, PASSWORD
from browser.login import _login
from browser.scroll import _count_needed_scrolls, _scroll
from crawl.extract_html import _extract_html


def extract(page, numOfPost, infinite_scroll=False, scrape_comment=False):

    option = Options()
    option.add_argument("--disable-infobars")
    option.add_argument("start-maximized")
    option.add_argument("--disable-extensions")

    option.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 1
    })

    is_group = "/groups/" in page

    browser = webdriver.Chrome(
        service=Service("./chromedriver"),
        options=option
    )

    browser.set_page_load_timeout(180)
    _login(browser, EMAIL, PASSWORD)
    browser.get(page)
    time.sleep(5)

    lenOfPage = _count_needed_scrolls(browser, infinite_scroll, numOfPost, is_group)
    _scroll(browser, infinite_scroll, lenOfPage)

    bs_data = bs(browser.page_source, 'html.parser')
    result = _extract_html(bs_data, is_group=is_group)

    browser.close()
    return result
