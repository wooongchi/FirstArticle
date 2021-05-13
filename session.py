import re
import uuid
import requests
import rsa
import lzstring
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


def encrypt(key_str, uid, upw):
    def naver_style_join(l):
        return ''.join([chr(len(s)) + s for s in l])
    sessionkey, keyname, e_str, n_str = key_str.split(',')
    e, n = int(e_str, 16), int(n_str, 16)
    message = naver_style_join([sessionkey, uid, upw]).encode()
    pubkey = rsa.PublicKey(e, n)
    encrypted = rsa.encrypt(message, pubkey)
    return keyname, encrypted.hex()


def encrypt_account(uid, upw):
    key_str = requests.get('https://nid.naver.com/login/ext/keys.nhn').content.decode("utf-8")
    return encrypt(key_str, uid, upw)


def naver_session(nid, npw):
    encnm, encpw = encrypt_account(nid, npw)
    s = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=0.1,
        status_forcelist=[500, 502, 503, 504]
    )
    s.mount('https://', HTTPAdapter(max_retries=retries))
    request_headers = {
        'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36'
    }
    bvsd_uuid = uuid.uuid4()
    encData = '{"a":"%s-4","b":"1.3.4","d":[{"i":"id","b":{"a":["0,%s"]},"d":"%s","e":false,"f":false},{"i":"%s","e":true,"f":false}],"h":"1f","i":{"a":"Mozilla/5.0"}}' % (bvsd_uuid, nid, nid, npw)
    bvsd = '{"uuid":"%s","encData":"%s"}' % (bvsd_uuid, lzstring.LZString.compressToEncodedURIComponent(encData))
    resp = s.post('https://nid.naver.com/nidlogin.login', data={
        'svctype': '0',
        'enctp': '1',
        'encnm': encnm,
        'enc_url': 'http0X0.0000000000001P-10220.0000000.000000www.naver.com',
        'url': 'www.naver.com',
        'smart_level': '1',
        'encpw': encpw,
        'bvsd': bvsd
    }, headers=request_headers)

    finalize_url = re.search(r'location\.replace\("([^"]+)"\)', resp.content.decode("utf-8")).group(1)
    s.get(finalize_url)
    return s


REQUEST_URL_SEARCH_ARTICLE = 'https://apis.naver.com/cafe-web/cafe-articleapi/v2/cafes/{cafe_id}/articles/{article_id}'
REQUEST_URL_DELETE_ARTICLE = 'https://apis.naver.com/cafe-web/cafe2/ArticleDelete.json'
REQUEST_URL_DELETE_ARTICLE_LIST = 'https://cafe.naver.com/ArticleDelete.nhn'
FORM_DATA_DELETE_ARTICLE = {
    'cafeId': '',
    'articleId': ''
}
REQUEST_URL_RESTORE_ARTICLE = 'https://cafe.naver.com/ManageRemoveArticleRestore.nhn'
REQUEST_DATA_RESTORE_ARTICLE = {
    'redirectUrl': '/ManageRemoveArticleList.nhn',
    'search.searchtype': 0,
    'search.page': 1
}
REQUEST_URL_REMOVE_ARTICLE_LIST = 'https://cafe.naver.com/ManageRemoveArticleList.nhn?search.clubid=%s'
REQUEST_URL_SUSPEND_MEMBER = 'https://cafe.naver.com/ManageActivityStopProcess.nhn'
REQUEST_URL_RELEASE_MEMBER = 'https://cafe.naver.com/ManageActivityStopRelease.nhn'
REQUEST_URL_MEMBER_STATUS = 'https://cafe.naver.com/ManageMemberListViewAjax.nhn'
REQUEST_URL_FORCE_EJECT_MEMBER = 'https://cafe.naver.com/ManageSecedePopup.nhn'
REQUEST_URL_SEND_NOTE ='https://note.naver.com/json/write/send/'
REFERER_URL_MOVE_ARTICLE = 'https://cafe.naver.com/ArticleMove.nhn?m=view&clubid=%s&menuid=%s&articleid=%s'
REQUEST_URL_MOVE_ARTICLE = 'https://cafe.naver.com/ArticleMove.nhn'
REQUEST_URL_CREATE_ARTICLE = 'https://apis.naver.com/cafe-web/cafe-editor-api/v1.0/cafes/{cafe_id}/menus/{menu_id}/articles'
