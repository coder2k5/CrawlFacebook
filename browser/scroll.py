import time
import math


def _count_needed_scrolls(browser, infinite_scroll, numOfPost, is_group=False):
    if infinite_scroll:
        return browser.execute_script("return document.body.scrollHeight")
    posts_per_scroll = 4 if is_group else 8
    return max(1, math.ceil(numOfPost / posts_per_scroll))


def _scroll(browser, infinite_scroll, lenOfPage):
    lastCount = -1
    match = False

    while not match:
        if infinite_scroll:
            lastCount = lenOfPage
        else:
            lastCount += 1

        time.sleep(6)
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")

        if lastCount == lenOfPage:
            match = True
