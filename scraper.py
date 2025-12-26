import argparse
import time
import json
import csv
import math
import re
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup as bs


with open('facebook_credentials.txt') as file:
    EMAIL = file.readline().split('"')[1]
    PASSWORD = file.readline().split('"')[1]


# Import extraction functions from crawl_facebook_thongtin_vang.py
try:
    from crawl_facebook_thongtin_vang import (
        _extract_post_text,
        _extract_link,
        _extract_post_id,
        _extract_image
    )
except ImportError:
    # Fallback: define locally if crawl_facebook_thongtin_vang is not available
    def _extract_post_text(item):
        actualPosts = item.find_all(attrs={"data-testid": "post_message"})
        if actualPosts:
            for posts in actualPosts:
                paragraphs = posts.find_all('p')
                text = ""
                for p in paragraphs:
                    text += p.text
            if text:
                return text
        candidates = [t.get_text(separator=' ', strip=True) for t in item.find_all(['div','span','p'], attrs={'dir':'auto'}) if t.get_text(separator=' ', strip=True)]
        return max(candidates, key=len) if candidates else item.get_text(separator=' ', strip=True)

    def _extract_link(item):
        for a in item.find_all('a', href=True):
            href = a.get('href')
            if href and any(x in href for x in ["/permalink", "/posts/", "/groups/"]):
                return href if href.startswith('http') else f"https://www.facebook.com{href}"
        anchors = item.find_all('a', href=True)
        if anchors:
            href = anchors[0].get('href')
            return href if href and href.startswith('http') else (f"https://www.facebook.com{href}" if href else "")
        return ""

    def _extract_post_id(item):
        for a in item.find_all('a', href=True):
            href = a.get('href')
            if href and any(x in href for x in ["/permalink", "/posts/"]):
                return href if href.startswith('http') else f"https://www.facebook.com{href}"
        return _extract_link(item)

    def _extract_image(item):
        for img in item.find_all('img', src=True):
            src = img.get('src')
            if src and any(x in src for x in ['scontent','cdn','static']):
                return src
        img = item.find('img', src=True)
        return img.get('src') if img else ""


def _extract_post_text(item):
    # Try old selector first
    actualPosts = item.find_all(attrs={"data-testid": "post_message"})
    text = ""
    if actualPosts:
        for posts in actualPosts:
            paragraphs = posts.find_all('p')
            text = ""
            for index in range(0, len(paragraphs)):
                text += paragraphs[index].text
        if text:
            return text

    # Fallback: find visible text blocks used in group posts (dir="auto")
    candidates = []
    for tag in item.find_all(['div', 'span', 'p'], attrs={'dir': 'auto'}):
        t = tag.get_text(separator=' ', strip=True)
        if t and len(t) > 0:
            candidates.append(t)

    if candidates:
        # choose the longest candidate as most likely the post body
        return max(candidates, key=len)

    # Last resort: return all text inside the item
    return item.get_text(separator=' ', strip=True)


def _extract_link(item):
    # Try to find a permalink or post link within the post item
    anchors = item.find_all('a', href=True)
    for a in anchors:
        href = a.get('href')
        if href and ("/permalink" in href or "/posts/" in href or "/groups/" in href):
            if href.startswith('http'):
                return href
            return f"https://www.facebook.com{href}"

    # fallback: first anchor
    if anchors:
        href = anchors[0].get('href')
        if href:
            return href if href.startswith('http') else f"https://www.facebook.com{href}"
    return ""


def _extract_post_id(item):
    # Look for permalink-style hrefs to build a stable post URL
    anchors = item.find_all('a', href=True)
    for a in anchors:
        href = a.get('href')
        if href and ("/permalink" in href or "/posts/" in href):
            return href if href.startswith('http') else f"https://www.facebook.com{href}"

    # fallback to link extractor
    return _extract_link(item)


def _extract_image(item):
    # Find first meaningful image inside the post (scontent or static)
    for img in item.find_all('img', src=True):
        src = img.get('src')
        if not src:
            continue
        # prefer content images
        if 'scontent' in src or 'cdn' in src or 'static' in src:
            return src

    # fallback: any img
    img = item.find('img', src=True)
    if img:
        return img.get('src')
    return ""


def _extract_shares(item):
    postShares = item.find_all(class_="_4vn1")
    shares = ""
    for postShare in postShares:

        x = postShare.string
        if x is not None:
            x = x.split(">", 1)
            shares = x
        else:
            shares = "0"
    return shares


def _extract_comments(item):
    postComments = item.find_all("div", {"class": "_4eek"})
    comments = dict()
    # print(postDict)
    for comment in postComments:
        if comment.find(class_="_6qw4") is None:
            continue

        commenter = comment.find(class_="_6qw4").text
        comments[commenter] = dict()

        comment_text = comment.find("span", class_="_3l3x")

        if comment_text is not None:
            comments[commenter]["text"] = comment_text.text

        comment_link = comment.find(class_="_ns_")
        if comment_link is not None:
            comments[commenter]["link"] = comment_link.get("href")

        comment_pic = comment.find(class_="_2txe")
        if comment_pic is not None:
            comments[commenter]["image"] = comment_pic.find(class_="img").get("src")

        commentList = item.find('ul', {'class': '_7791'})
        if commentList:
            comments = dict()
            comment = commentList.find_all('li')
            if comment:
                for litag in comment:
                    aria = litag.find("div", {"class": "_4eek"})
                    if aria:
                        commenter = aria.find(class_="_6qw4").text
                        comments[commenter] = dict()
                        comment_text = litag.find("span", class_="_3l3x")
                        if comment_text:
                            comments[commenter]["text"] = comment_text.text
                            # print(str(litag)+"\n")

                        comment_link = litag.find(class_="_ns_")
                        if comment_link is not None:
                            comments[commenter]["link"] = comment_link.get("href")

                        comment_pic = litag.find(class_="_2txe")
                        if comment_pic is not None:
                            comments[commenter]["image"] = comment_pic.find(class_="img").get("src")

                        repliesList = litag.find(class_="_2h2j")
                        if repliesList:
                            reply = repliesList.find_all('li')
                            if reply:
                                comments[commenter]['reply'] = dict()
                                for litag2 in reply:
                                    aria2 = litag2.find("div", {"class": "_4efk"})
                                    if aria2:
                                        replier = aria2.find(class_="_6qw4").text
                                        if replier:
                                            comments[commenter]['reply'][replier] = dict()

                                            reply_text = litag2.find("span", class_="_3l3x")
                                            if reply_text:
                                                comments[commenter]['reply'][replier][
                                                    "reply_text"] = reply_text.text

                                            r_link = litag2.find(class_="_ns_")
                                            if r_link is not None:
                                                comments[commenter]['reply']["link"] = r_link.get("href")

                                            r_pic = litag2.find(class_="_2txe")
                                            if r_pic is not None:
                                                comments[commenter]['reply']["image"] = r_pic.find(
                                                    class_="img").get("src")
    return comments


def _extract_reaction(item):
    toolBar = item.find_all(attrs={"role": "toolbar"})

    if not toolBar:  # pretty fun
        return
    reaction = dict()
    for toolBar_child in toolBar[0].children:
        str = toolBar_child['data-testid']
        reaction = str.split("UFI2TopReactions/tooltip_")[1]

        reaction[reaction] = 0

        for toolBar_child_child in toolBar_child.children:

            num = toolBar_child_child['aria-label'].split()[0]

            # fix weird ',' happening in some reaction values
            num = num.replace(',', '.')

            if 'K' in num:
                realNum = float(num[:-1]) * 1000
            else:
                realNum = float(num)

            reaction[reaction] = realNum
    return reaction


def _extract_html(bs_data, is_group=False):

    #Add to check
    with open('./bs.html',"w", encoding="utf-8") as file:
        file.write(str(bs_data.prettify()))

    # Tìm posts khác nhau cho Pages vs Groups
    if is_group:
        # Facebook Groups sử dụng div với role="article"
        posts = bs_data.find_all('div', {'role': 'article'})
        if not posts:
            # Fallback nếu không tìm thấy
            posts = bs_data.find_all(class_="x1yztbdb")
    else:
        # Facebook Pages sử dụng div với class "_5pcr userContentWrapper"
        posts = bs_data.find_all(class_="_5pcr userContentWrapper")
        if not posts:
            # Fallback cho HTML mới
            posts = bs_data.find_all('div', {'role': 'article'})

    postBigDict = list()

    for item in posts:
        try:
            postDict = dict()
            postDict['Post'] = _extract_post_text(item)
            postDict['Link'] = _extract_link(item) or _extract_post_id(item)
            postDict['PostId'] = _extract_post_id(item)
            postDict['Image'] = _extract_image(item)
            postDict['Shares'] = _extract_shares(item)
            postDict['Comments'] = _extract_comments(item) if _extract_comments(item) else {}

            # Bỏ qua posts không có nội dung
            if not postDict['Post'] and not postDict['Image']:
                continue

            #Add to check
            postBigDict.append(postDict)
            with open('./postBigDict.json','w', encoding='utf-8') as file:
                file.write(json.dumps(postBigDict, ensure_ascii=False).encode('utf-8').decode())
        except Exception as e:
            print(f"Error extracting post: {e}")
            continue

    return postBigDict


def _login(browser, email, password):
    browser.get("http://facebook.com")
    browser.maximize_window()
    time.sleep(3)
    
    # Wait for email field to be present
    wait = WebDriverWait(browser, 15)
    email_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
    email_field.send_keys(email)
    
    # Wait for password field and fill it
    password_field = wait.until(EC.presence_of_element_located((By.NAME, "pass")))
    password_field.send_keys(password)
    
    # Wait for login button - try different selectors
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
    time.sleep(5)


def _count_needed_scrolls(browser, infinite_scroll, numOfPost, is_group=False):
    if infinite_scroll:
        lenOfPage = browser.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;"
        )
    else:
        # roughly posts per scroll: groups tend to load fewer posts per scroll
        posts_per_scroll = 4 if is_group else 8
        lenOfPage = max(1, math.ceil(numOfPost / posts_per_scroll))
    print("Number Of Scrolls Needed " + str(lenOfPage))
    return lenOfPage


def _scroll(browser, infinite_scroll, lenOfPage):
    lastCount = -1
    match = False

    while not match:
        if infinite_scroll:
            lastCount = lenOfPage
        else:
            lastCount += 1

        # wait for the browser to load, this time can be changed slightly ~3 seconds with no difference, but 5 seems
        # to be stable enough
        # wait a bit longer to allow XHR-rendered content to appear
        time.sleep(6)

        if infinite_scroll:
            lenOfPage = browser.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return "
                "lenOfPage;")
        else:
            browser.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return "
                "lenOfPage;")

        if lastCount == lenOfPage:
            match = True


def extract(page, numOfPost, infinite_scroll=False, scrape_comment=False):
    option = Options()
    option.add_argument("--disable-infobars")
    option.add_argument("start-maximized")
    option.add_argument("--disable-extensions")

    # Pass the argument 1 to allow and 2 to block
    option.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 1
    })

    # Kiểm tra xem có phải Facebook Group không
    is_group = "/groups/" in page

    # chromedriver should be in the same folder as file
    service = Service("./chromedriver")
    browser = webdriver.Chrome(service=service, options=option)
    browser.set_page_load_timeout(180)  # Tăng timeout lên 180 giây (3 phút)
    _login(browser, EMAIL, PASSWORD)
    browser.get(page)
    time.sleep(5)  # Chờ trang load xong
    lenOfPage = _count_needed_scrolls(browser, infinite_scroll, numOfPost, is_group=is_group)
    _scroll(browser, infinite_scroll, lenOfPage)

    # click on all the comments to scrape them all!
    # TODO: need to add more support for additional second level comments
    # TODO: ie. comment of a comment

    if scrape_comment:
        #first uncollapse collapsed comments
        unCollapseCommentsButtonsXPath = '//a[contains(@class,"_666h")]'
        unCollapseCommentsButtons = browser.find_elements(By.XPATH, unCollapseCommentsButtonsXPath)
        for unCollapseComment in unCollapseCommentsButtons:
            action = webdriver.common.action_chains.ActionChains(browser)
            try:
                # move to where the un collapse on is
                action.move_to_element_with_offset(unCollapseComment, 5, 5)
                action.perform()
                unCollapseComment.click()
            except:
                # do nothing right here
                pass

        #second set comment ranking to show all comments
        rankDropdowns = browser.find_elements(By.CLASS_NAME, '_2pln') #select boxes who have rank dropdowns
        rankXPath = '//div[contains(concat(" ", @class, " "), "uiContextualLayerPositioner") and not(contains(concat(" ", @class, " "), "hidden_elem"))]//div/ul/li/a[@class="_54nc"]/span/span/div[@data-ordering="RANKED_UNFILTERED"]'
        for rankDropdown in rankDropdowns:
            #click to open the filter modal
            action = webdriver.common.action_chains.ActionChains(browser)
            try:
                action.move_to_element_with_offset(rankDropdown, 5, 5)
                action.perform()
                rankDropdown.click()
            except:
                pass

            # if modal is opened filter comments
            ranked_unfiltered = browser.find_elements(By.XPATH, rankXPath) # RANKED_UNFILTERED => (All Comments)
            if len(ranked_unfiltered) > 0:
                try:
                    ranked_unfiltered[0].click()
                except:
                    pass    
        
        moreComments = browser.find_elements(By.XPATH, '//a[@class="_4sxc _42ft"]')
        print("Scrolling through to click on more comments")
        while len(moreComments) != 0:
            for moreComment in moreComments:
                action = webdriver.common.action_chains.ActionChains(browser)
                try:
                    # move to where the comment button is
                    action.move_to_element_with_offset(moreComment, 5, 5)
                    action.perform()
                    moreComment.click()
                except:
                    # do nothing right here
                    pass

            moreComments = browser.find_elements(By.XPATH, '//a[@class="_4sxc _42ft"]')

    # Now that the page is fully scrolled, grab the source code.
    source_data = browser.page_source

    # Throw your source into BeautifulSoup and start parsing!
    bs_data = bs(source_data, 'html.parser')

    # Prefer using the processing logic from crawl_facebook_thongtin_vang if available
    try:
        from crawl_facebook_thongtin_vang import process_loaded_group
        # ensure the page is loaded and then call the processor which uses Selenium driver
        postBigDict = process_loaded_group(browser, max_posts=numOfPost)
    except Exception:
        postBigDict = _extract_html(bs_data, is_group=is_group)
    browser.close()

    return postBigDict


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Facebook Page Scraper")
    required_parser = parser.add_argument_group("required arguments")
    required_parser.add_argument('-page', '-p', help="The Facebook Public Page you want to scrape", required=True)
    required_parser.add_argument('-len', '-l', help="Number of Posts you want to scrape", type=int, required=True)
    optional_parser = parser.add_argument_group("optional arguments")
    optional_parser.add_argument('-infinite', '-i',
                                 help="Scroll until the end of the page (1 = infinite) (Default is 0)", type=int,
                                 default=0)
    optional_parser.add_argument('-usage', '-u', help="What to do with the data: "
                                                      "Print on Screen (PS), "
                                                      "Write to Text File (WT) (Default is WT)", default="CSV")

    optional_parser.add_argument('-comments', '-c', help="Scrape ALL Comments of Posts (y/n) (Default is n). When "
                                                         "enabled for pages where there are a lot of comments it can "
                                                         "take a while", default="No")
    args = parser.parse_args()

    infinite = False
    if args.infinite == 1:
        infinite = True

    scrape_comment = False
    if args.comments == 'y':
        scrape_comment = True

    postBigDict = extract(page=args.page, numOfPost=args.len, infinite_scroll=infinite, scrape_comment=scrape_comment)


    #TODO: rewrite parser
    if args.usage == "WT":
        with open('output.txt', 'w') as file:
            for post in postBigDict:
                file.write(json.dumps(post))  # use json load to recover

    elif args.usage == "CSV":
        with open('data.csv', 'w',) as csvfile:
           writer = csv.writer(csvfile)
           #writer.writerow(['Post', 'Link', 'Image', 'Comments', 'Reaction'])
           writer.writerow(['Post', 'Link', 'Image', 'Comments', 'Shares'])

           for post in postBigDict:
              writer.writerow([post['Post'], post['Link'],post['Image'], post['Comments'], post['Shares']])
              #writer.writerow([post['Post'], post['Link'],post['Image'], post['Comments'], post['Reaction']])

    else:
        for post in postBigDict:
            print(post)

    print("Finished")
