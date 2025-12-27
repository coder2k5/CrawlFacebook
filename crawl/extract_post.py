def _extract_post_text(item):
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

    candidates = []
    for tag in item.find_all(['div', 'span', 'p'], attrs={'dir': 'auto'}):
        t = tag.get_text(separator=' ', strip=True)
        if t and len(t) > 0:
            candidates.append(t)

    if candidates:
        return max(candidates, key=len)

    return item.get_text(separator=' ', strip=True)
