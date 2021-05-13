import os
import json
import sys

# profile 확인
env = os.getenv('FLASK_ENV', default="local")

# profile에 따른 대상 설정 파일 지정
config_file = f"config/config_{env}.json"

# 설정파일 load
with open(config_file) as f:
    conf = json.load(f)


def get_club_id():
    return conf['CLUB_ID']


def get_profile():
    return env


def get_user_id():
    return conf['USER_ID']


def get_user_password():
    return conf['USER_PASSWORD']
