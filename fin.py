import requests
import pandas as pd
import time

API_KEY = "c2bc2e5748c3279f4b75fd9508b4e8e8145ada4b"
CORP_CODE = "00126380" # 삼성전자 고유번호
YEAR = "2026"
QUARTERS = ["11013", "11012", "11014", "11011"]

# 1. 인자를 4개 받도록 수정했습니다
def fetch_data(corp_code, name, year, quarter):
    url = "https://opendart.fss.or.kr/api/fnlttSinglAcnt.json"
    params = {"crtfc_key": API_KEY, "corp_code": corp_code, "bsns_year": year, "reprt_code": quarter}
    
    print(f"DEBUG: 요청 중... {year}년 {quarter}분기")
    res = requests.get(url, params=params)
    
    if res.status_code == 200:
        data = res.json()
        print(f"DEBUG: 서버 응답 확인 (Status: {data.get('status')})")
        
        if data.get('status') == '000':
            return pd.DataFrame(data['list'])
        else:
            print(f"DEBUG: 데이터 없음 또는 오류 (메시지: {data.get('message')})")
    else:
        print(f"DEBUG: 네트워크 오류 (코드: {res.status_code})")
    return None

# 실행
print(f"{'기업명':<10} | {'연도':<5} | {'분기':<6} | {'계정명':<15} | {'금액':<20}")
print("-" * 70)

for q in QUARTERS:
    df = fetch_data(CORP_CODE, "삼성전자", YEAR, q)
    if df is not None and not df.empty:
        # 데이터가 있으면 출력 (일단 5개만)
        for _, item in df.head(5).iterrows():
            print(f"{'삼성전자':<10} | {YEAR:<5} | {q:<6} | {item['account_nm']:<15} | {item['thstrm_amount']:<20}")
    time.sleep(0.5)