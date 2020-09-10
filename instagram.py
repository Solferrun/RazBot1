from traceback import print_exc
from requests import get
from os import environ

# from re import findall
# from urllib import request

root_url = "https://graph.instagram.com"
user_id = environ['IG_USER_ID']
access_token = environ['IG_TOKEN']


def get_posts():
    try:
        url = f"{root_url}/{user_id}/media?access_token={access_token}&fields=permalink,caption,media_url"

        response = get(url).json()
        posts = response.get('data')

        permalinks = [p.get('permalink') if p.get('permalink') else "" for p in posts]
        post_codes = [p[-12:-1] if p else "" for p in permalinks]
        captions = [p.get('caption').replace('\\n', '\n') if p.get('caption') else "No Caption" for p in posts]
        media_urls = [p.get('media_url') if p.get('media_url') else "No Media URL" for p in posts]
        posts = ({'post_code': a,
                  'caption': b.replace('\\n', '\n'),
                  'media_url': c}
                 for (a, b, c) in zip(post_codes, captions, media_urls))
        # r = get(url)
        # response = r.content.decode('utf8')
        # post_codes = findall("/p\\\\/(.*?)\\\\/", response)
        # captions = findall("caption\":\"(.*?)\",\"media_url", response)
        # media_urls = findall("media_url\":\"(.*?)\",\"id", response)
        # posts = ({'post_code': a,
        #           'caption': b.replace('\\n', '\n'),
        #           'media_url': c.replace('\\', '')}
        #          for (a, b, c) in zip(post_codes, captions, media_urls))
        return posts
    except TypeError:
        return None
    except Exception:
        print_exc()
        return None
