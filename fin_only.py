import requests
import pandas as pd
import time

API_KEY = "c2bc2e5748c3279f4b75fd9508b4e8e8145ada4b"
CORP_CODE = "00126380" # 삼성전자 고유번호
YEAR = "2025"
# 1분기(11013), 반기(11012), 3분기(11014), 사업보고서(11011)
QUARTERS = ["11013", "11012", "11014", "11011"]

# DART 표준 계정 ID (이걸로 매칭해야 이름 중복에 안 속음)
STANDARD_IDS = {
    "ifrs-full_Equity": "자본총계",
    "ifrs-full_Assets": "자산총계",
    "ifrs-full_Liabilities": "부채총계",
    "ifrs-full_Revenue": "매출액",
    "ifrs-full_OperatingProfitLoss": "영업이익"
}

def fetch_all_financial_data(corp_code, year, quarter):
    url = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"
    params = {
        "crtfc_key": API_KEY, 
        "corp_code": corp_code, 
        "bsns_year": year, 
        "reprt_code": quarter,
        "fs_div": "CFS" # 연결재무제표 기준
    }
    
    print(f"DEBUG: 요청 중... {year}년 {quarter} 분기코드")
    res = requests.get(url, params=params)
    
    if res.status_code == 200:
        data = res.json()
        if data.get('status') == '000':
            return pd.DataFrame(data['list'])
    return None

# 출력 헤더
print(f"\n{'기업명':<8} | {'연도':<4} | {'분기':<5} | {'계정명':<18} | {'금액(원)':<20}")
print("-" * 85)

for q in QUARTERS:
    df = fetch_all_financial_data(CORP_CODE, YEAR, q)
    
    if df is not None and not df.empty:
        # 공백 제거
        df['account_id'] = df['account_id'].str.strip()
        df['account_nm'] = df['account_nm'].str.strip()
        
        # 1. 고유 ID(account_id) 기반으로 일반 계정 필터링 (자본총계 중복 방지)
        normal_df = df[df['account_id'].isin(STANDARD_IDS.keys())]
        
        # 만약 표준 ID로 안 잡히는 항목이 있다면 계정명으로 2차 백업 필터링 (중복 제거 포함)
        seen_normal = set()
        for _, item in normal_df.iterrows():
            standard_nm = STANDARD_IDS[item['account_id']]
            if standard_nm in seen_normal:
                continue
            seen_normal.add(standard_nm)
            
            try: amount = f"{int(item['thstrm_amount']):,}"
            except: amount = item['thstrm_amount'] if item['thstrm_amount'] else "0"
            print(f"{'삼성전자':<8} | {YEAR:<4} | {q:<5} | {standard_nm:<18} | {amount:<20}")
            
        # 2. 현금흐름표 데이터 추출 (영업, 투자, 재무)
        cf_df = df[(df['sj_div'] == 'CF') | (df['account_nm'].str.contains('현금흐름'))]
        cf_types = {'영업': '영업활동 현금흐름', '투자': '투자활동 현금흐름', '재무': '재무활동 현금흐름'}
        seen_cf = set()
        
        for _, item in cf_df.iterrows():
            nm = item['account_nm']
            for key, standard_nm in cf_types.items():
                if key in nm and "현금흐름" in nm and standard_nm not in seen_cf:
                    try: amount = f"{int(item['thstrm_amount']):,}"
                    except: amount = item['thstrm_amount'] if item['thstrm_amount'] else "0"
                    
                    print(f"{'삼성전자':<8} | {YEAR:<4} | {q:<5} | {standard_nm:<18} | {amount:<20}")
                    seen_cf.add(standard_nm)
                    
    print("-" * 85)
    time.sleep(0.5)