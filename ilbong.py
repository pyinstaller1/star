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
import numpy as np
import duckdb
try:
    from api.db import *
except:
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













import pandas as pd
import numpy as np
import time
import requests
import math


# ----------------------------------------------------------------------
# 통합 지표 계산 함수 (tail_n 분기 최적화 반영)
# ----------------------------------------------------------------------
def get_ilbong_rsi(ilbong, tail_n=None):
    """
    주어진 일봉 데이터(ilbong: List of Dict)에 RSI, MACD, Bollinger Band, 일목균형표를 계산합니다.
    💡 tail_n이 지정되면 지표 계산은 전체(500일)로 정확하게 수행하되, 
       최종 Dict 변환 루프는 최근 N일만 수행하여 연산 속도를 극대화합니다.
    """
    if not ilbong:
        return []

    # 1. 날짜 오름차순 정렬 (모든 지표 계산의 기본 조건)
    ilbong.sort(key=lambda row: row['date'])

    # 2. Pandas DataFrame으로 변환 (계산 효율성 극대화)
    df = pd.DataFrame(ilbong)
    df['high'] = pd.to_numeric(df['high'])
    df['low'] = pd.to_numeric(df['low'])
    df['close'] = pd.to_numeric(df['close']) 
    
    closes = df['close']
    
    # ----------------------------------------------------------------------
    # A. RSI (N=14)
    # ----------------------------------------------------------------------
    N_rsi = 14
    delta = closes.diff()
    u = delta.apply(lambda x: x if x > 0 else 0)
    d = delta.apply(lambda x: -x if x < 0 else 0)

    df['au'] = u.ewm(com=N_rsi-1, adjust=False).mean()
    df['ad'] = d.ewm(com=N_rsi-1, adjust=False).mean()
    df['rsi14'] = 100 * df['au'] / (df['au'] + df['ad'])

    # ----------------------------------------------------------------------
    # B. MACD (EMA12, EMA26, Signal 9)
    # ----------------------------------------------------------------------
    ema_short, ema_long, signal_n = 12, 26, 9
    df['ema12'] = closes.ewm(span=ema_short, adjust=False).mean()
    df['ema26'] = closes.ewm(span=ema_long, adjust=False).mean()
    df['macd'] = df['ema12'] - df['ema26']
    df['macd9'] = df['macd'].ewm(span=signal_n, adjust=False).mean()
    
    # ----------------------------------------------------------------------
    # C. Bollinger Band (N=20)
    # ----------------------------------------------------------------------
    N_bol = 20
    df['ma20_bol'] = closes.rolling(window=N_bol).mean()
    stddev_20 = closes.rolling(window=N_bol).std()
    df['bol_u'] = df['ma20_bol'] + stddev_20 * 2
    df['bol_l'] = df['ma20_bol'] - stddev_20 * 2
    
    df['bol_width'] = df['bol_u'] - df['bol_l']
    bol_mean = df['bol_width'].mean()
    
    df['bol_size'] = np.where(
        df['bol_u'].isna(), None,
        np.where(df['bol_width'] > bol_mean * 1.5, 'Big', 'Small')
    )
    df['bol_dolpa'] = np.where(
        df['bol_u'].isna(), None,
        np.where(df['close'] > df['bol_u'], '상향돌파',
                 np.where(df['close'] < df['bol_l'], '하향돌파', '보통'))
    )

    # ----------------------------------------------------------------------
    # D. 일목균형표 (키움 스타일)
    # ----------------------------------------------------------------------
    high_26 = df['high'].rolling(window=26).max()
    low_26 = df['low'].rolling(window=26).min()
    kijun = (high_26 + low_26) / 2

    high_9 = df['high'].rolling(window=9).max()
    low_9 = df['low'].rolling(window=9).min()
    tenkan = (high_9 + low_9) / 2

    df['ilmok_a'] = ((kijun + tenkan) / 2).shift(25)
    high_52 = df['high'].rolling(window=52).max()
    low_52 = df['low'].rolling(window=52).min()
    df['ilmok_b'] = ((high_52 + low_52) / 2).shift(25)
    
    df['ilmok_yang'] = np.where(df['ilmok_a'].isna() | df['ilmok_b'].isna(), None,
                                np.where(df['ilmok_a'] > df['ilmok_b'], '양운', '음운'))
    
    nan_condition = df['ilmok_a'].isna() | df['ilmok_b'].isna()
    df['ilmok_dolpa'] = np.where(
        nan_condition, None,
        np.where(
            (df['high'] > df['ilmok_a']) & (df['high'] > df['ilmok_b']), "상향돌파",
            np.where(
                (df['low'] < df['ilmok_a']) & (df['low'] < df['ilmok_b']), "하향돌파",
                np.where(
                    ((df['low'] > df['ilmok_a']) & (df['low'] < df['ilmok_b'])) | \
                    ((df['low'] < df['ilmok_a']) & (df['low'] > df['ilmok_b'])) | \
                    ((df['high'] > df['ilmok_a']) & (df['high'] < df['ilmok_b'])) | \
                    ((df['high'] < df['ilmok_a']) & (df['high'] > df['ilmok_b'])),
                    "구름내부", "보통"
                )
            )
        )
    )
    
    # ----------------------------------------------------------------------
    # 💡 7. 최종 결과 추출 분기 최적화 (핵심 변경 지점)
    # ----------------------------------------------------------------------
    # tail_n이 있으면 원본 리스트와 DataFrame의 마지막 N개만 매칭 타겟으로 삼음
    if tail_n is not None and tail_n > 0:
        target_ilbong = ilbong[-tail_n:]
        start_idx = len(df) - tail_n
    else:
        target_ilbong = ilbong
        start_idx = 0
    
    for i, row in enumerate(target_ilbong):
        df_idx = start_idx + i
        if df_idx < 0 or df_idx >= len(df):
            continue
            
        row['rsi14'] = round(df['rsi14'].iloc[df_idx], 4) if pd.notna(df['rsi14'].iloc[df_idx]) else None
        row['macd'] = round(df['macd'].iloc[df_idx], 4) if pd.notna(df['macd'].iloc[df_idx]) else None
        row['macd9'] = round(df['macd9'].iloc[df_idx], 4) if pd.notna(df['macd9'].iloc[df_idx]) else None
        row['bol_u'] = round(df['bol_u'].iloc[df_idx], 2) if pd.notna(df['bol_u'].iloc[df_idx]) else None
        row['bol_l'] = round(df['bol_l'].iloc[df_idx], 2) if pd.notna(df['bol_l'].iloc[df_idx]) else None
        row['bol_size'] = df['bol_size'].iloc[df_idx] if pd.notna(df['bol_size'].iloc[df_idx]) else None
        row['bol_dolpa'] = df['bol_dolpa'].iloc[df_idx] if pd.notna(df['bol_dolpa'].iloc[df_idx]) else None
        row['ilmok_a'] = round(df['ilmok_a'].iloc[df_idx], 2) if pd.notna(df['ilmok_a'].iloc[df_idx]) else None
        row['ilmok_b'] = round(df['ilmok_b'].iloc[df_idx], 2) if pd.notna(df['ilmok_b'].iloc[df_idx]) else None
        row['ilmok_yang'] = df['ilmok_yang'].iloc[df_idx] if pd.notna(df['ilmok_yang'].iloc[df_idx]) and df['ilmok_yang'].iloc[df_idx] != '?' else None
        row['ilmok_dolpa'] = df['ilmok_dolpa'].iloc[df_idx] if pd.notna(df['ilmok_dolpa'].iloc[df_idx]) and df['ilmok_dolpa'].iloc[df_idx] != '?' else None

    return target_ilbong







def get_ilbong(access_token, shcode, start_date='19990101', end_date=time.strftime('%Y%m%d', time.localtime()), qrycnt=500):
    
    """
    일봉 데이터를 받아와서 정확한 지표 계산을 위해 기존 DB 데이터와 병합한 뒤, 
    요청한 qrycnt 분량만큼만 최적화 계산하여 DB에 저장합니다.
    """
    url_base = "https://openapi.ls-sec.co.kr:8080/stock/chart"
    url_supply = "https://openapi.ls-sec.co.kr:8080/stock/frgr-itt"
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "authorization": f"Bearer {access_token}"
    }

    # ======================================================================
    # 1. t8410 (순수 신규 일봉 OHLCV) API 요청 및 단독 가공
    # ======================================================================
    headers_ohlcv = {**headers, "tr_cd": "t8410", "tr_cont": "N", "tr_cont_key": ""}
    body_ohlcv = {
        "t8410InBlock": {
            "shcode": shcode, "gubun": "2", "qrycnt": qrycnt,  
            "sdate": start_date, "edate": end_date, "cts_date": "", 
            "comp_yn": "N", "sujung": "Y"
        }
    }

    try:
        res_ohlcv = requests.post(url_base, headers=headers_ohlcv, json=body_ohlcv, verify=False) 
        rows = res_ohlcv.json().get("t8410OutBlock1", [])
    except Exception:
        rows = []
    
    if not rows:
        return []

    temp_ilbong_data = []
    for row in rows:
        temp_ilbong_data.append({
            "date": str(row["date"]), "open": float(row["open"]), "high": float(row["high"]), 
            "low": float(row["low"]), "close": float(row["close"]), "volume": int(row["jdiff_vol"])
        })
    
    # 💡 1단계: 이번에 새로 요청해서 받아온 신규 데이터 기간만으로 DataFrame을 선형성(Index화)합니다.
    df_new = pd.DataFrame(temp_ilbong_data).drop_duplicates(subset=['date']).set_index('date')

    # ======================================================================
    # 2. t1702 (신규 기간 수급 데이터) API 요청 후 df_new에 먼저 매칭
    # ======================================================================
    headers_t1702 = {**headers, "tr_cd": "t1702", "tr_cont": "N", "tr_cont_key": ""}
    body_t1702 = {"t1702InBlock": {"shcode": shcode, "fromdt": start_date, "todt": end_date, "volvalgb": "1", "msmdgb": "0", "gubun": "0", "exchgubun": "U"}}
    
    investor_rows = []
    try:
        res_t1702 = requests.post(url_supply, headers=headers_t1702, json=body_t1702, verify=False)
        investor_rows = res_t1702.json().get("t1702OutBlock1", [])
    except Exception:
        pass

    if investor_rows:
        investor_data_list = []
        for row in investor_rows:
            핵심_기관_합계 = (
                float(row.get("tjj0001", 0)) + float(row.get("tjj0002", 0)) +
                float(row.get("tjj0003", 0)) + float(row.get("tjj0004", 0)) +
                float(row.get("tjj0005", 0)) 
            )
            investor_data_list.append({
                'date': str(row["date"]), '개인': float(row.get("tjj0008", 0)), 
                '외국인': float(row.get("tjj0016", 0)), '기관': 핵심_기관_합계,                     
                '연기금': float(row.get("tjj0006", 0)), '사모펀드': float(row.get("tjj0000", 0)),
            })
        df_investor = pd.DataFrame(investor_data_list).drop_duplicates(subset=['date']).set_index('date')
        # 💡 신규 일봉 기간 내에서만 수급 left join
        df_new = df_new.join(df_investor, how='left')
        
    # ======================================================================
    # 3. t1716 (신규 기간 공매도/프로그램) API 요청 후 df_new에 마저 매칭
    # ======================================================================
    headers_t1716 = {**headers, "tr_cd": "t1716", "tr_cont": "N", "tr_cont_key": ""}
    body_t1716 = {
        "t1716InBlock": {
            "shcode": shcode, "gubun": "0", "fromdt": start_date, "todt": end_date,
            "prapp": 0, "prgubun": "0", "orggubun": "0", "frggubun": "0"
        }
    }

    all_short_rows = []
    try:
        res_t1716 = requests.post(url_supply, headers=headers_t1716, json=body_t1716, verify=False)
        all_short_rows = res_t1716.json().get("t1716OutBlock", [])
    except Exception:
        pass

    if all_short_rows:
        extra_data_list = []
        for row in all_short_rows:
            extra_data_list.append({
                'date': str(row["date"]),
                '공매도수량': float(row.get("gm_volume", 0)), 
                '공매도대금': float(row.get("gm_value", 0)),
                '프로그램': float(row.get("pgmvol", 0)), 
            })
        df_extra = pd.DataFrame(extra_data_list).drop_duplicates(subset=['date']).set_index('date')
        # 💡 신규 일봉 기간 내에서만 공매도 left join
        df_new = df_new.join(df_extra, how='left')

    # ======================================================================
    # 💡 [핵심 변경] 신규 수급/공매도가 완결된 df_new 뒤에 과거 DB(200일치)를 보완결합
    # ======================================================================
    df_new.reset_index(inplace=True)
    
    if qrycnt < 150:
        try:
            con = duckdb.connect(db_path)
            # 과거 수급/공매도 컬럼까지 완벽하게 보존된 상태로 가져옵니다.
            db_query = """
                SELECT date, open, high, low, close, volume, 
                       개인, 외국인, 기관, 연기금, 사모펀드, 프로그램, 공매도수량, 공매도대금 
                FROM tb_ilbong WHERE code = $shcode ORDER BY date DESC LIMIT 200
            """
            df_db = con.execute(db_query, {"shcode": shcode}).df()
            con.close()
            
            if not df_db.empty:
                df_db['date'] = df_db['date'].astype(str)
                # 새로 수집된 날짜와 겹치는 과거 데이터 제거
                new_dates = df_new['date'].tolist()
                df_db_filtered = df_db[~df_db['date'].isin(new_dates)]
                
                # 💡 위아래 결합(concat) 방식을 사용하여 과거 수급 데이터 오염을 완벽히 차단
                df = pd.concat([df_new, df_db_filtered], ignore_index=True)
            else:
                df = df_new
        except Exception as e:
            print(f"[시스템 알림] 과거 DB 연동 불가로 현재 수집된 데이터로만 처리합니다: {e}")
            df = df_new
    else:
        df = df_new

    # ======================================================================
    # 4. 전체 기간 정렬 및 이평선 계산
    # ======================================================================
    df['date'] = df['date'].astype(str)
    df.sort_values('date', ascending=True, inplace=True)
    df['close'] = pd.to_numeric(df['close']) 
    df.set_index('date', inplace=True)

    df['ma5'] = df['close'].rolling(window=5).mean()
    df['ma20'] = df['close'].rolling(window=20).mean()
    df['ma60'] = df['close'].rolling(window=60).mean()
    df['ma120'] = df['close'].rolling(window=120).mean()
    
    # ======================================================================
    # 5. Dict List 구조 변환
    # ======================================================================
    ilbong = []
    for index, row in df.reset_index().iterrows():
        item = {
            'code': shcode, 'date': row['date'],
            'open': row['open'], 'high': row['high'], 'low': row['low'], 'close': row['close'],
            'volume': row.get('volume', 0), 
            'ma5': round(row['ma5'], 2) if pd.notna(row.get('ma5')) else None,
            'ma20': round(row['ma20'], 2) if pd.notna(row.get('ma20')) else None,
            'ma60': round(row['ma60'], 2) if pd.notna(row.get('ma60')) else None,
            'ma120': round(row['ma120'], 2) if pd.notna(row.get('ma120')) else None,
            '개인': float(row['개인']) if '개인' in row and pd.notna(row['개인']) else None,
            '외국인': float(row['외국인']) if '외국인' in row and pd.notna(row['외국인']) else None,
            '기관': float(row['기관']) if '기관' in row and pd.notna(row['기관']) else None,
            '연기금': float(row['연기금']) if '연기금' in row and pd.notna(row['연기금']) else None,
            '사모펀드': float(row['사모펀드']) if '사모펀드' in row and pd.notna(row['사모펀드']) else None,
            '프로그램': float(row['프로그램']) if '프로그램' in row and pd.notna(row['프로그램']) else None,
            '공매도수량': float(row['공매도수량']) if '공매도수량' in row and pd.notna(row['공매도수량']) else None,
            '공매도대금': float(row['공매도대금']) if '공매도대금' in row and pd.notna(row['공매도대금']) else None,
        }
        ilbong.append(item)

    # ======================================================================
    # 6. 지표 연산 엔진 가동 (tail_n으로 N일치만 최종 반환 제어)
    # ======================================================================
    if qrycnt < 150:
        ilbong = get_ilbong_rsi(ilbong, tail_n=qrycnt)
    else:
        ilbong = get_ilbong_rsi(ilbong)

    # print(f"[{shcode}] {len(ilbong)}건 완료")
    
    # 7. 최종 데이터베이스 Upsert 적재
    if ilbong:
        insert_tb_ilbong(ilbong)

    return ilbong









def get_ilbong_total7():
    print('get_ilbong_total')

    access_token = get_token()
    list_kospi = select_tb_kospi()

    for i, item in enumerate(list_kospi):
        print(str(i+1) + ' ' + str(item[0]) + ' ' + str(item[1]))
        get_ilbong(access_token, str(item[0]))










def get_ilbong_total8():
    print('get_ilbong_total 시작')

    access_token = get_token()
    list_kospi = select_tb_kospi()

    for i, item in enumerate(list_kospi):
        # 1. 출력할 메시지 구성
        msg = f"{i+1} {item[0]} {item[1]}"
        
        # 2. 서버 콘솔 출력 (기존 기능)
        print(msg)
        
        # 3. 브라우저 로그창으로 전송 (SSE 형식 필수: data: 메시지\n\n)
        yield f"{msg}\n\n"
        
        # 4. 실제 데이터 수집 작업
        get_ilbong(access_token, str(item[0]))



def get_ilbong_1day8():
    print('get_ilbong_1day 시작')
    access_token = get_token()
    list_kospi = select_tb_kospi()

    for i, item in enumerate(list_kospi):
        msg = f"{i+1} {item[0]} {item[1]}"
        
        # [핵심] 브라우저 로그창으로 전송
        yield f"{msg}\n\n" 
        
        # 1일치 수집 (기존 qrycnt=1 유지)
        get_ilbong(access_token, str(item[0]), qrycnt=100)




def get_ilbong_1day(qrycnt):
    print(f'get_ilbong_1day 시작 (요청 일수: {qrycnt}일)')
    access_token = get_token()
    list_kospi = select_tb_kospi()

    for i, item in enumerate(list_kospi):
        msg = f"{i+1} {item[0]} {item[1]}"

        print(msg)
        
        # [핵심] 브라우저 로그창으로 전송
        yield f"{msg}\n\n" 
        
        # [수정] 기존 고정값 대신 넘겨받은 qrycnt 변수를 대입해서 실제 수집 연산에 반영!
        get_ilbong(access_token, str(item[0]), qrycnt=qrycnt)












if __name__ == "__main__":
    access_token = get_token()
    list_kospi = select_tb_kospi()
    print('일봉 수집 시작!   ' + time.strftime('[%H:%m]', time.localtime()))

    create_tb_ilbong()

    get_ilbong_1day()


    '''
    for i, item in enumerate(list_kospi):
        print(str(i+1) + ' ' + str(item[0]) + ' ' + str(item[1]))
        get_ilbong(access_token, str(item[0]))
    '''


    print('일봉 수집 종료   ' + time.strftime('[%H:%m]', time.localtime()))











    
