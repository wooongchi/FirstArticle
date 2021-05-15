import time
import timeit
from flask import jsonify
import datetime as pydatetime
from session import *
from connection import *


def crawling_articles(cafe_session, menu_id, min_article_id, target_word, user_id, send_sqs=None):
    club_id = get_club_id()
    # if send_sqs:
    #     send_sqs = send_sqs.replace(' ', '').split(',')
    start_time = timeit.default_timer()  # 시작시간 체크
    print("start : ", start_time)
    # DocumentDB 접속 (게시글 저장을 위한)
    # conn = get_mongo_connection()
    # print("--------> mongodb connection :", timeit.default_timer() - start_time )
    # db = conn.get_database(get_mongo_db_name())  # 데이터베이스 선택
    # collection = 'articles_' + club_id  # club id 기준으로 테이블명 생성
    # collection_articles = db.get_collection(collection)  # 테이블 선택

    # 카페 호출 API 용 URL ( 게시판 지정 조회 URL과 게시판 구분없이 모든 게시글 조회 URL로 구분 )
    if menu_id is None:
        cafe_article_list_url = CAFE_ARTICLE_LIST_ALL_URL.format(club_id=club_id)
    else:
        cafe_article_list_url = CAFE_ARTICLE_LIST_MENU_ID_URL.format(club_id=club_id, menu_id=menu_id)

    page_no = 1  # 페이지 정보

    print("--------> 최근 게시글 가져오기 :", timeit.default_timer() - start_time)

    # 크롤링 시작 게시글 ID 설정 ( 시작 게시글 요청이 없으면 마지막 크롤링 게시글 +100 만큼 수행 )
    max_article_id = min_article_id + 100

    # max_article_id 가 포함된 페이지 부터 min_article_id 까지 크롤링 반복 수행
    while True:
        print("--------> start while :", timeit.default_timer() - start_time)
        articles_list_url = cafe_article_list_url + str(page_no)
        resp = cafe_session.get(articles_list_url)
        print("--------> get article list :", timeit.default_timer() - start_time)
        data = resp.json()
        # 스크래핑 대상 게시글 리스트 추출
        raw_article_list = data['message']['result']['articleList']

        # 카페에서 조회한 게시글 리스트에서 게시글 ID, subject, writer_id 추출
        article_list, article_id_list = parse_article_list(raw_article_list)
        print('article_list: ', article_list)

        # raw_article_list 가 비어 있으면 크롤링 종료
        if not article_list:
            min_article_id = page_top_article_id
            max_article_id = min_article_id + 100
            page_no = 1
            print('새로운 글이 없는 상태')
            time.sleep(10)
            continue
        for article in article_list:
            if article[1].find(target_word) != -1 and article[2] != user_id and article[0] > min_article_id:
                print("찾았다 요놈!")
                return jsonify({'meta': {'code': 200, 'message': 'find word'},
                                'data': {'article_id': article[0]}})
        # 페이지에서 스크랩핑 대상 마지막 articleID 수집
        page_top_article_id = max(article_id_list)
        page_bottom_article_id = min(article_id_list)

        print('max_article_id', max_article_id)
        print('min_article_id: ', min_article_id)
        print('page_top_article_id: ', page_top_article_id)
        print('page_bottom_article_id: ', page_bottom_article_id)

        # TODO 첫번째 페이지의 top articleID 보다 현재 페이지의 top articleID 가 크거나 같으면 다음 페이지 호출
        # TODO 이전 페이지의 bottom articleID 보다 현재 페이지의 bottom articleID 가 크거나 같으면 다음 페이지 호출

        print("--------> filter article list :", timeit.default_timer() - start_time)

        crawling_article_list = between(article_id_list, min_article_id, page_top_article_id)
        print('crawling_article_list: ', crawling_article_list)
        target_count = len(crawling_article_list)
        print('target_count: ', target_count)

        # 페이지의 처음 게시글 번호보다 이전 크롤링 작업의 마지막 게시글 번호보다 작거나 같으면 중지
        if page_top_article_id <= min_article_id:
            print("새로운 글은 있지만 키워드를 포함한 글이 올라오진 않은 상황")
            min_article_id = page_top_article_id
            max_article_id = min_article_id + 100
            page_no = 1
            time.sleep(10)
            continue

        if target_count == 0:
            print('')
            print('There are no articles to crawling !!! Go to next page !!')
            print('--------------------------------------------------------')
        else:
            target_raw_article_list = []
            for article in raw_article_list:
                if article['articleId'] in crawling_article_list:
                    article["_id"] = article['articleId']
                    article["crawling_date"] = str(pydatetime.datetime.now())
                    target_raw_article_list.append(article)
            # 게시글 입력
            # try:
            #     print(target_raw_article_list)
            #     result = collection_articles.insert_many(target_raw_article_list, ordered=False)
            #
            # except pymongo.errors.BulkWriteError as e:
            #     kafka_producers(e.details['writeErrors'])
            #     print(e.details['writeErrors'])
            #     pass

        # 크롤링 대상 게시글 id와 현재 페이지의 마지막 게시글 id의 차이를 구한다.
        gap_between_page_bottom_and_max_article_id = page_bottom_article_id - max_article_id
        print('gap_between_page_bottom_and_max_article_id: ', gap_between_page_bottom_and_max_article_id)

        # 현재 페이지의 마지막 게시글 id 가 수집해야할 게시글 id 보다 200 이상 크면 그 차이를 한페이지 게시글 수인 20으로 나누어 한번에 이동할 페이지를 계산한다.
        # 네이버 API에서 최대로 조회할 수 있는 페이지는 1000페이지이다 그러므로 이동할 페이지가 1000보다 크면 1000페이지로 수정
        if gap_between_page_bottom_and_max_article_id > 200:
            jump_to_page_no = int(round(gap_between_page_bottom_and_max_article_id / 25, -1))
            page_no += jump_to_page_no
        else:
            page_no += 1


def parse_article_list(article_list):
    keys = ['articleId', 'subject', 'writerId']
    result_list = []
    article_id_list = []
    for x in article_list:
        result_list.append(list(map(x.get, keys)))
        article_id_list.append(x['articleId'])
    return result_list, article_id_list


# 리스트에서 사이값 추출 (low,high value 포함)
def between(origin_list, low, high):
    result_list = []
    for i in origin_list:
        if low <= i <= high:
            result_list.append(i)
    return result_list
