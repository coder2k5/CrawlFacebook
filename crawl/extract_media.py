def _extract_link(item):
    anchors = item.find_all('a', href=True)
    for a in anchors:
        href = a.get('href')
        if href and ("/permalink" in href or "/posts/" in href or "/groups/" in href):
            return href if href.startswith('http') else f"https://www.facebook.com{href}"
    if anchors:
        href = anchors[0].get('href')
        if href:
            return href if href.startswith('http') else f"https://www.facebook.com{href}"
    return ""


def _extract_post_id(item):
    anchors = item.find_all('a', href=True)
    for a in anchors:
        href = a.get('href')
        if href and ("/permalink" in href or "/posts/" in href):
            return href if href.startswith('http') else f"https://www.facebook.com{href}"
    return _extract_link(item)


def _extract_image(item):
    for img in item.find_all('img', src=True):
        src = img.get('src')
        if not src:
            continue
        if 'scontent' in src or 'cdn' in src or 'static' in src:
            return src
    img = item.find('img', src=True)
    return img.get('src') if img else ""
