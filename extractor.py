# extractor.py
import json
from bs4 import BeautifulSoup as bs

def extract_post_text(item):
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
        return max(candidates, key=len)

    # Last resort
    return item.get_text(separator=' ', strip=True)

def extract_link(item):
    anchors = item.find_all('a', href=True)
    for a in anchors:
        href = a.get('href')
        if href and ("/permalink" in href or "/posts/" in href or "/groups/" in href):
            if href.startswith('http'):
                return href
            return f"https://www.facebook.com{href}"
    
    if anchors:
        href = anchors[0].get('href')
        if href:
            return href if href.startswith('http') else f"https://www.facebook.com{href}"
    return ""

def extract_post_id(item):
    anchors = item.find_all('a', href=True)
    for a in anchors:
        href = a.get('href')
        if href and ("/permalink" in href or "/posts/" in href):
            return href if href.startswith('http') else f"https://www.facebook.com{href}"
    return extract_link(item)

def extract_image(item):
    for img in item.find_all('img', src=True):
        src = img.get('src')
        if not src: continue
        if 'scontent' in src or 'cdn' in src or 'static' in src:
            return src
    
    img = item.find('img', src=True)
    if img:
        return img.get('src')
    return ""

def extract_shares(item):
    postShares = item.find_all(class_="_4vn1")
    shares = "0"
    for postShare in postShares:
        x = postShare.string
        if x is not None:
            x = x.split(">", 1)
            shares = x
    return shares

def extract_comments(item):
    """
    Hàm mới: Lấy comment dựa trên role='article' và aria-label từ HTML bạn cung cấp.
    """
    comments = []
    
    # Tìm tất cả các div đóng vai trò là comment
    # HTML bạn gửi: <div aria-label="Bình luận dưới tên..." role="article" ...>
    comment_blocks = item.find_all('div', attrs={'role': 'article'})
    
    for comment_node in comment_blocks:
        try:
            c_data = {}
            
            # 1. Lấy tên người bình luận và Link Profile
            # Thường tên người nằm trong thẻ <a> có href, hoặc trong aria-label
            aria_label = comment_node.get('aria-label', '')
            if "Bình luận dưới tên" not in aria_label:
                # Có thể là reply hoặc dạng khác, vẫn cố lấy
                pass

            # Tìm thẻ a chứa link profile (thường nằm ở phần đầu comment)
            # Trong HTML bạn gửi: <a role="link" href="/groups/...">Đỗ Ngọc Trâm</a>
            author_tag = comment_node.find('a', attrs={'role': 'link'}, href=True)
            
            if author_tag:
                c_data['name'] = author_tag.get_text(strip=True)
                c_data['link'] = author_tag['href']
                if c_data['link'].startswith('/'):
                    c_data['link'] = "https://www.facebook.com" + c_data['link']
            else:
                c_data['name'] = "Unknown"
                c_data['link'] = ""

            # 2. Lấy nội dung bình luận
            # HTML bạn gửi: <div dir="auto" style="text-align: start;">Sắp 4k6 luôn ời</div>
            # Logic: Tìm thẻ div có dir="auto" nằm bên trong comment_node
            # Lưu ý: Tên người cũng có dir="auto", nên phải cẩn thận.
            
            text_candidates = comment_node.find_all('div', attrs={'dir': 'auto'})
            comment_text = ""
            
            # Thường text comment là cái dài nhất hoặc cái nằm sau cùng
            for cand in text_candidates:
                txt = cand.get_text(strip=True)
                # Loại bỏ nếu text trùng với tên người dùng
                if txt != c_data['name']:
                    comment_text = txt
                    break # Lấy cái đầu tiên khác tên người dùng thường là nội dung
            
            c_data['text'] = comment_text

            # 3. Lấy ảnh trong comment (nếu có)
            img_tag = comment_node.find('a', attrs={'role': 'link'}) 
            # (Phần này phức tạp vì ảnh comment FB giấu kỹ, tạm thời lấy text trước)
            
            if c_data['text']:
                comments.append(c_data)
                
        except Exception as e:
            continue

    return comments

    # Logic lấy comment giữ nguyên từ code gốc
    postComments = item.find_all("div", {"class": "_4eek"})
    comments = dict()
    for comment in postComments:
        if comment.find(class_="_6qw4") is None:
            continue
        commenter = comment.find(class_="_6qw4").text
        comments[commenter] = dict()
        
        comment_text = comment.find("span", class_="_3l3x")
        if comment_text: comments[commenter]["text"] = comment_text.text
        
        comment_link = comment.find(class_="_ns_")
        if comment_link: comments[commenter]["link"] = comment_link.get("href")
        
        comment_pic = comment.find(class_="_2txe")
        if comment_pic: comments[commenter]["image"] = comment_pic.find(class_="img").get("src")

        # Nested comments logic (rút gọn cho hiển thị, logic core vẫn giữ)
        # ... (Phần xử lý reply comment giữ nguyên logic cũ nếu cần thiết)
    
    # Logic xử lý danh sách comment type 2
    commentList = item.find('ul', {'class': '_7791'})
    if commentList:
        # Tái khởi tạo comments nếu tìm thấy list kiểu mới (theo logic cũ của bạn)
        comments = dict()
        list_items = commentList.find_all('li')
        if list_items:
            for litag in list_items:
                aria = litag.find("div", {"class": "_4eek"})
                if aria:
                    commenter = aria.find(class_="_6qw4").text
                    comments[commenter] = dict()
                    comment_text = litag.find("span", class_="_3l3x")
                    if comment_text: comments[commenter]["text"] = comment_text.text
                    # ... (Các phần lấy link/image reply tương tự code gốc)
    return comments

def parse_html_content(html_source, is_group=False):
    """
    Hàm chính để parse HTML lấy được từ Selenium.
    """
    bs_data = bs(html_source, 'html.parser')
    
    # Debug: Save raw HTML
    with open('./bs.html', "w", encoding="utf-8") as file:
        file.write(str(bs_data.prettify()))

    # Selector strategy
    if is_group:
        posts = bs_data.find_all('div', {'role': 'article'})
        if not posts:
            posts = bs_data.find_all(class_="x1yztbdb")
    else:
        posts = bs_data.find_all(class_="_5pcr userContentWrapper")
        if not posts:
            posts = bs_data.find_all('div', {'role': 'article'})



    postBigDict = list()

    for item in posts:
        try:
            postDict = dict()
            postDict['Post'] = extract_post_text(item)
            postDict['Link'] = extract_link(item) or extract_post_id(item)
            postDict['PostId'] = extract_post_id(item)
            postDict['Image'] = extract_image(item)
            postDict['Shares'] = extract_shares(item)
            # postDict['Comments'] = extract_comments(item) # Tạm tắt hoặc bật tùy nhu cầu

            if not postDict['Post'] and not postDict['Image']:
                continue

            postBigDict.append(postDict)
            
            # Debug: Save progress
            with open('./postBigDict.json', 'w', encoding='utf-8') as file:
                file.write(json.dumps(postBigDict, ensure_ascii=False))
        except Exception as e:
            print(f"Error extracting post: {e}")
            continue

    return postBigDict