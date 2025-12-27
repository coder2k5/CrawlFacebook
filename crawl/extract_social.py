def _extract_shares(item):
    postShares = item.find_all(class_="_4vn1")
    for postShare in postShares:
        if postShare.string:
            return postShare.string
    return "0"


def _extract_comments(item):
    postComments = item.find_all("div", {"class": "_4eek"})
    comments = dict()

    for comment in postComments:
        if comment.find(class_="_6qw4") is None:
            continue

        commenter = comment.find(class_="_6qw4").text
        comments[commenter] = dict()

        comment_text = comment.find("span", class_="_3l3x")
        if comment_text:
            comments[commenter]["text"] = comment_text.text

    return comments


def _extract_reaction(item):
    toolBar = item.find_all(attrs={"role": "toolbar"})
    if not toolBar:
        return
