


import requests
import urllib3
import os
from dotenv import load_dotenv
try:
    from api.db import *
except:
    from db import *





    
load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_token():
    """hoga.py 내부에서 직접 토큰을 발급받는 함수"""
    url = "https://openapi.ls-sec.co.kr:8080/oauth2/token"
    headers = {"content-type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "appkey": os.getenv("LS_APP_KEY"),
        "appsecretkey": os.getenv("LS_APP_SECRET"),
        "scope": "oob"
    }
    res = requests.post(url, headers=headers, data=data, verify=False)
    if res.status_code == 200:
        return res.json().get("access_token")
    print(f"토큰 발급 실패: {res.status_code}")
    return None

def fetch_hoga_api(shcode):
    access_token = get_token()
    if not access_token:
        return {}

    url = "https://openapi.ls-sec.co.kr:8080/stock/market-data"
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "authorization": f"Bearer {access_token}",
        "tr_cd": "t1101",
        "tr_cont": "N"
    }
    body = {"t1101InBlock": {"shcode": shcode}}
    
    res = requests.post(url, headers=headers, json=body, verify=False)
    
    if res.status_code == 200:
        raw = res.json().get("t1101OutBlock", {})
        
        # 1. API 데이터를 DB 컬럼명 규칙(offer1, bid1 등)으로 변환하여 api_data에 저장
        api_data = {}
        for i in range(1, 11):
            api_data[f'offer{i}'] = raw.get(f'offerho{i}', 0)
            api_data[f'offer_rem{i}'] = raw.get(f'offerrem{i}', 0)
            api_data[f'bid{i}'] = raw.get(f'bidho{i}', 0)
            api_data[f'bid_rem{i}'] = raw.get(f'bidrem{i}', 0)
            
        return api_data
        
    return {}












def save_hoga():

    list_kospi = select_tb_kospi()

    try:
        for item in list_kospi:
            print(item[0] + ' ' + item[1])
            api_data = fetch_hoga_api(item[0])
            if api_data:
                upsert_hoga(item[0], api_data)
    except Exception as e:
        print(f"⚠️ API 호출 실패: {e}")







def get_hoga(shcode):


    try:
        hoga_data = select_hoga(shcode) or {}
    except Exception as e:
        print(f"{e}")
    # print(hoga_data)

    return hoga_data



    

# save_hoga()
# get_hoga('005930')







