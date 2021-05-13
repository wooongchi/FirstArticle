import json
from session import *
from flask import Flask, current_app, jsonify, json
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor
from requests_futures.sessions import FuturesSession
from concurrent import futures
from connection import *

app = Flask(__name__)


def get_info_article_status(article_id, club_id, future_session):
    # 프록시 접속
    # proxy_url = get_proxy()
    # time.sleep(0.05)
    pp = future_session.get(REQUEST_URL_SEARCH_ARTICLE.format(cafe_id=club_id, article_id=article_id)  # ,
                            # proxies={"http": proxy_url, "https": proxy_url}
                            )
    # a = pp.result().status_code
    resp = {
        "articleId": article_id,
        "status_code": pp.result().status_code
    }
    # time.sleep(0.05)
    return resp


def cafe_article_list_check(check_article_list_json):
    # log(request, {'message': 'cafeService.cafe_article_list_check is begin!!'})
    article_id_list = check_article_list_json['article_id_list']
    if 'club_id' in check_article_list_json.keys() and check_article_list_json['club_id'] != "":
        club_id = check_article_list_json['club_id']
    else:
        club_id = get_club_id()

    # 제재할 랜덤 스텝 정보 조회 (step_id, step_nickname, step_passwd 반환)
    # random_step_info = random_step(club_id)
    # step_id = random_step_info[0]
    # # step_nickname = random_step_info[1]
    # step_passwd = decode_password(random_step_info[2])
    # step_login_id = random_step_info[3]

    # 카페 세션 생성
    step_id = get_user_id()
    step_passwd = get_user_password()

    cafe_session = naver_session(step_id, step_passwd)
    # future 세션 생성
    future_session = FuturesSession(session=cafe_session)

    # 게시글 수 정의
    # tot_counts = len(article_id_list)
    # exist_article_counts = 0
    # not_exist_article_counts = 0

    exist_article_list = []
    not_exist_article_list = []

    with ThreadPoolExecutor(max_workers=50) as exe:
        future_to_url = {exe.submit(get_info_article_status, article_id, club_id, future_session): article_id for
                         article_id in article_id_list}
        for future in futures.as_completed(future_to_url):
            article_id = future_to_url[future]
            try:
                resp = future.result()
                # 게시글 유무 리스트를 분리해서 담는다.
                if resp["status_code"] == 200:
                    exist_article_list.append(resp["articleId"])
                    # exist_article_counts += 1
                else:
                    not_exist_article_list.append(resp["articleId"])
                    # not_exist_article_counts += 1
            except Exception as exp:
                print("%r generated an exception: %s" % (article_id, exp))

    return jsonify({'meta': {'code': '200', 'message': 'success'},
                    'data': {'exist_article_list': exist_article_list,
                             'not_exist_article_list': not_exist_article_list}})


# 카페에서 게시글리스트 삭제
def cafe_article_list_delete(article_ids):
    # proxy_url = get_proxy()

    string_article_ids = [str(articleid) for articleid in article_ids]
    articleids = ",".join(string_article_ids)
    # cafe id
    club_id = get_club_id()

    # 제재할 랜덤 스텝 정보 조회 (step_id, step_nickname, step_passwd 반환)
    step_id = get_user_id()
    step_passwd = get_user_password()

    cafe_session = naver_session(step_id, step_passwd)

    referer = 'https://cafe.naver.com/ArticleList.nhn?search.clubid=%s' % club_id

    request_headers = {
        'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded', 'Referer': referer}

    form_data_delete_article_list = {}
    form_data_delete_article_list['clubid'] = club_id
    form_data_delete_article_list['menuid'] = ''
    form_data_delete_article_list['boardtype'] = 'L'
    form_data_delete_article_list['page'] = 1
    form_data_delete_article_list['articleid'] = articleids
    form_data_delete_article_list['userDisplay'] = 15

    form_parameters = urlencode(form_data_delete_article_list)
    delete_response = cafe_session.post(REQUEST_URL_DELETE_ARTICLE_LIST, params=form_parameters,
                                        headers=request_headers)

    return jsonify({'meta': {'code': delete_response.status_code, 'message': delete_response.reason},
                    'data': {'step_id': step_id}})


# 카페에서 게시글 등록
def cafe_article_create(article_id):
    # proxy_url = get_proxy()

    # cafe id
    club_id = get_club_id()

    # 제재할 랜덤 스텝 정보 조회 (step_id, step_nickname, step_passwd 반환)
    step_id = get_user_id()
    step_passwd = get_user_password()

    cafe_session = naver_session(step_id, step_passwd)

    referer = 'https://cafe.naver.com/ca-fe/cafes/%s/articles/write?boardType=L' % club_id

    request_headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'ko-KR,ko;q=0.9',
        'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',
        'Content-Type': 'application/json;charset=UTF-8',
        # 'origin': 'https://cafe.naver.com',
        'Referer': referer,
        "sec-ch-ua": '"Chromium";v="86", "\"Not\\A;Brand";v = "99", "Whale";v = "2"',
        "sec-ch-ua-mobile": "?0",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site"
    }
    # params = {
    #     "cafeId": "30446983",
    #     "cclTypes": [],
    #     "contentJson": {"document": {"version": "2.5.2", "theme": "default", "language": "ko-KR", "components": [
    #         {"id": "SE-990774f2-c9b8-471a-a401-40ee49a94ee0", "layout": "default", "value": [
    #             {"id": "SE-47cb29c2-55ec-490d-bca3-ef86b5797753", "nodes": [
    #                 {"id": "SE-9e4c9eb9-5047-4e70-aa98-2a3794a1db62", "value": "잘나오나?", "@ctype": "textNode"}],
    #              "@ctype": "paragraph"}], "@ctype": "text"}]}, "documentId": ""},
    #     "editorVersion": 4,
    #     "enableComment": True,
    #     "enableCopy": False,
    #     "enableScrap": False,
    #     "externalOpen": False,
    #     "from": "pc",
    #     "menuId": 1,
    #     "naverOpen": True,
    #     "open": False,
    #     "parentId": 0,
    #     "subject": "api 테스트",
    #     "tagList": [],
    #     "useAutoSource": False,
    #     "useCcl": False
    # }
    params = {"article": {"cafeId": "30446983",
                          "contentJson": "{\"document\":{\"version\":\"2.5.2\",\"theme\":\"default\",\"language\":\"ko-KR\",\"components\":[{\"id\":\"SE-990774f2-c9b8-471a-a401-40ee49a94ee0\",\"layout\":\"default\",\"value\":[{\"id\":\"SE-47cb29c2-55ec-490d-bca3-ef86b5797753\",\"nodes\":[{\"id\":\"SE-9e4c9eb9-5047-4e70-aa98-2a3794a1db62\",\"value\":\"testtest\",\"@ctype\":\"textNode\"}],\"@ctype\":\"paragraph\"}],\"@ctype\":\"text\"}]},\"documentId\":\"\"}",
                          "from": "pc", "menuId": 1, "subject": "api", "tagList": [], "editorVersion": 4, "parentId": 0,
                          "open": False, "naverOpen": True, "externalOpen": False, "enableComment": True,
                          "enableScrap": False,
                          "enableCopy": False, "useAutoSource": False, "cclTypes": [], "useCcl": False}}

    # form_parameters = urlencode(params)
    create_response = cafe_session.post(REQUEST_URL_CREATE_ARTICLE.format(cafe_id=str(club_id), menu_id='1'),
                                        json=params,
                                        headers=request_headers)

    return jsonify({'meta': {'code': create_response.status_code, 'message': create_response.reason},
                    'data': {'step_id': step_id}})


def delete_article_on_naver(article_ids):
    # check_article_list_json = dict({'article_id_list': article_ids})
    # article_check_in_cafe = cafe_article_list_check(check_article_list_json)
    try:
        # -------------------------------------------- 네이버에서 게시글 삭제 수행 --------------------------------------------
        success_cafe_delete_ids = []
        failed_cafe_delete_ids = []
        if len(article_ids) > 0:
            # tic = perf_counter()
            delete_article_cafe_result = cafe_article_list_delete(article_ids)
            cafe_del_result = delete_article_cafe_result.get_json()
            step_id = str(cafe_del_result['data']['step_id'])
            # toc = perf_counter()
            # time_second = f"[DAL]delete_article [naver delete] time took {toc - tic:0.4f} seconds. "
            # log(request, {'message': time_second + str(article_ids)})

            # ------------------------------------------ 네이버에서 정상삭제되었는지 확인 ------------------------------------------
            # 네이버 카페에 존재하는 게시글만 선별
            # tic = perf_counter()
            check_article_list_json = dict({'article_id_list': article_ids})
            article_check_in_cafe = cafe_article_list_check(check_article_list_json).get_json()
            # toc = perf_counter()
            # time_second = f"[DAL]delete_article [naver check2] time took {toc - tic:0.4f} seconds. "
            # log(request, {'message': time_second + str(article_ids)})

            success_cafe_delete_ids = article_check_in_cafe['data']['not_exist_article_list']
            failed_cafe_delete_ids = article_check_in_cafe['data']['exist_article_list']

        result = jsonify({'meta': {'code': 200, 'message': 'success'},
                          'data': {'success_cafe_delete_ids': success_cafe_delete_ids,
                                   'failed_cafe_delete_ids': failed_cafe_delete_ids,
                                   # 'cafe_not_exist_article_ids': cafe_not_exist_article_ids,
                                   'step_id': step_id}
                          })

        return result
    except Exception as e:
        # error_log(request, 500, {'message': '[DAL]delete_article_on_naver Exception!!'})
        # raise InvalidUsage(traceback.format_exc(), status_code=500)
        jsonify({'meta': {'code': 400, 'message': 'fail'}})


@app.route('/')
def hello_world():
    cafe_article_create(2)
    # delete_article_on_naver([3])
    return 'Hello World!'


if __name__ == '__main__':
    # cafe_article_create(2)
    app.run()
