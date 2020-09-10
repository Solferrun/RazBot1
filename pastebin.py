from os import environ
import requests  # see https://2.python-requests.org/en/master/


def make_paste(title, content):
    key = environ['PASTEBIN_TOKEN']
    text = content
    t_title = title

    login_data = {
        'api_dev_key': key,
        'api_user_name': environ['PASTEBIN_USER'],
        'api_user_password': environ['PASTEBIN_PASS']
    }
    data = {
        'api_option': 'paste',
        'api_dev_key': key,
        'api_paste_code': text,
        'api_paste_name': t_title,
        'api_paste_expire_date': '10M',
        'api_user_key': None,
        'api_paste_format': 'text'
    }

    login = requests.post("https://pastebin.com/api/api_login.php", data=login_data)
    print(">> Pastebin login status: ", login.status_code if login.status_code != 200 else "OK/200")
    data['api_user_key'] = login.text

    r = requests.post("https://pastebin.com/api/api_post.php", data=data)
    print(">> Paste send: ", r.status_code if r.status_code != 200 else "OK/200")
    print(">> Paste URL: ", r.text)
    return r.text
