import requests
import mariadb
from dotenv import load_dotenv
import os
import json
from datetime import datetime
import time
import asyncio
import websockets
import ssl
from db import *


import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()


def get_token():
    url = "https://openapi.ls-sec.co.kr:8080/oauth2/token"

    headers = {
        "content-type": "application/x-www-form-urlencoded"
    }

    data = {
        "grant_type": "client_credentials",
        "appkey": os.getenv("LS_APP_KEY"),
        "appsecretkey": os.getenv("LS_APP_SECRET"),
        "scope": "oob"
    }

    res = requests.post(url, headers=headers, data=data, verify=False)

    if res.status_code != 200:
        print("토큰 발급 실패 ❌, status:", res.status_code, ' ', res.text)
        return None

    return res.json().get("access_token")










import requests
import urllib3
urllib3.disable_warnings()

def get_kospi(access_token):
    """
    LS증권 API (t8432)를 사용하여 코스피 시가총액 상위 100개 종목을 조회합니다.
    
    :param access_token: 유효한 LS증권 API 접근 토큰
    :return: [{종목코드, 종목명}, ...] 리스트, 실패 시 None
    """
    url = "https://openapi.ls-sec.co.kr:8080/stock/market"

    # API 호출에 필요한 헤더 설정
    headers = {
        "content-type": "application/json; charset=UTF-8",
        "authorization": f"Bearer {access_token}",
        "tr_cd": "t8432", # 전 종목 시세 조회 (시가총액 순)
        "tr_cont": "N",
        "tr_cont_key": ""
    }
    
    # API 요청에 필요한 입력 데이터
    input_data = {
        "t8432InBlock": {
            "gubun": "0",  # 0: 코스피, 1: 코스닥
            "qrycnt": 100, # 100개 종목 요청
            "tname": "",   # 시가총액 순으로 조회하려면 공백 ("") 유지
            "sdate": ""    # 날짜 필드 (필요 없음)
        }
    }
    
    print("📈 코스피 시가총액 상위 100개 종목 목록 요청 중... (TR_CD: t8432)")
    
    res = requests.post(url, headers=headers, json=input_data, verify=False)
    
    if res.status_code != 200 or res.json().get("rsp_cd") != "00000":
        print("시총 상위 종목 요청 실패 ❌, status:", res.status_code)
        print("서버 응답 본문:", res.text)
        return None
        
    json_data = res.json()
    # 결과는 t8432OutBlock1 리스트에 담겨 있습니다.
    top_stocks = json_data.get("t8432OutBlock1", [])

    result_list = []
    for stock in top_stocks:
        result_list.append({
            "code": stock.get("shcode"),
            "name": stock.get("hname")
        })
        
    return result_list




if __name__ == "__main__":
    access_token = get_token()

    create_tb_basic()



    # kospi = get_kospi(access_token)
    # print(kospi)


    








    
