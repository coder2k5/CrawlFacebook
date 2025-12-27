import json

from crawl.extract_post import _extract_post_text
from crawl.extract_media import _extract_link, _extract_post_id, _extract_image
from crawl.extract_social import _extract_shares, _extract_comments


def _extract_html(bs_data, is_group=False):

    with open('./bs.html',"w", encoding="utf-8") as file:
        file.write(str(bs_data.prettify()))

    if is_group:
        posts = bs_data.find_all('div', {'role': 'article'})
        if not posts:
            posts = bs_data.find_all(class_="x1yztbdb")
    else:
        posts = bs_data.find_all(class_="_5pcr userContentWrapper")
        if not posts:
            posts = bs_data.find_all('div', {'role': 'article'})

    postBigDict = []

    for item in posts:
        try:
            postDict = dict()
            postDict['Post'] = _extract_post_text(item)
            postDict['Link'] = _extract_link(item) or _extract_post_id(item)
            postDict['PostId'] = _extract_post_id(item)
            postDict['Image'] = _extract_image(item)
            postDict['Shares'] = _extract_shares(item)
            postDict['Comments'] = _extract_comments(item) if _extract_comments(item) else {}

            if not postDict['Post'] and not postDict['Image']:
                continue

            postBigDict.append(postDict)

            with open('./postBigDict.json','w', encoding='utf-8') as file:
                file.write(json.dumps(postBigDict, ensure_ascii=False))

        except Exception as e:
            print(f"Error extracting post: {e}")

    return postBigDict
