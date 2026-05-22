import requests
import pandas as pd
import time

API_KEY = "c2bc2e5748c3279f4b75fd9508b4e8e8145ada4b"
CORP_CODE = "00126380"
YEARS = ["2023", "2024", "2025"]
QUARTERS = ["11013", "11012", "11014", "11011"]

TARGET_ACCOUNTS = ["자산총계", "부채총계", "자본총계", "매출액", "영업이익", "영업활동현금흐름"]
all_data = {}
Q_ORDER = {"11014": 1, "11012": 2, "11013": 3, "11011": 4}

def fetch_data(year, q):
    url = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"
    params = {"crtfc_key": API_KEY, "corp_code": CORP_CODE, "bsns_year": year, "reprt_code": q, "fs_div": "CFS"}
    res = requests.get(url, params=params)
    if res.status_code == 200:
        data = res.json()
        if data.get('status') == '000': return pd.DataFrame(data['list'])
    return None

def get_safe_amount(df, target_key):
    for _, row in df.iterrows():
        nm = str(row['account_nm']).strip()
        raw_val = row.get('thstrm_amount')
        if pd.isna(raw_val) or str(raw_val).strip() == '': continue
        try: val = int(raw_val)
        except: continue
        if target_key == "매출액" and ('매출액' in nm or '영업수익' in nm): return val
        elif target_key == "영업이익" and '영업이익' in nm and '비용' not in nm: return val
        elif target_key == "영업활동현금흐름" and '영업활동' in nm and '현금흐름' in nm: return val
        elif target_key in nm and target_key in ["자산총계", "부채총계", "자본총계"]: return val
    return 0

# 데이터 수집
for y in YEARS:
    for q in QUARTERS:
        df = fetch_data(y, q)
        if df is not None:
            all_data[f"{y}-{q}"] = {key: get_safe_amount(df, key) for key in TARGET_ACCOUNTS}
        time.sleep(0.3)

sorted_keys = sorted(all_data.keys(), key=lambda x: (x.split('-')[0], Q_ORDER.get(x.split('-')[1], 0)))

# 1. 수집된 기본 정보 출력
print(f"{'분기':<8} | {'매출액':<14} | {'영업이익':<14} | {'영업현금흐름':<14} | {'자산총계':<14}")
print("-" * 75)
for key in sorted_keys:
    d = all_data.get(key)
    print(f"{key:<8} | {d.get('매출액',0):>13,} | {d.get('영업이익',0):>13,} | {d.get('영업활동현금흐름',0):>13,} | {d.get('자산총계',0):>13,}")

# 2. 분석 지표 출력
print(f"\n{'분기':<8} | {'영익률':<6} | {'현금영익(OCF)':<12} | {'부채비율':<7} | {'매출(Y)':<9} | {'영익(Y)':<9} | {'자산(Y)':<9} | {'매출(Q)':<9} | {'영익(Q)':<9} | {'자산(Q)':<9}")
print("-" * 145)

for i, key in enumerate(sorted_keys):
    curr = all_data.get(key)
    if not curr or curr.get('매출액', 0) == 0: continue
    
    r, o, ocf, a = curr.get('매출액', 0), curr.get('영업이익', 0), curr.get('영업활동현금흐름', 0), curr.get('자산총계', 0)
    op_r, ocf_r = (o / r * 100), (ocf / r * 100)
    debt_r = (curr.get('부채총계', 0) / curr.get('자본총계', 1) * 100)
    
    def calc_change(curr_v, prev_v): return ((curr_v - prev_v) / prev_v * 100) if (prev_v and prev_v != 0) else None
    
    y, q = key.split('-')
    prev_yoy = all_data.get(f"{int(y)-1}-{q}")
    prev_qoq = all_data.get(sorted_keys[i-1]) if i > 0 else None
    
    r_yoy, o_yoy, a_yoy = calc_change(r, prev_yoy.get('매출액', 0) if prev_yoy else None), calc_change(o, prev_yoy.get('영업이익', 0) if prev_yoy else None), calc_change(a, prev_yoy.get('자산총계', 0) if prev_yoy else None)
    r_qoq, o_qoq, a_qoq = calc_change(r, prev_qoq.get('매출액', 0) if prev_qoq else None), calc_change(o, prev_qoq.get('영업이익', 0) if prev_qoq else None), calc_change(a, prev_qoq.get('자산총계', 0) if prev_qoq else None)
    
    def fmt_g(v): return f"{v:>8.1f}%" if v is not None else "     N/A"




    '''
   성장성 필터: 매출(Y) > 10% AND 영익(Y) > 10% (최소한 10% 이상 성장하는 기업)
   수익성 필터: 영익률 > 10% (장사 좀 할 줄 아는 기업)
   안전성 필터: 부채비율 < 100% (빚이 적은 기업)
   현금력 필터: 현금영익(OCF) > 0 (현금 흐름이 막히지 않은 기업)
    '''    
    print(f"{key:<8} | {op_r:>5.1f}% | {ocf_r:>10.1f}% | {debt_r:>6.1f}% | {fmt_g(r_yoy)} | {fmt_g(o_yoy)} | {fmt_g(a_yoy)} | {fmt_g(r_qoq)} | {fmt_g(o_qoq)} | {fmt_g(a_qoq)}")