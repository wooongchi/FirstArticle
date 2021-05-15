from session import *
from flask import Flask, jsonify
from urllib.parse import urlencode
from connection import *

app = Flask(__name__)


def get_info_article_status(cafe_session, article_id):
    club_id = get_club_id()
    response = cafe_session.get(REQUEST_URL_SEARCH_ARTICLE.format(cafe_id=club_id, article_id=article_id))
    resp = {
        "article_id": article_id,
        "status_code": response.status_code,
        "response": response.json()
    }
    return resp


# 카페에서 게시글리스트 삭제
def cafe_article_list_delete(cafe_session, article_id):
    # cafe id
    club_id = get_club_id()

    referer = f'https://cafe.naver.com/ArticleList.nhn?search.clubid={club_id}'
    request_headers = {
        'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded', 'Referer': referer}

    form_data_delete_article_list = {}
    form_data_delete_article_list['clubid'] = club_id
    form_data_delete_article_list['menuid'] = ''
    form_data_delete_article_list['boardtype'] = 'L'
    form_data_delete_article_list['page'] = 1
    form_data_delete_article_list['articleid'] = article_id
    form_data_delete_article_list['userDisplay'] = 15

    form_parameters = urlencode(form_data_delete_article_list)
    delete_response = cafe_session.post(REQUEST_URL_DELETE_ARTICLE_LIST, params=form_parameters,
                                        headers=request_headers)

    return jsonify({'meta': {'code': delete_response.status_code, 'message': delete_response.reason}})


def get_article_data(cafe_session, article_id):
    club_id = get_club_id()
    referer = f'https://cafe.naver.com/ca-fe/cafes/{club_id}/articles/{article_id}/modify'

    request_headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'ko-KR,ko;q=0.9',
        'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',
        'Content-Type': 'application/json;charset=UTF-8',
        'Referer': referer,
        "sec-ch-ua": '"Chromium";v="86", "\"Not\\A;Brand";v = "99", "Whale";v = "2"',
        "sec-ch-ua-mobile": "?0",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "x-cafe-product": "pc"
    }
    response = cafe_session.get(REQUEST_URL_EDIT_ARTICLE.format(cafe_id=str(club_id), article_id=article_id),
                                headers=request_headers)

    return response.json()['result']


# 카페에서 게시글 등록
def cafe_article_create(cafe_session, article_data):
    # cafe id
    club_id = get_club_id()
    referer = f'https://cafe.naver.com/ca-fe/cafes/{club_id}/articles/write?boardType=L'
    request_headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'ko-KR,ko;q=0.9',
        'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',
        'Content-Type': 'application/json;charset=UTF-8',
        'Referer': referer,
        "sec-ch-ua": '"Chromium";v="86", "\"Not\\A;Brand";v = "99", "Whale";v = "2"',
        "sec-ch-ua-mobile": "?0",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site"
    }
    content_json = article_data['article']['contentJson']
    menu_id = article_data['selectedMenu']['menu']['menuId']
    subject = article_data['article']['subject']
    open = article_data['options']['open']
    naver_open = article_data['options']['naverOpen']
    external_open = article_data['options']['externalOpen']
    enable_comment = article_data['options']['enableComment']
    enable_scrap = article_data['options']['enableScrap']
    enable_copy = article_data['options']['enableCopy']
    use_auto_source = article_data['options']['useAutoSource']
    ccl_yypes = article_data['options']['cclTypes']
    params = {
        "article": {
            "cafeId": club_id,
            "contentJson": content_json,
            "from": "pc",
            "menuId": menu_id,
            "subject": subject,
            "tagList": [],
            "editorVersion": 4,
            "parentId": 0,
            "open": open,
            "naverOpen": naver_open,
            "externalOpen": external_open,
            "enableComment": enable_comment,
            "enableScrap": enable_scrap,
            "enableCopy": enable_copy,
            "useAutoSource": use_auto_source,
            "cclTypes": ccl_yypes,
            "useCcl": False
        }
    }
    create_response = cafe_session.post(REQUEST_URL_CREATE_ARTICLE.format(cafe_id=str(club_id), menu_id=str(menu_id)),
                                        json=params,
                                        headers=request_headers)

    return jsonify({'meta': {'code': create_response.status_code, 'message': create_response.reason},
                    'data': {'new_article_id': create_response.json()['result']['articleId']}})


def delete_and_create_article_on_naver(article_id):
    try:
        # ------------------------------------------------- 네이버 로그인  -------------------------------------------------
        step_id = get_user_id()
        step_passwd = get_user_password()
        cafe_session = naver_session(step_id, step_passwd)
        # -------------------------------------------- 네이버에서 게시글 정보 수집 --------------------------------------------
        try:
            article_data = get_article_data(cafe_session, article_id)
        except Exception as e:
            print("존재하지 않는 게시글입니다.")
            return jsonify({'meta': {'code': 404, 'message': "article doesn't exist"}})
        # -------------------------------------------- 네이버에서 게시글 삭제 수행 --------------------------------------------
        delete_article_cafe_result = cafe_article_list_delete(cafe_session, article_id)
        if delete_article_cafe_result.status_code != 200:
            print("게시글 삭제에 실패했습니다.")
            return jsonify({'meta': {'code': 403, 'message': "article doesn't deleted"}})
        # ------------------------------------------ 네이버에서 정상삭제되었는지 확인 -------------------------------------------
        # 네이버 카페에 존재하는 게시글만 선별
        # article_check_in_cafe = get_info_article_status(cafe_session, article_id)
        # if article_check_in_cafe['status_code'] != 404:
        #     print("삭제 실패!!!")
        # ------------------------------------------- 네이버에 다시 게시글 등록 -----------------------------------------------
        new_article = cafe_article_create(cafe_session, article_data)
        return jsonify({'meta': {'code': 200, 'message': 'success'},
                        'data': {'new_article_id': new_article.json['data']['new_article_id']}})
    except Exception as e:
        jsonify({'meta': {'code': 400, 'message': 'Bad Request'}})


@app.route('/')
def hello_world():
    result = delete_and_create_article_on_naver(27)
    if result.json['meta']['code'] == 200:
        return str(result.json['data']['new_article_id'])
    else:
        return "실패"


if __name__ == '__main__':
    app.run()
