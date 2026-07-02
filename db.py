import os
import time
import math
import requests
import duckdb
import pandas as pd
import numpy as np
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from django.http import JsonResponse




load_dotenv()

# 1. MariaDB 연결 (SQLAlchemy Engine)
DB_URL = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@127.0.0.1:3306/db_ls?charset=utf8mb4"
engine = create_engine(DB_URL)

# 2. SQLite 경로 설정 (기존 stock.db 유지)
# base_dir = os.path.dirname(os.path.abspath(__file__))
# db_path = os.path.abspath(os.path.join(base_dir, '..', 'stock.db'))





def get_ilbong_data(shcode: str):
    con = duckdb.connect(db_path)
    
    query = "SELECT * FROM tb_ilbong WHERE code = $shcode ORDER BY date ASC"
    df = con.execute(query, {"shcode": shcode}).df()
    con.close()



    # 🔥 핵심 1: numpy → python type 변환
    df = df.astype(object)

    # 🔥 핵심 2: NaN → None
    df = df.where(pd.notnull(df), None)


    return df.to_dict('records')






base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.abspath(os.path.join(base_dir, '..', '..', 'stock.duckdb'))
# db_path = os.path.abspath(os.path.join(base_dir, '..', '..', 'stock.duckdb'))



def select_tb_ilbong(code):
    with duckdb.connect(db_path) as con:
        # 1. 쿼리 실행 및 딕셔너리 리스트 변환
        raw_list = con.execute(
            "SELECT * FROM tb_ilbong WHERE code = ? ORDER BY date ASC", 
            [code]
        ).df().to_dict('records')
        
        # 2. 함수 내부에서 곧바로 데이터 정제 (NaN -> None)
        cleaned_list = []
        for row in raw_list:
            # {key: (None if math.isnan(val) else val) for key, val in row.items()} 
            # 위 한 줄이 아래 반복문을 대신합니다 (딕셔너리 컴프리헨션)
            new_row = {k: (None if isinstance(v, float) and math.isnan(v) else v) for k, v in row.items()}
            cleaned_list.append(new_row)
            
        return cleaned_list

























def get_ilbong_db(shcode: str):
    """DuckDB를 사용하여 최근 500개 일봉 데이터 조회"""
    
    if 'db_path' not in globals():
        _base = os.path.dirname(os.path.abspath(__file__))
        target_path = os.path.abspath(os.path.join(_base, '..', '..', 'stock_data.duckdb'))
    else:
        target_path = db_path

    try:
        # 1. DuckDB 연결 (read_only=True로 설정하면 여러 프로세스에서 동시에 읽기 좋습니다)
        con = duckdb.connect(target_path, read_only=True) 
        
        # 2. 쿼리 실행
        query = "SELECT * FROM tb_ilbong WHERE code = ? ORDER BY date DESC LIMIT 500"
        df = con.execute(query, [shcode]).df()
        
        if df.empty:
            return []

        # 3. 날짜 역순 정렬 (최근 데이터가 뒤로 가게)
        df = df.iloc[::-1]

        # 4. 데이터 정제 함수 (반복되는 clean 로직 최적화)
        def clean(val, is_int=False):
            if pd.isna(val): return None
            if isinstance(val, (np.floating, np.integer)):
                val = val.item()
            try:
                return int(val) if is_int else float(val)
            except (ValueError, TypeError):
                return val

        # 5. 리스트 컴프리헨션을 사용하여 속도 향상
        ilbong_list = [
            {
                'code': shcode,
                'date': str(row['date']),
                'open': clean(row.get('open')),
                'high': clean(row.get('high')),
                'low': clean(row.get('low')),
                'close': clean(row.get('close')),
                'volume': clean(row.get('volume'), is_int=True),
                'ma5': clean(row.get('ma5')),
                'ma20': clean(row.get('ma20')),
                'ma60': clean(row.get('ma60')),
                'ma120': clean(row.get('ma120')),
                '개인': clean(row.get('개인')),
                '외국인': clean(row.get('외국인')),
                '기관': clean(row.get('기관')),
                '연기금': clean(row.get('연기금')),
                '사모펀드': clean(row.get('사모펀드')),
                '프로그램': clean(row.get('프로그램')),
                '공매도수량': clean(row.get('공매도수량')),
                '공매도대금': clean(row.get('공매도대금')),
                'rsi14': clean(row.get('rsi14')),
                'macd': clean(row.get('macd', 0.0)),
                'macd9': clean(row.get('macd9', 0.0)),
                'bol_u': clean(row.get('bol_u')),
                'bol_l': clean(row.get('bol_l')),
                'bol_size': clean(row.get('bol_size')),
                'bol_dolpa': clean(row.get('bol_dolpa')),
                'ilmok_a': clean(row.get('ilmok_a')),
                'ilmok_b': clean(row.get('ilmok_b')),
                'ilmok_yang': clean(row.get('ilmok_yang')),
                'ilmok_dolpa': clean(row.get('ilmok_dolpa')),
            }
            for _, row in df.iterrows()
        ]
        
        return ilbong_list
            
    except Exception as e:
        print(f"DuckDB 조회 오류 ({shcode}): {e}")
        return []
    finally:
        if 'con' in locals():
            con.close()















def select_golden(sql):

    con = duckdb.connect(db_path)

    try:

        cur = con.execute(sql)

        return {
            "columns": [d[0] for d in cur.description],
            "rows": cur.fetchall()
        }

    except Exception as e:

        return {
            "error": str(e)
        }

    finally:

        con.close()


















def upsert_hoga_bulk(bulk_data):
    if not bulk_data:
        return

    con = duckdb.connect(db_path)
    
    try:
        # 1. 컬럼 순서를 DB 테이블 스키마와 완벽히 일치시킴 (code, offer1, offer_rem1, bid1, bid_rem1, ...)
        cols = ["code"]
        for i in range(1, 11):
            cols.extend([f"offer{i}", f"offer_rem{i}", f"bid{i}", f"bid_rem{i}"])

        # 2. 파이썬 데이터 매핑도 위 순서와 1:1로 맞춤
        # 데이터에서 shcode는 code로 가져오고, 나머지는 순서대로 추출
        values = []
        for d in bulk_data:
            row = [d.get('shcode')]
            for i in range(1, 11):
                row.append(d.get(f'offer{i}', 0))
                row.append(d.get(f'offer_rem{i}', 0))
                row.append(d.get(f'bid{i}', 0))
                row.append(d.get(f'bid_rem{i}', 0))
            values.append(row)

        cols_def = ", ".join([f"offer{i} INTEGER, offer_rem{i} INTEGER, bid{i} INTEGER, bid_rem{i} INTEGER" for i in range(1, 11)])
        con.execute(f"CREATE TABLE IF NOT EXISTS tb_hoga (code VARCHAR PRIMARY KEY, {cols_def}, updated_at TIMESTAMP)")            
        
        # 3. 임시 테이블 생성
        con.execute("CREATE OR REPLACE TEMP TABLE temp_hoga AS SELECT * FROM tb_hoga WHERE 1=0")
        
        # 4. 쿼리문 자동 생성 (순서가 꼬일 일 없음)
        col_str = ", ".join(cols)
        placeholders = ", ".join(["?"] * len(cols))
        
        # 5. 일괄 삽입
        con.executemany(f"INSERT INTO temp_hoga ({col_str}) VALUES ({placeholders})", values)
        
        # 6. 원본 테이블로 Upsert (updated_at은 여기서 처리)
        # 중요: 원본 테이블 컬럼 순서가 (code, ..., bid_rem10, updated_at) 형태여야 함
        con.execute(f"""
            INSERT OR REPLACE INTO tb_hoga
            SELECT {col_str}, CURRENT_TIMESTAMP FROM temp_hoga
        """)
        
        print(f"✅ {len(bulk_data)}건의 데이터를 성공적으로 일괄 업데이트했습니다.")
        
    except Exception as e:
        print(f"❌ DB 일괄 저장 중 오류 발생: {e}")
        raise e
    finally:
        con.close()
        







def upsert_hoga(code, data):
    """
    10단계 호가 데이터를 저장/갱신합니다.
    """
    # 1. 연결 및 실행
    con = duckdb.connect(db_path)
    
    # 2. 쿼리 작성
    sql = """
        INSERT OR REPLACE INTO tb_hoga
        (code, 
         offer1, offer2, offer3, offer4, offer5, offer6, offer7, offer8, offer9, offer10,
         offer_rem1, offer_rem2, offer_rem3, offer_rem4, offer_rem5, offer_rem6, offer_rem7, offer_rem8, offer_rem9, offer_rem10,
         bid1, bid2, bid3, bid4, bid5, bid6, bid7, bid8, bid9, bid10,
         bid_rem1, bid_rem2, bid_rem3, bid_rem4, bid_rem5, bid_rem6, bid_rem7, bid_rem8, bid_rem9, bid_rem10,
         updated_at) 
        VALUES (?, 
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                CURRENT_TIMESTAMP)
    """
    params = [code] + \
             [data.get(f'offer{i}', 0) for i in range(1, 11)] + \
             [data.get(f'offer_rem{i}', 0) for i in range(1, 11)] + \
             [data.get(f'bid{i}', 0) for i in range(1, 11)] + \
             [data.get(f'bid_rem{i}', 0) for i in range(1, 11)]

    try:
        con.execute(sql, params)
    except duckdb.Error:
        # 테이블이 없는 경우 생성
        cols = ", ".join([f"offer{i} INTEGER, offer_rem{i} INTEGER, bid{i} INTEGER, bid_rem{i} INTEGER" for i in range(1, 11)])
        con.execute(f"CREATE TABLE IF NOT EXISTS tb_hoga (code VARCHAR PRIMARY KEY, {cols}, updated_at TIMESTAMP)")
        con.execute(sql, params)
    finally:
        con.close()

def select_hoga(code):
    """
    특정 종목의 호가 데이터를 조회합니다.
    """
    cols = ", ".join([f"offer{i}, offer_rem{i}, bid{i}, bid_rem{i}" for i in range(1, 11)])
    sql = f"SELECT code, {cols}, updated_at FROM tb_hoga WHERE code = ?"
    
    con = duckdb.connect(db_path)
    try:
        # 1. 쿼리 실행
        res = con.execute(sql, [code]).fetchone()
        
        # 2. 결과가 없으면 None 반환
        if not res:
            return None
        
        # 3. 딕셔너리로 변환 (DuckDB의 description을 이용해 키 매핑)
        # res는 튜플로 나오므로, 컬럼명을 가져와서 딕셔너리로 만듭니다.
        description = [desc[0] for desc in con.description]
        return dict(zip(description, res))
        
    except duckdb.Error:
        return None
    finally:
        con.close()
        





def select_st_hoga8(mode):
    con = duckdb.connect(db_path)

    list_kospi = select_tb_kospi()
    codes = [item[0] for item in list_kospi]
    codes = "','".join(codes)

    
    cols = ", ".join([f"offer{i}, offer_rem{i}, bid{i}, bid_rem{i}" for i in range(1, 11)])
    sql = f"SELECT code, 종목명 as name, {cols}, updated_at FROM tb_hoga a, tb_kospi b WHERE code in ('{codes}') and a.code = b.코드"

    tick = {'매도1': 3,  '매도2': 7,  '매도3': 11, '매도4': 15, '매도5': 19, '매도6': 23, '매도7': 27, '매도8': 31,
            '매수1': 5,  '매수2': 9,  '매수3': 13, '매수4': 17, '매수5': 21, '매수6': 25, '매수7': 29, '매수8': 33 }


    
    list_hoga = []



    rows = con.execute(sql).fetchall()
    description = [desc[0] for desc in con.description]

    
    for row in rows:
        # buy_cond = (row[tick['매수1']] > 500 and (row[tick['매수1']]/10 > row[tick['매도1']]) and (row[tick['매수1']]/10 > row[tick['매도2']]) and (row[tick['매수1']]/10 > row[tick['매도3']]) and (row[tick['매수1']]/10 > row[tick['매도4']]) and (row[tick['매수1']]/10 > row[tick['매도5']]) )



        buy_cond = (
            row[tick['매수1']] > 500 and
            row[tick['매수1']] / 10 > row[tick['매도1']] and
            row[tick['매수1']] / 10 > row[tick['매도2']] and
            row[tick['매수1']] / 10 > row[tick['매도3']] and
            row[tick['매수1']] / 10 > row[tick['매도4']] and
            row[tick['매수1']] / 10 > row[tick['매도5']] and
            
            row[tick['매수2']] / 5 > row[tick['매도1']] and
            row[tick['매수2']] / 5 > row[tick['매도2']] and
            row[tick['매수2']] / 5 > row[tick['매도3']] and
            row[tick['매수2']] / 5 > row[tick['매도4']] and
            row[tick['매수2']] / 5 > row[tick['매도5']]
            
        )


        # sell_cond = row[tick['매도1']] > 500 and (row[tick['매도1']]/10 > row[tick['매수1']]) and (row[tick['매도1']]/10 > row[tick['매수2']]) and (row[tick['매도1']]/10 > row[tick['매수3']]) and (row[tick['매도1']]/10 > row[tick['매수4']]) and (row[tick['매도1']]/10 > row[tick['매수5']])
        

        sell_cond = (
            row[tick['매도1']] > 500 and
            row[tick['매도1']] / 10 > row[tick['매수1']] and
            row[tick['매도1']] / 10 > row[tick['매수2']] and
            row[tick['매도1']] / 10 > row[tick['매수3']] and
            row[tick['매도1']] / 10 > row[tick['매수4']] and
            row[tick['매도1']] / 10 > row[tick['매수5']] and

            row[tick['매도2']] / 5 > row[tick['매수1']] and
            row[tick['매도2']] / 5 > row[tick['매수2']] and
            row[tick['매도2']] / 5 > row[tick['매수3']] and
            row[tick['매도2']] / 5 > row[tick['매수4']] and
            row[tick['매도2']] / 5 > row[tick['매수5']]

            
        )





        if mode=='buy' and buy_cond:
            list_hoga.append(dict(zip(description, row)))
                                 
        elif mode=='sell' and sell_cond:
            list_hoga.append(dict(zip(description, row)))

        elif mode=='etc' and not buy_cond and not sell_cond:
            list_hoga.append(dict(zip(description, row)))

    return list_hoga





def select_st_hoga(mode):
    con = duckdb.connect(db_path)
    
    # 1. SQL 단에서 매수/매도 조건을 미리 계산하기 위한 수식 정의
    # tick 딕셔너리의 인덱스 번호 대신 테이블 컬럼명을 직접 사용하여 DB 연산으로 처리합니다.
    buy_condition = """
        bid_rem1 > 500 AND
        (bid_rem1 / 10.0) > offer_rem1 AND (bid_rem1 / 10.0) > offer_rem2 AND 
        (bid_rem1 / 10.0) > offer_rem3 AND (bid_rem1 / 10.0) > offer_rem4 AND 
        (bid_rem1 / 10.0) > offer_rem5 AND
        (bid_rem2 / 5.0) > offer_rem1 AND (bid_rem2 / 5.0) > offer_rem2 AND 
        (bid_rem2 / 5.0) > offer_rem3 AND (bid_rem2 / 5.0) > offer_rem4 AND 
        (bid_rem2 / 5.0) > offer_rem5
    """
    
    sell_condition = """
        offer_rem1 > 500 AND
        (offer_rem1 / 10.0) > bid_rem1 AND (offer_rem1 / 10.0) > bid_rem2 AND 
        (offer_rem1 / 10.0) > bid_rem3 AND (offer_rem1 / 10.0) > bid_rem4 AND 
        (offer_rem1 / 10.0) > bid_rem5 AND
        (offer_rem2 / 5.0) > bid_rem1 AND (offer_rem2 / 5.0) > bid_rem2 AND 
        (offer_rem2 / 5.0) > bid_rem3 AND (offer_rem2 / 5.0) > bid_rem4 AND 
        (offer_rem2 / 5.0) > bid_rem5
    """

    # mode에 따라 SQL WHERE 절 동적 구성
    if mode == 'buy':
        filter_sql = f"WHERE ({buy_condition})"
    elif mode == 'sell':
        filter_sql = f"WHERE ({sell_condition})"
    else:  # 'etc'
        filter_sql = f"WHERE NOT ({buy_condition}) AND NOT ({sell_condition})"

    # 2. 호가 잔량 20개 중 최댓값(max_rem)을 DB에서 바로 구하는 대형 컬럼 리스트 생성
    all_rem_cols = [f"offer_rem{i}" for i in range(1, 11)] + [f"bid_rem{i}" for i in range(1, 11)]
    max_rem_expression = f"GREATEST({', '.join(all_rem_cols)}) as max_rem"
    
    cols = ", ".join([f"offer{i}, offer_rem{i}, bid{i}, bid_rem{i}" for i in range(1, 11)])
    
    # 3. 문자열 IN 대신 깔끔한 INNER JOIN 구조로 쿼리 작성 (속도 극대화)
    # 기존에 프론트엔드 template에서 사용하던 'item.max_rem'도 한 번에 넘겨줍니다.




    sql = f"""
        SELECT 
            a.code, 
            b.종목명 as name, 
            {cols}, 
            strftime(a.updated_at, '%H:%M:%S') as updated_at, -- DB에서 바로 포맷팅
            GREATEST({', '.join(all_rem_cols)}) as max_rem
        FROM tb_hoga a
        INNER JOIN tb_kospi b ON a.code = b.코드
        {filter_sql} 
    """







    try:
        # DuckDB의 df() 또는 dict() 변환 기능을 활용하면 파이썬 루프 없이 초고속 변환 가능
        # 여기서는 기존 템플릿과의 호환성을 위해 fetchall_of_dicts()와 유사한 구조를 사용하거나,
        # DuckDB에서 제공하는fetchall() 데이터를 바로 딕셔너리 리스트로 치환합니다.
        res = con.execute(sql)
        description = [desc[0] for desc in con.description]
        
        # 파이썬 레벨의 연산 없이 오직 결과 조립만 수행
        list_hoga = [dict(zip(description, row)) for row in res.fetchall()]
        
    except duckdb.Error as e:
        print(f"조회 오류 발생: {e}")
        list_hoga = []
    finally:
        con.close()

    return list_hoga























def insert_df_to_db(table, df):
    """SQLite에 DataFrame을 안전하게 Upsert 합니다."""
    with sqlite3.connect(db_path) as conn:
        temp_table = f"{table}_temp"
        df.to_sql(temp_table, conn, if_exists="replace", index=True, index_label="date")
        cur = conn.cursor()
        cur.execute(f'SELECT name FROM sqlite_master WHERE type="table" AND name="{table}"')
        if not cur.fetchone():
            df.head(0).to_sql(table, conn, if_exists="replace", index=True, index_label="date")
            cur.execute(f'CREATE UNIQUE INDEX IF NOT EXISTS idx_{table}_date ON "{table}" (date)')
        
        col_str = ", ".join(list(df.columns))
        cur.execute(f'INSERT INTO "{temp_table}" (date, {col_str}) SELECT date, {col_str} FROM "{table}" WHERE date NOT IN (SELECT date FROM "{temp_table}")')
        cur.execute(f'DELETE FROM "{table}"')
        cur.execute(f'INSERT INTO "{table}" (date, {col_str}) SELECT date, {col_str} FROM "{temp_table}"')
        cur.execute(f'DROP TABLE IF EXISTS "{temp_table}"')
        conn.commit()

def get_kospi_codes():
    with sqlite3.connect(db_path) as conn:
        return [row[0] for row in conn.execute("SELECT 코드 FROM KOSPI").fetchall()]

def get_kospi300_code():
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql("SELECT 코드, 종목명, 현재가, 등락률, 시가총액, 시장, 순위 FROM KOSPI", conn)












def create_tb_kospi(df, option="replace"):

    con = duckdb.connect(db_path)

    try:
        if option == "replace":
            con.execute("DROP TABLE IF EXISTS tb_kospi")
            con.execute("CREATE TABLE tb_kospi AS SELECT * FROM df")
        
        con.execute("CREATE INDEX IF NOT EXISTS idx_kospi_code ON tb_kospi (코드)")
        
    except Exception as e:
        print(f"DuckDB 테이블 생성 오류: {e}")
    finally:
        con.close()
        





def select_tb_kospi_code():

    con = duckdb.connect(db_path)
    sql = 'SELECT "코드" FROM tb_kospi'

    res = con.execute(sql).fetchall()
        
    con.close()
    return [item[0] for item in res]




def select_tb_kospi_name(shcode=None):

    con = duckdb.connect(db_path)
    sql = 'SELECT "코드", "종목명" FROM tb_kospi'
    
    if shcode:
        sql = 'SELECT "코드", "종목명" FROM tb_kospi WHERE "코드" = ?'
        
        res = con.execute(sql, [shcode]).fetchall()
    else:
        res = con.execute(sql).fetchall()
        
    con.close()
    return res




def select_tb_kospi(shcode=None):
    """전체 코스피 종목과 최신 일봉 RSI를 계산하여 순서대로 반환"""
    con = duckdb.connect(db_path)
    
    # 0=코드, 1=종목명, 2=현재가, 3=등락률, 4=시가총액, 5=RSI
    sql = """
        SELECT 
            "코드", "종목명", "현재가", "등락률", "시가총액",
            (SELECT ROUND(rsi14, 0) FROM tb_ilbong WHERE code = tb_kospi."코드" ORDER BY date DESC LIMIT 1) as rsi
        FROM tb_kospi
    """
    
    if shcode:
        sql = """
            SELECT 
                "코드", "종목명", "현재가", "등락률", "시가총액",
                (SELECT ROUND(rsi14, 0) FROM tb_ilbong WHERE code = tb_kospi."코드" ORDER BY date DESC LIMIT 1) as rsi
            FROM tb_kospi WHERE "코드" = ?
        """
        res = con.execute(sql, [shcode]).fetchall()
    else:
        res = con.execute(sql).fetchall()
        
    con.close()
    return res


def select_tb_kospi8(code=None):
    """MariaDB tb_kospi 조회 (views.py 호출용)"""
    with engine.connect() as conn:
        if code:
            query = text("""SELECT 코드, 종목명, 현재가, 등락률, 시가총액, 매출, 영업이익, 배당금, 외국인, PER, 
                            concat(replace(replace(시장, '코스피', ''), '코스닥', 'Q'), 순위) as 순위, '' as 섹터,
                            (SELECT ROUND(rsi14, 0) FROM tb_ilbong WHERE code = tb_kospi.코드 ORDER BY date DESC LIMIT 1) as rsi 
                            FROM tb_kospi WHERE 코드 = :code""")
            result = conn.execute(query, {"code": code})
        else:
            query = text("""SELECT 코드, 종목명, 현재가, 등락률, 시가총액, 매출, 영업이익, 배당금, 외국인, PER, 
                            concat(replace(replace(시장, '코스피', ''), '코스닥', 'Q'), 순위) as 순위, '' as 섹터,
                            (SELECT ROUND(rsi14, 0) FROM tb_ilbong WHERE code = tb_kospi.코드 ORDER BY date DESC LIMIT 1) as rsi 
                            FROM tb_kospi""")
            result = conn.execute(query)
        return [tuple(row) for row in result.fetchall()]



def select_tb_basic(code=None):
    """MariaDB tb_basic 조회 (views.py 호출용)"""
    with engine.connect() as conn:
        query = text("SELECT * FROM tb_basic WHERE 코드 = :code") if code else text("SELECT * FROM tb_basic")
        result = conn.execute(query, {"code": code} if code else {})
        return [tuple(row) for row in result.fetchall()]


def create_tb_basic8():
    with engine.connect() as conn:
        # 테이블 삭제
        conn.execute(text("DROP TABLE IF EXISTS tb_basic"))

        # 테이블 생성
        sql_create = '''
        CREATE TABLE IF NOT EXISTS tb_basic (
            코드 VARCHAR(20) PRIMARY KEY,
            종목명 VARCHAR(100),
            corp_code VARCHAR(20),
            섹터 VARCHAR(50),
            매출202201 BIGINT, 영업이익202201 BIGINT, 매출202202 BIGINT, 영업이익202202 BIGINT, 매출202203 BIGINT, 영업이익202203 BIGINT, 매출202204 BIGINT, 영업이익202204 BIGINT,
            매출202301 BIGINT, 영업이익202301 BIGINT, 매출202302 BIGINT, 영업이익202302 BIGINT, 매출202303 BIGINT, 영업이익202303 BIGINT, 매출202304 BIGINT, 영업이익202304 BIGINT,
            매출202401 BIGINT, 영업이익202401 BIGINT, 매출202402 BIGINT, 영업이익202402 BIGINT, 매출202403 BIGINT, 영업이익202403 BIGINT, 매출202404 BIGINT, 영업이익202404 BIGINT,
            매출202501 BIGINT, 영업이익202501 BIGINT, 매출202502 BIGINT, 영업이익202502 BIGINT, 매출202503 BIGINT, 영업이익202503 BIGINT, 매출202504 BIGINT, 영업이익202504 BIGINT,
            매출202601 BIGINT, 영업이익202601 BIGINT, 매출202602 BIGINT, 영업이익202602 BIGINT, 매출202603 BIGINT, 영업이익202603 BIGINT, 매출202604 BIGINT, 영업이익202604 BIGINT
        );
        '''
        conn.execute(text(sql_create))

        # KOSPI 데이터 삽입 (이미 tb_kospi 테이블이 있다고 가정)
        conn.execute(text('''
        INSERT INTO tb_basic (코드, 종목명)
        SELECT 코드, 종목명 FROM tb_kospi
        '''))

        # XML -> corp_code 매핑
        xml_path = os.path.join(base_dir, "CORPCODE.xml")
        tree = ET.parse(xml_path)
        root = tree.getroot()
        mapping = {item.find("stock_code").text.strip(): item.find("corp_code").text.strip()
                   for item in root.findall("list") if item.find("stock_code") is not None}

        for stock_code, corp_code in mapping.items():
            conn.execute(
                text("UPDATE tb_basic SET corp_code = :corp WHERE 코드 = :code"),
                {"corp": corp_code, "code": stock_code}
            )


        # DART API 분기 실적 업데이트 (기존 로직 그대로)
        API_KEY = "c2bc2e5748c3279f4b75fd9508b4e8e8145ada4b"
        REPRT_MAP = {1: "11013", 2: "11012", 3: "11014", 4: "11011"}

        def fetch_dart_quarter(corp_code, year, quarter):
            url = "https://opendart.fss.or.kr/api/fnlttSinglAcnt.json"
            params = {"crtfc_key": API_KEY, "corp_code": corp_code, "bsns_year": str(year), "reprt_code": REPRT_MAP[quarter]}
            r = requests.get(url, params=params).json()
            if r.get("status") != "000":
                return None, None
            sales, op = None, None
            for item in r.get("list", []):
                val = item.get("thstrm_amount", "0").replace(",", "")
                v = int(val) if val and val != '-' else 0
                if item.get("account_nm") == "매출액":
                    sales = v
                elif item.get("account_nm") == "영업이익":
                    op = v
            return sales, op

        rows = conn.execute(text("SELECT 코드, corp_code FROM tb_basic")).fetchall()

        cnt = 0
        for stock_code, corp_code in rows:
            cnt += 1
            if cnt >= 1:
                print(str(cnt) + '\t' + stock_code + '\t' + time.strftime("%H:%M", time.localtime()))
                if not corp_code:
                    continue
                update_dict = {}
                for year in range(2022, 2027):
                    for q in range(1, 5):
                        sales, op = fetch_dart_quarter(corp_code, year, q)
                        update_dict[f"매출{year}{q:02d}"] = sales
                        update_dict[f"영업이익{year}{q:02d}"] = op
                set_clause = ", ".join([f"{k}=:{k}" for k in update_dict.keys()])
                params = update_dict.copy()
                params["code"] = stock_code
                conn.execute(text(f"UPDATE tb_basic SET {set_clause} WHERE 코드 = :code"), params)

                conn.commit()

    print("[ALL DONE] tb_basic 생성 및 분기 실적 업데이트 완료")







def create_tb_basic():
    """
    DuckDB를 사용하여 tb_basic 테이블 생성 및 실적 데이터를 업데이트합니다.
    """
    with duckdb.connect(db_path) as conn:
        # 1. 테이블 초기화 (DuckDB는 DROP/CREATE 방식 사용)
        conn.execute("DROP TABLE IF EXISTS tb_basic")
        
        # 2. 테이블 생성 (DuckDB 문법에 맞게 조정)
        sql_create = '''
        CREATE TABLE tb_basic (
            코드 VARCHAR PRIMARY KEY,
            종목명 VARCHAR,
            corp_code VARCHAR,
            섹터 VARCHAR,
            매출202201 BIGINT, 영업이익202201 BIGINT, 매출202202 BIGINT, 영업이익202202 BIGINT, 매출202203 BIGINT, 영업이익202203 BIGINT, 매출202204 BIGINT, 영업이익202204 BIGINT,
            매출202301 BIGINT, 영업이익202301 BIGINT, 매출202302 BIGINT, 영업이익202302 BIGINT, 매출202303 BIGINT, 영업이익202303 BIGINT, 매출202304 BIGINT, 영업이익202304 BIGINT,
            매출202401 BIGINT, 영업이익202401 BIGINT, 매출202402 BIGINT, 영업이익202402 BIGINT, 매출202403 BIGINT, 영업이익202403 BIGINT, 매출202404 BIGINT, 영업이익202404 BIGINT,
            매출202501 BIGINT, 영업이익202501 BIGINT, 매출202502 BIGINT, 영업이익202502 BIGINT, 매출202503 BIGINT, 영업이익202503 BIGINT, 매출202504 BIGINT, 영업이익202504 BIGINT,
            매출202601 BIGINT, 영업이익202601 BIGINT, 매출202602 BIGINT, 영업이익202602 BIGINT, 매출202603 BIGINT, 영업이익202603 BIGINT, 매출202604 BIGINT, 영업이익202604 BIGINT
        );
        '''
        conn.execute(sql_create)

        # 3. KOSPI 데이터 복사 (tb_kospi가 같은 DuckDB 내에 있다고 가정)
        # 만약 tb_kospi가 MariaDB에 있다면 DataFrame으로 읽어와서 insert 해야 합니다.
        try:
            conn.execute("INSERT INTO tb_basic (코드, 종목명) SELECT 코드, 종목명 FROM tb_kospi")
        except Exception as e:
            print("⚠️ tb_kospi 조회 실패: MariaDB에서 데이터를 가져와야 할 수도 있습니다.")

        # 4. XML -> corp_code 매핑 및 업데이트
        xml_path = os.path.join(base_dir, "CORPCODE.xml")
        if os.path.exists(xml_path):
            tree = ET.parse(xml_path)
            root = tree.getroot()
            # stock_code가 있는 것만 추출
            mapping = []
            for item in root.findall("list"):
                s_code = item.findtext("stock_code").strip()
                c_code = item.findtext("corp_code").strip()
                if s_code:
                    mapping.append({'code': s_code, 'corp': c_code})
            
            # DataFrame을 활용한 일괄 업데이트용 임시 테이블 활용
            df_map = pd.DataFrame(mapping)
            conn.execute("CREATE TEMPORARY TABLE temp_map AS SELECT * FROM df_map")
            conn.execute("""
                UPDATE tb_basic 
                SET corp_code = temp_map.corp 
                FROM temp_map 
                WHERE tb_basic.코드 = temp_map.code
            """)
            conn.execute("DROP TABLE temp_map")

        # 5. DART API 실적 업데이트 (기본 로직 유지하되 DuckDB 커넥션 사용)
        API_KEY = "c2bc2e5748c3279f4b75fd9508b4e8e8145ada4b"
        REPRT_MAP = {1: "11013", 2: "11012", 3: "11014", 4: "11011"}

        def fetch_dart_quarter(corp_code, year, quarter):
            url = "https://opendart.fss.or.kr/api/fnlttSinglAcnt.json"
            params = {"crtfc_key": API_KEY, "corp_code": corp_code, "bsns_year": str(year), "reprt_code": REPRT_MAP[quarter]}
            try:
                r = requests.get(url, params=params, timeout=10).json()
                if r.get("status") != "000": return None, None
                sales, op = 0, 0
                for item in r.get("list", []):
                    val = item.get("thstrm_amount", "0").replace(",", "")
                    v = int(val) if val and val not in ['-', ''] else 0
                    if item.get("account_nm") == "매출액": sales = v
                    elif item.get("account_nm") == "영업이익": op = v
                return sales, op
            except:
                return None, None

        # 실적 업데이트 대상 조회
        rows = conn.execute("SELECT 코드, corp_code FROM tb_basic WHERE corp_code IS NOT NULL").fetchall()

        for cnt, (stock_code, corp_code) in enumerate(rows, 1):
            print(f"[{cnt}/{len(rows)}] {stock_code} 업데이트 중... {time.strftime('%H:%M')}")
            
            update_data = {}
            # 예시로 2024년까지만 루프 (필요에 따라 범위 조절)
            for year in range(2022, 2025): 
                for q in range(1, 5):
                    sales, op = fetch_dart_quarter(corp_code, year, q)
                    if sales is not None:
                        update_data[f"매출{year}{q:02d}"] = sales
                        update_data[f"영업이익{year}{q:02d}"] = op
            
            if update_data:
                set_clause = ", ".join([f"{k} = ?" for k in update_data.keys()])
                values = list(update_data.values()) + [stock_code]
                conn.execute(f"UPDATE tb_basic SET {set_clause} WHERE 코드 = ?", values)

    print("[ALL DONE] tb_basic DuckDB 생성 및 업데이트 완료")





























def create_db():
    create_tb_basic()
    create_tb_gwansim_group()
    create_tb_ilbong()
    create_tb_checkbox()
    
























def create_tb_gwansim_group():
    """
    관심그룹 및 관심종목 관련 테이블/시퀀스/인덱스를 생성합니다.
    """
    # 1. 시퀀스 및 테이블 생성 SQL
    setup_queries = [
        # 그룹 ID 자동 생성을 위한 시퀀스
        "CREATE SEQUENCE IF NOT EXISTS seq_group_id START 1;",
        
        # 관심 그룹 테이블
        """
        CREATE TABLE IF NOT EXISTS tb_gwansim_group (
            group_id INTEGER PRIMARY KEY,
            group_name VARCHAR NOT NULL,
            order_no INTEGER DEFAULT 0,
            reg_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # 관심 종목 테이블 (외래키 제외, 성능 중심)
        """
        CREATE TABLE IF NOT EXISTS tb_gwansim_stock (
            group_id INTEGER,
            shcode VARCHAR NOT NULL,
            order_no INTEGER DEFAULT 0,
            reg_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (group_id, shcode)
        );
        """,
        
        # 2. 인덱스 생성 (조회 성능 최적화)
        # 특정 그룹의 종목을 불러올 때 검색 속도를 비약적으로 높여줍니다.
        "CREATE INDEX IF NOT EXISTS idx_gwansim_stock_group ON tb_gwansim_stock (group_id);"
    ]

    try:
        with duckdb.connect(db_path) as conn:
            for sql in setup_queries:
                conn.execute(sql)
        print("✅ 관심 종목 시스템 테이블 및 인덱스 생성 완료!")
        return True
    except Exception as e:
        print(f"❌ 테이블 생성 중 오류 발생: {e}")
        return False





def update_gwansim_group_order(group_id_list):
    """
    관심그룹의 순서를 1부터 차례대로 재부여합니다.
    group_id_list: ['1', '3', '2']와 같이 정렬된 그룹 ID 리스트
    """
    try:
        with duckdb.connect(db_path) as conn:
            for index, g_id in enumerate(group_id_list):
                new_order = index + 1
                conn.execute("""
                    UPDATE tb_gwansim_group 
                    SET order_no = ? 
                    WHERE group_id = ?
                """, [new_order, int(g_id)])
            return True
    except Exception as e:
        print(f"그룹 DB 순서 업데이트 중 오류 발생: {e}")
        return False




def delete_gwansim_group(group_id):

    con = duckdb.connect(db_path)
    try:
        gid = int(group_id)
        
        # ? 쓰지 말고 f-string으로 값을 직접 넣어서 실행 (DuckDB 엔진 에러 회피)
        con.execute(f"DELETE FROM tb_gwansim_stock WHERE group_id = {gid}")
        con.execute(f"DELETE FROM tb_gwansim_group WHERE group_id = {gid}")
        
        con.close()
        return True
    except Exception as e:
        print(f"그룹 삭제 중 DB 오류 발생: {e}")
        if con:
            con.close()
        return False


def update_gwansim_stock_order(group_id, shcode_list):
    """
    관심종목의 순서를 1부터 차례대로 재부여합니다.
    shcode_list: ['005930', '068270', ...] 정렬된 리스트
    """
    try:
        # db_path는 기존 db.py에 설정된 경로를 사용합니다.
        with duckdb.connect(db_path) as conn:
            for index, shcode in enumerate(shcode_list):
                new_order = index + 1
                conn.execute("""
                    UPDATE tb_gwansim_stock 
                    SET order_no = ? 
                    WHERE group_id = ? AND shcode = ?
                """, [new_order, int(group_id), shcode])
            return True
    except Exception as e:
        print(f"DB 순서 업데이트 중 오류 발생: {e}")
        return False








def insert_tb_gwansim_stock(group_id, shcode):
    # 테이블 생성 쿼리 (가급적 프로그램 시작 시점에 한 번 하는 게 좋지만, 유지함)
    setup_sql = """
        CREATE TABLE IF NOT EXISTS tb_gwansim_stock (
            group_id INTEGER,
            shcode VARCHAR,
            order_no INTEGER,
            reg_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (group_id, shcode)
        );
    """

    try:
        # group_id 타입을 인트로 강제 변환 (문자열 방지)
        gid = int(group_id)
        
        with duckdb.connect(db_path) as conn:
            # 1. 테이블 생성 확인
            conn.execute(setup_sql)
            
            # 2. 순번(order_no) 계산을 밖으로 뺌 (서브쿼리 버그 방지)
            # 데이터가 하나도 없을 때를 대비해 명시적 처리
            res = conn.execute("SELECT MAX(order_no) FROM tb_gwansim_stock WHERE group_id = ?", [gid]).fetchone()
            next_no = (res[0] if res and res[0] is not None else 0) + 1
            
            # 3. 데이터 삽입 (가장 단순한 형태로 실행)
            conn.execute(
                "INSERT INTO tb_gwansim_stock (group_id, shcode, order_no) VALUES (?, ?, ?)",
                [gid, str(shcode), next_no]
            )
            
            print(f"DEBUG: 그룹({gid})에 종목({shcode}) 추가 완료 (순번: {next_no})")
            return True

    except duckdb.ConstraintException:
        print(f"DEBUG: 이미 등록된 종목입니다. (Group: {group_id}, Code: {shcode})")
        return False
    except Exception as e:
        # 여기서 'vector of size 0' 에러가 나면 DB 파일이 잠겼거나 세션이 꼬인 것임
        print(f"ERROR: insert_tb_gwansim_stock 오류: {e}")
        return False


def delete_tb_gwansim_stock(group_id, shcode):
    """
    특정 관심 그룹에서 특정 종목을 삭제합니다.
    """
    sql = "DELETE FROM tb_gwansim_stock WHERE group_id = ? AND shcode = ?"
    try:
        with duckdb.connect(db_path) as conn:
            conn.execute(sql, [int(group_id), shcode])
            return True
    except Exception as e:
        print(f"ERROR: delete_tb_gwansim_stock 오류: {e}")
        return False







def insert_tb_gwansim_group_st(group_name, codes):

    # 1. DB 연결 및 테이블/시퀀스 준비 (존재하면 건너뜀)
    conn = duckdb.connect(db_path)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tb_gwansim_group (
            group_id INTEGER PRIMARY KEY,
            group_name VARCHAR NOT NULL,
            order_no INTEGER DEFAULT 0,
            reg_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 2. 값 계산: 쿼리 결과를 바로 꺼내서 정수 변환 (None 처리)
    result = conn.execute("SELECT MAX(group_id), MAX(order_no) FROM tb_gwansim_group").fetchone()
    max_id = result[0] if result[0] is not None else 0
    max_order = result[1] if result[1] is not None else 0
    
    new_id = max_id + 1
    new_order = max_order + 1
    
    # 3. 데이터 삽입
    conn.execute("""
        INSERT INTO tb_gwansim_group (group_id, group_name, order_no, reg_date)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    """, [new_id, group_name, new_order])
    

    
    print(f"생성된 group_id: {new_id}")
    
    for code in codes:
        result = conn.execute("SELECT MAX(order_no) FROM tb_gwansim_stock WHERE group_id = ?", [new_id]).fetchone()
        next_no = (result[0] if result and result[0] is not None else 0) + 1
            
        conn.execute("INSERT INTO tb_gwansim_stock (group_id, shcode, order_no) VALUES (?, ?, ?)",  [new_id, code, next_no])

    conn.close()





















def insert_tb_gwansim_group(group_name):

    sql = """
        INSERT INTO tb_gwansim_group (group_id, group_name, order_no, reg_date)
        SELECT
            COALESCE(MAX(group_id), 0) + 1,
            ?,
            COALESCE(MAX(order_no), 0) + 1,
            CURRENT_TIMESTAMP
        FROM tb_gwansim_group
    """

    try:
        with duckdb.connect(db_path) as conn:
            conn.execute(sql, [group_name])

    except duckdb.CatalogException:
        with duckdb.connect(db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tb_gwansim_group (
                    group_id INTEGER PRIMARY KEY,
                    group_name VARCHAR NOT NULL,
                    order_no INTEGER DEFAULT 0,
                    reg_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.execute(sql, [group_name])
            


            

def select_tb_gwansim_group():
    try:
        with duckdb.connect(db_path) as conn:
            # group_id, group_name을 리스트로 return
            return conn.execute("""
                SELECT group_id, group_name 
                FROM tb_gwansim_group 
                ORDER BY order_no ASC
            """).fetchall()
    except duckdb.CatalogException:
        return []




def select_tb_gwansim_stock8(group_id):

    con = duckdb.connect(db_path)
    
    # 💡 서브쿼리를 완전히 지워버리고 A.rsi (또는 A."RSI") 데이터를 1:1 매칭해 가져옵니다.
    sql = """
           SELECT A.*
            FROM tb_gwansim_stock B
            LEFT JOIN tb_kospi A ON B.shcode = A."코드"
            WHERE B.group_id = ?
            ORDER BY B.order_no ASC
    """
    try:
        res = con.execute(sql, [int(group_id)]).fetchall()
    except Exception as e:
        print(f"DB 순서 업데이트 중 오류 발생: {e}")
    finally:
        con.close()
    return res








def select_tb_gwansim_stock(group_id):
    con = duckdb.connect(db_path)
    
    # 별칭: A=tb_kospi, B=tb_gwansim_stock, C=tb_ilbong(최신 RSI)
    sql = """
        SELECT 
            A."코드", A."종목명", A."현재가", A."등락률", A."시가총액", C.rsi
        FROM tb_gwansim_stock B
        LEFT JOIN tb_kospi A ON B.shcode = A."코드"
        LEFT JOIN (
            SELECT code, ROUND(rsi14, 0) as rsi
            FROM (
                SELECT code, rsi14, ROW_NUMBER() OVER (PARTITION BY code ORDER BY date DESC) as rn
                FROM tb_ilbong
            ) WHERE rn = 1
        ) C ON A."코드" = C.code
        WHERE B.group_id = ?
        ORDER BY B.order_no ASC
    """
    
    try:
        res = con.execute(sql, [int(group_id)]).fetchall()
    except Exception as e:
        print(f"관심종목 조회 중 오류 발생: {e}")
        res = []
    finally:
        con.close()
    return res






















# db.py 내부 적절한 위치에 추가

def update_check_setting(settings_json_str):
    """
    체크박스 설정값을 업데이트(덮어쓰기)합니다.
    최초 실행 시 테이블이 없다면 자동으로 생성(CREATE)하고, 
    평소에는 매번 들어오는 설정값으로 데이터를 갱신(UPDATE)합니다.
    """
    con = duckdb.connect(db_path)
    try:
        # 1. [최초 1회만 작동] 테이블이 없을 때만 테이블 생성
        con.execute("""
            CREATE TABLE IF NOT EXISTS tb_check_setting (
                setting_id TEXT PRIMARY KEY,
                settings_json TEXT
            )
        """)
        
        # 2. [평소에 작동] 'default' 행에 JSON 설정값 문자열을 덮어쓰기 (Update/Insert 자동 처리)
        con.execute("""
            INSERT OR REPLACE INTO tb_check_setting (setting_id, settings_json)
            VALUES ('default', $1)
        """, [settings_json_str])
        
        print("[DuckDB] tb_check_setting 체크 설정 업데이트 완료")
    except Exception as e:
        print(f"[DuckDB] 설정 업데이트 중 오류 발생: {e}")
    finally:
        con.close()


def select_check_setting():
    """
    DuckDB에 저장된 체크박스 설정값을 읽어옵니다. (SELECT)
    테이블이 아직 없거나 데이터가 비어 있다면 빈 구조인 '{}' 문자열을 반환합니다.
    """
    con = duckdb.connect(db_path)
    try:
        res = con.execute("""
            SELECT settings_json FROM tb_check_setting WHERE setting_id = 'default'
        """).fetchone()
        
        return res[0] if res else "{}"
    except Exception as e:
        # 최초 로딩 시 테이블이 아예 없는 에러 상태를 안전하게 방어하기 위해 빈 값 반환
        return "{}"
    finally:
        con.close()












































def create_tb_ilbong():
    
    con = duckdb.connect(db_path)
    con.execute("DROP TABLE IF EXISTS tb_ilbong")
    
    con.execute("""
        CREATE TABLE tb_ilbong (
            code VARCHAR,
            date VARCHAR,
            open INTEGER,
            high INTEGER,
            low INTEGER,
            close INTEGER,
            volume BIGINT,
            ma5 DOUBLE,
            ma20 DOUBLE,
            ma60 DOUBLE,
            ma120 DOUBLE,
            ema26 DOUBLE,            
            rsi14 DOUBLE,
            macd DOUBLE,
            macd9 DOUBLE,
            bol_u DOUBLE,
            bol_l DOUBLE,
            bol_size VARCHAR,
            bol_dolpa VARCHAR,
            ilmok_a DOUBLE,
            ilmok_b DOUBLE,
            ilmok_dolpa VARCHAR,
            ilmok_yang VARCHAR,
            개인 DOUBLE,
            외국인 DOUBLE,
            기관 DOUBLE,
            연기금 DOUBLE,
            사모펀드 DOUBLE,
            프로그램 DOUBLE,
            공매도수량 DOUBLE,
            공매도대금 DOUBLE,
            PRIMARY KEY (code, date)
        )
    """)
    
    # 4. 인덱스 생성 (조회 속도 최적화)
    # 인덱스: 종목(code), 날짜(date)로 검색할 때 성능 향상
    con.execute("CREATE INDEX idx_ilbong_code ON tb_ilbong (code)")
    con.execute("CREATE INDEX idx_ilbong_date ON tb_ilbong (date)")
    
    # 5. 연결 종료
    con.close()
    
    print("DuckDB: tb_ilbong 테이블 및 인덱스 생성 완료")














def insert_tb_ilbong(ilbong_list):
    con = duckdb.connect(db_path)
    
    sql = """
        INSERT OR REPLACE INTO tb_ilbong (
            code, date, open, high, low, close, volume, 
            ma5, ma20, ma60, ma120, ema26,
            rsi14, macd, macd9, bol_u, bol_l, bol_size, bol_dolpa, 
            ilmok_a, ilmok_b, ilmok_dolpa, ilmok_yang,
            개인, 외국인, 기관, 연기금, 사모펀드, 프로그램, 공매도수량, 공매도대금
        ) VALUES (
            $code, $date, $open, $high, $low, $close, $volume, 
            $ma5, $ma20, $ma60, $ma120, $ema26,
            $rsi14, $macd, $macd9, $bol_u, $bol_l, $bol_size, $bol_dolpa, 
            $ilmok_a, $ilmok_b, $ilmok_dolpa, $ilmok_yang,
            $개인, $외국인, $기관, $연기금, $사모펀드, $프로그램, $공매도수량, $공매도대금
        )
    """
    
    con.executemany(sql, ilbong_list)
    con.close()




def insert_tb_ilbong_remain():
    ilbong = select_tb_ilbong('005930')

    if not ilbong:
        return []

    last_date = ilbong[-1]['date']

    sql = """
        SELECT A.코드, A.종목명
        FROM TB_KOSPI A
        LEFT JOIN (
            SELECT code, MAX(date) AS date
            FROM tb_ilbong
            GROUP BY code
        ) B
        ON A.코드 = B.code
        WHERE B.date IS NULL
           OR B.date <> ?
        ORDER BY A.시장 DESC, A.순위
    """

    with duckdb.connect(db_path) as con:
        list_remain = con.execute(sql, [last_date]).fetchall()

    return list_remain




# --- [복구] 삭제 및 유틸리티 함수 ---

def delete_db_1day(code, date):
    """SQLite 특정일 삭제"""
    with sqlite3.connect(db_path) as conn:
        conn.execute(f"DELETE FROM '{code}' WHERE DATE = '{date}'")
        conn.commit()

def delete_db_days(code, date1, date2):
    """SQLite 범위 삭제 (복구 완료)"""
    with sqlite3.connect(db_path) as con:
        con.execute(f"DELETE FROM '{code}' WHERE DATE BETWEEN '{date1}' AND '{date2}'")
        con.commit()

def drop_db(code):
    """SQLite 테이블 삭제"""
    with sqlite3.connect(db_path) as conn:
        conn.execute(f"DROP TABLE IF EXISTS '{code}'")
        conn.commit()
        




























def select_st_macd(mode: str):

    con = duckdb.connect(db_path)

    buy_condition = """
        1=1
        AND HIST_10 < HIST_3
        AND HIST_7 < HIST_3
        AND HIST_7 < HIST_1
        AND HIST_5 < HIST_1
        AND HIST_3 < HIST_1
        AND HIST_12 < HIST
        AND HIST_5 < HIST
        AND HIST_3 < HIST
        AND HIST_2 < HIST
        AND HIST_1 < HIST
        AND ABS(HIST) / GREATEST(ABS(MACD9), 0.001) <= 0.1
    """

    sell_condition = """
        1=1
        AND HIST_10 > HIST_3
        AND HIST_7 > HIST_3
        AND HIST_7 > HIST_1
        AND HIST_5 > HIST_1
        AND HIST_3 > HIST_1
        AND HIST_12 > HIST
        AND HIST_5 > HIST
        AND HIST_3 > HIST
        AND HIST_2 > HIST
        AND HIST_1 > HIST
        AND ABS(HIST) / GREATEST(ABS(MACD9), 0.001) <= 0.1
    """

    if mode == "buy":

        condition = f"""
            ROW_NO = 1
            AND ({buy_condition})
        """

    elif mode == "sell":

        condition = f"""
            ROW_NO = 1
            AND ({sell_condition})
        """

    else:

        condition = f"""
            ROW_NO = 1
            AND NOT ({buy_condition})
            AND NOT ({sell_condition})
        """

    query = f"""
WITH A AS (
    SELECT
        CODE,
        DATE,
        MACD,
        MACD9,

        MACD - MACD9 AS HIST,

        LAG(MACD - MACD9, 1) OVER (PARTITION BY CODE ORDER BY DATE) AS HIST_1,
        LAG(MACD - MACD9, 2) OVER (PARTITION BY CODE ORDER BY DATE) AS HIST_2,
        LAG(MACD - MACD9, 3) OVER (PARTITION BY CODE ORDER BY DATE) AS HIST_3,
        LAG(MACD - MACD9, 5) OVER (PARTITION BY CODE ORDER BY DATE) AS HIST_5,
        LAG(MACD - MACD9, 7) OVER (PARTITION BY CODE ORDER BY DATE) AS HIST_7,
        LAG(MACD - MACD9, 10) OVER (PARTITION BY CODE ORDER BY DATE) AS HIST_10,
        LAG(MACD - MACD9, 12) OVER (PARTITION BY CODE ORDER BY DATE) AS HIST_12,

        ROW_NUMBER() OVER (
            PARTITION BY CODE
            ORDER BY DATE DESC
        ) AS ROW_NO

    FROM TB_ILBONG
)

SELECT
    A.CODE AS code,
    K."종목명" AS name
FROM A
JOIN TB_KOSPI K
  ON A.CODE = K."코드"
WHERE
    {condition}
ORDER BY CAST(REPLACE(K."시가총액", ',', '') AS BIGINT) DESC, A.CODE
"""

    df = con.execute(query).df()

    con.close()

    return df.to_dict("records")












def select_st_macd_ilbong(code_list: list):
    """2. 요청받은 종목들의 전체 일봉 데이터를 가져오는 함수 (필터링 제거)"""
    con = duckdb.connect(db_path)
    # 쉼표로 구분된 코드 문자열 생성
    codes_str = ", ".join([f"'{c}'" for c in code_list])
    
    query = f"""
        SELECT code, date, macd, macd9 
        FROM tb_ilbong 
        WHERE code IN ({codes_str})
        ORDER BY code, date ASC
    """
    df = con.execute(query).df()
    con.close()
    
    # NaN 처리
    df = df.replace({np.nan: None})
    
    # [최적화] 컬럼 중심 구조(Columnar)로 반환
    return {
        code: {
            'date': group['date'].tolist(),
            'macd': group['macd'].tolist(),
            'macd9': group['macd9'].tolist()
        } for code, group in df.groupby('code')
    }





def select_st_rsi(mode: str):

    con = duckdb.connect(db_path)

    if mode == "buy":

        condition = """
            ROW_NO = 1
            AND PREV_RSI < 30
            AND RSI14 > PREV_RSI
        """

    elif mode == "sell":

        condition = """
            ROW_NO = 1
            AND PREV_RSI > 70
            AND RSI14 < PREV_RSI
        """

    else:
        condition = """
            ROW_NO = 1
            AND NOT (
                (PREV_RSI < 30 AND RSI14 > PREV_RSI)
                OR
                (PREV_RSI > 70 AND RSI14 < PREV_RSI)
            )
        """




        

    query = f"""
        WITH T AS (
            SELECT CODE, DATE, RSI14,
                LAG(RSI14) OVER (
                    PARTITION BY CODE
                    ORDER BY DATE
                ) AS PREV_RSI,

                ROW_NUMBER() OVER (
                    PARTITION BY CODE
                    ORDER BY DATE DESC
                ) AS ROW_NO
            FROM TB_ILBONG
        )
        SELECT
            T.CODE AS code,
            K."종목명" AS name
        FROM T
        JOIN TB_KOSPI K
          ON T.CODE = K."코드"
        WHERE {condition}
        ORDER BY CAST(REPLACE(K."시가총액", ',', '') AS BIGINT) DESC
    """

    df = con.execute(query).df()

    con.close()

    return df.to_dict("records")







def select_st_rsi_ilbong(code_list: list):
    con = duckdb.connect(db_path)

    codes_str = ", ".join([f"'{c}'" for c in code_list])

    query = f"""
        SELECT code, date, rsi14
        FROM tb_ilbong
        WHERE code IN ({codes_str})
        ORDER BY code, date ASC
    """

    df = con.execute(query).df()
    con.close()

    df = df.replace({np.nan: None})

    return {
        code: {
            'date': group['date'].tolist(),
            'rsi14': group['rsi14'].tolist()
        }
        for code, group in df.groupby('code')
    }








def select_st_bol(mode: str):

    con = duckdb.connect(db_path)


    buy_condition = """
        POS <= 0.15
        AND POS15 > POS7
        AND POS10 > POS3
        AND POS7 > POS3
        AND POS5 > POS1
        AND POS1 < POS
        AND CLOSE > CLOSE1
    """

    sell_condition = """
        POS >= 0.85
        AND POS15 < POS7
        AND POS10 < POS3
        AND POS7 < POS3
        AND POS5 < POS1
        AND POS1 > POS
        AND CLOSE < CLOSE1
    """


    if mode == "buy":
        condition = f"""
            ROW_NO = 1
            AND ({buy_condition})
        """

    elif mode == "sell":
        condition = f"""
            ROW_NO = 1
            AND ({sell_condition})
        """

    else:
        condition = f"""
            ROW_NO = 1
            AND NOT ({buy_condition})
            AND NOT ({sell_condition})
        """

    query = f"""
WITH A AS (
    SELECT CODE, DATE, CLOSE, BOL_U, BOL_L,

           (CLOSE - BOL_L) / NULLIF(BOL_U - BOL_L,0) AS POS,

           LAG(CLOSE,1) OVER (PARTITION BY CODE ORDER BY DATE) AS CLOSE1,

           LAG((CLOSE - BOL_L) / NULLIF(BOL_U - BOL_L,0), 1) OVER (PARTITION BY CODE ORDER BY DATE) AS POS1,
           LAG((CLOSE - BOL_L) / NULLIF(BOL_U - BOL_L,0), 3) OVER (PARTITION BY CODE ORDER BY DATE) AS POS3,
           LAG((CLOSE - BOL_L) / NULLIF(BOL_U - BOL_L,0), 5) OVER (PARTITION BY CODE ORDER BY DATE) AS POS5,
           LAG((CLOSE - BOL_L) / NULLIF(BOL_U - BOL_L,0), 7) OVER (PARTITION BY CODE ORDER BY DATE) AS POS7,
           LAG((CLOSE - BOL_L) / NULLIF(BOL_U - BOL_L,0),10) OVER (PARTITION BY CODE ORDER BY DATE) AS POS10,
           LAG((CLOSE - BOL_L) / NULLIF(BOL_U - BOL_L,0),15) OVER (PARTITION BY CODE ORDER BY DATE) AS POS15,

           ROW_NUMBER() OVER (PARTITION BY CODE ORDER BY DATE DESC) AS ROW_NO

    FROM TB_ILBONG
)
SELECT A.CODE AS code, K."종목명" AS name
FROM A
JOIN TB_KOSPI K
  ON A.CODE = K."코드"
WHERE
    {condition}
ORDER BY CAST(REPLACE(K."시가총액", ',', '') AS BIGINT) DESC
"""

    df = con.execute(query).df()
    con.close()
    return df.to_dict("records")






def select_st_bol_ilbong(code_list: list):
    con = duckdb.connect(db_path)

    codes_str = ", ".join([f"'{c}'" for c in code_list])

    query = f"""
        SELECT
            code,
            date,
            open,
            high,
            low,
            close,
            ma20,
            ma60,
            ma120,
            bol_u,
            bol_l
        FROM tb_ilbong
        WHERE code IN ({codes_str})
        ORDER BY code, date ASC
    """

    df = con.execute(query).df()
    con.close()

    df = df.replace({np.nan: None})

    return {
        code: {
            'date': group['date'].tolist(),
            'open': group['open'].tolist(),
            'high': group['high'].tolist(),
            'low': group['low'].tolist(),
            'close': group['close'].tolist(),
            'ma20': group['ma20'].tolist(),
            'ma60': group['ma60'].tolist(),
            'ma120': group['ma120'].tolist(),
            'bol_u': group['bol_u'].tolist(),
            'bol_l': group['bol_l'].tolist()
        }
        for code, group in df.groupby('code')
    }








def select_st_ilmok(mode: str):

    con = duckdb.connect(db_path)

    buy_condition = """
        ILMOK_DOLPA = '상향돌파'
        AND COALESCE(DOLPA3, '') != '상향돌파'
        AND COALESCE(DOLPA5, '') != '상향돌파'
        AND COALESCE(DOLPA10, '') != '상향돌파'
    """

    sell_condition = """
        ILMOK_DOLPA = '하향돌파'
        AND COALESCE(DOLPA3, '') != '하향돌파'
        AND COALESCE(DOLPA5, '') != '하향돌파'
        AND COALESCE(DOLPA10, '') != '하향돌파'
    """

    if mode == "buy":
        condition = f"""
            ROW_NO = 1
            AND ({buy_condition})
        """

    elif mode == "sell":
        condition = f"""
            ROW_NO = 1
            AND ({sell_condition})
        """

    else:
        condition = f"""
            ROW_NO = 1
            AND (
                (ILMOK_DOLPA NOT IN ('상향돌파', '하향돌파'))
                OR (ILMOK_DOLPA IS NULL)
                OR (
                    NOT ({buy_condition.replace('ROW_NO = 1 AND ', '')})
                    AND NOT ({sell_condition.replace('ROW_NO = 1 AND ', '')})
                )
            )
        """


    query = f"""
WITH A AS (
    SELECT CODE, DATE, ILMOK_DOLPA,
           LAG(ILMOK_DOLPA, 3) OVER (PARTITION BY CODE ORDER BY DATE) AS DOLPA3,
           LAG(ILMOK_DOLPA, 5) OVER (PARTITION BY CODE ORDER BY DATE) AS DOLPA5,
           LAG(ILMOK_DOLPA,10) OVER (PARTITION BY CODE ORDER BY DATE) AS DOLPA10,
           ROW_NUMBER() OVER (PARTITION BY CODE ORDER BY DATE DESC) AS ROW_NO
    FROM TB_ILBONG
)
SELECT A.CODE AS code, K."종목명" AS name
FROM A
JOIN TB_KOSPI K
  ON A.CODE = K."코드"
WHERE
    {condition}
ORDER BY CAST(REPLACE(K."시가총액", ',', '') AS BIGINT) DESC
"""

    df = con.execute(query).df()

    con.close()

    return df.to_dict("records")



def select_st_ilmok_ilbong(code_list: list):
    con = duckdb.connect(db_path)

    codes_str = ", ".join([f"'{c}'" for c in code_list])

    query = f"""
        SELECT
            code,
            date,
            open,
            high,
            low,
            close,
            ilmok_a,
            ilmok_b,
            ilmok_dolpa,
            ilmok_yang
        FROM tb_ilbong
        WHERE code IN ({codes_str})
        ORDER BY code, date ASC
    """

    df = con.execute(query).df()
    con.close()

    df = df.replace({np.nan: None})

    return {
        code: {
            'date': group['date'].tolist(),
            'open': group['open'].tolist(),
            'high': group['high'].tolist(),
            'low': group['low'].tolist(),
            'close': group['close'].tolist(),
            'ilmok_a': group['ilmok_a'].tolist(),
            'ilmok_b': group['ilmok_b'].tolist(),
            'ilmok_dolpa': group['ilmok_dolpa'].tolist(),
            'ilmok_yang': group['ilmok_yang'].tolist()
        }
        for code, group in df.groupby('code')
    }
















def select_st_vol(mode: str):

    con = duckdb.connect(db_path)



    buy_condition = """
        ROW_NO = 1

        -- 거래량 감소 후 오늘 급증
        AND VOL15 > VOL7
        AND VOL15 > VOL3
        AND VOL10 > VOL3
        AND VOL7 > VOL3
        AND VOL5 > VOL1
        AND VOL3 > VOL1
        AND VOL2 > VOL1

        -- 오늘 거래량 2배 이상
        AND VOLUME >= VOL1 * 2
    """

    sell_condition = """
        ROW_NO = 1

        -- 거래량 증가 후 오늘 급감
        AND VOL15 < VOL7
        AND VOL15 < VOL3
        AND VOL10 < VOL3
        AND VOL7 < VOL3
        AND VOL5 < VOL1
        AND VOL3 < VOL1
        AND VOL2 < VOL1

        -- 오늘 거래량 절반 이하
        AND VOLUME <= VOL1 * 0.5
    """

    if mode == "buy":
        condition = f"""
            {buy_condition}
        """

    elif mode == "sell":
        condition = f"""
            {sell_condition}
        """

    else:
        condition = f"""
            ROW_NO = 1
            AND NOT (
                ({buy_condition})
                OR
                ({sell_condition})
            )
        """
        
    query = f"""
WITH A AS (
    SELECT CODE, DATE, VOLUME,
           LAG(VOLUME, 1) OVER (PARTITION BY CODE ORDER BY DATE) AS VOL1,
           LAG(VOLUME, 2) OVER (PARTITION BY CODE ORDER BY DATE) AS VOL2,
           LAG(VOLUME, 3) OVER (PARTITION BY CODE ORDER BY DATE) AS VOL3,
           LAG(VOLUME, 5) OVER (PARTITION BY CODE ORDER BY DATE) AS VOL5,
           LAG(VOLUME, 7) OVER (PARTITION BY CODE ORDER BY DATE) AS VOL7,
           LAG(VOLUME,10) OVER (PARTITION BY CODE ORDER BY DATE) AS VOL10,
           LAG(VOLUME,15) OVER (PARTITION BY CODE ORDER BY DATE) AS VOL15,
           ROW_NUMBER() OVER (PARTITION BY CODE ORDER BY DATE DESC) AS ROW_NO
    FROM TB_ILBONG
)
SELECT A.CODE AS code, K."종목명" AS name
FROM A
JOIN TB_KOSPI K
  ON A.CODE = K."코드"
WHERE
    {condition}
ORDER BY CAST(REPLACE(K."시가총액", ',', '') AS BIGINT) DESC
"""

    df = con.execute(query).df()

    con.close()

    return df.to_dict("records")





def select_st_vol_ilbong(code_list: list):
    con = duckdb.connect(db_path)

    codes_str = ", ".join([f"'{c}'" for c in code_list])

    query = f"""
        SELECT
            code,
            date,
            open,
            high,
            low,
            close,
            volume,
            ma20
        FROM tb_ilbong
        WHERE code IN ({codes_str})
        ORDER BY code, date ASC
    """

    df = con.execute(query).df()
    con.close()

    df = df.replace({np.nan: None})

    return {
        code: {
            'date': group['date'].tolist(),
            'open': group['open'].tolist(),
            'high': group['high'].tolist(),
            'low': group['low'].tolist(),
            'close': group['close'].tolist(),
            'volume': group['volume'].tolist(),
            'ma20': group['ma20'].tolist()
        }
        for code, group in df.groupby('code')
    }












def select_st_ma5(mode: str):

    con = duckdb.connect(db_path)

    if mode == "buy":

        condition = """
            ROW_NO = 1

            -- 5일선이 20일선으로 접근(골든크로스 직전)
            AND DIFF15 < DIFF7
            AND DIFF15 < DIFF3
            AND DIFF10 < DIFF3
            AND DIFF7 < DIFF3
            AND DIFF5 < DIFF1
            AND DIFF3 < DIFF
            AND DIFF2 < DIFF
            AND DIFF1 < DIFF

            AND ABS(DIFF) / GREATEST(MA20, 1) <= 0.1
        """

    elif mode == "sell":

        condition = """
            ROW_NO = 1

            -- 5일선이 20일선으로 접근(데드크로스 직전)
            AND DIFF15 > DIFF7
            AND DIFF15 > DIFF3
            AND DIFF10 > DIFF3
            AND DIFF7 > DIFF3
            AND DIFF5 > DIFF1
            AND DIFF3 > DIFF
            AND DIFF2 > DIFF
            AND DIFF1 > DIFF

            AND ABS(DIFF) / GREATEST(MA20, 1) <= 0.1
        """

    else:

        condition = "ROW_NO = 1"

    query = f"""
WITH A AS (
    SELECT CODE, DATE, MA5, MA20,
           MA5 - MA20 AS DIFF,
           LAG(MA5 - MA20, 1) OVER (PARTITION BY CODE ORDER BY DATE) AS DIFF1,
           LAG(MA5 - MA20, 2) OVER (PARTITION BY CODE ORDER BY DATE) AS DIFF2,
           LAG(MA5 - MA20, 3) OVER (PARTITION BY CODE ORDER BY DATE) AS DIFF3,
           LAG(MA5 - MA20, 5) OVER (PARTITION BY CODE ORDER BY DATE) AS DIFF5,
           LAG(MA5 - MA20, 7) OVER (PARTITION BY CODE ORDER BY DATE) AS DIFF7,
           LAG(MA5 - MA20,10) OVER (PARTITION BY CODE ORDER BY DATE) AS DIFF10,
           LAG(MA5 - MA20,15) OVER (PARTITION BY CODE ORDER BY DATE) AS DIFF15,
           ROW_NUMBER() OVER (PARTITION BY CODE ORDER BY DATE DESC) AS ROW_NO
    FROM TB_ILBONG
)
SELECT A.CODE AS code, K."종목명" AS name
FROM A
JOIN TB_KOSPI K
  ON A.CODE = K."코드"
WHERE
    {condition}
ORDER BY CAST(REPLACE(K."시가총액", ',', '') AS BIGINT) DESC
"""

    df = con.execute(query).df()

    con.close()

    return df.to_dict("records")


def select_st_ma5_ilbong(code_list: list):
    con = duckdb.connect(db_path)

    codes_str = ", ".join([f"'{c}'" for c in code_list])

    query = f"""
        SELECT
            code,
            date,
            open,
            high,
            low,
            close,
            ma5,
            ma20
        FROM tb_ilbong
        WHERE code IN ({codes_str})
        ORDER BY code, date ASC
    """

    df = con.execute(query).df()
    con.close()

    df = df.replace({np.nan: None})

    return {
        code: {
            'date': group['date'].tolist(),
            'open': group['open'].tolist(),
            'high': group['high'].tolist(),
            'low': group['low'].tolist(),
            'close': group['close'].tolist(),
            'ma5': group['ma5'].tolist(),
            'ma20': group['ma20'].tolist()
        }
        for code, group in df.groupby('code')
    }










def select_st_ma20(mode: str):

    con = duckdb.connect(db_path)

    if mode == "buy":

        condition = """
            ROW_NO = 1

            -- 20일선이 60일선으로 접근(골든크로스 직전)
            AND DIFF15 < DIFF7
            AND DIFF15 < DIFF3
            AND DIFF10 < DIFF3
            AND DIFF7 < DIFF3
            AND DIFF5 < DIFF1
            AND DIFF3 < DIFF
            AND DIFF2 < DIFF
            AND DIFF1 < DIFF

            AND ABS(DIFF) / GREATEST(MA60, 1) <= 0.05
        """

    elif mode == "sell":

        condition = """
            ROW_NO = 1

            -- 20일선이 60일선으로 접근(데드크로스 직전)
            AND DIFF15 > DIFF7
            AND DIFF15 > DIFF3
            AND DIFF10 > DIFF3
            AND DIFF7 > DIFF3
            AND DIFF5 > DIFF1
            AND DIFF3 > DIFF
            AND DIFF2 > DIFF
            AND DIFF1 > DIFF

            AND ABS(DIFF) / GREATEST(MA60, 1) <= 0.05
        """

    else:

        condition = "ROW_NO = 1"

    query = f"""
WITH A AS (
    SELECT CODE, DATE, MA20, MA60,
           MA20 - MA60 AS DIFF,
           LAG(MA20 - MA60, 1) OVER (PARTITION BY CODE ORDER BY DATE) AS DIFF1,
           LAG(MA20 - MA60, 2) OVER (PARTITION BY CODE ORDER BY DATE) AS DIFF2,
           LAG(MA20 - MA60, 3) OVER (PARTITION BY CODE ORDER BY DATE) AS DIFF3,
           LAG(MA20 - MA60, 5) OVER (PARTITION BY CODE ORDER BY DATE) AS DIFF5,
           LAG(MA20 - MA60, 7) OVER (PARTITION BY CODE ORDER BY DATE) AS DIFF7,
           LAG(MA20 - MA60,10) OVER (PARTITION BY CODE ORDER BY DATE) AS DIFF10,
           LAG(MA20 - MA60,15) OVER (PARTITION BY CODE ORDER BY DATE) AS DIFF15,
           ROW_NUMBER() OVER (PARTITION BY CODE ORDER BY DATE DESC) AS ROW_NO
    FROM TB_ILBONG
)
SELECT A.CODE AS code, K."종목명" AS name
FROM A
JOIN TB_KOSPI K
  ON A.CODE = K."코드"
WHERE {condition}
ORDER BY CAST(REPLACE(K."시가총액", ',', '') AS BIGINT) DESC
"""

    df = con.execute(query).df()

    con.close()

    return df.to_dict("records")


def select_st_ma20_ilbong(code_list: list):
    con = duckdb.connect(db_path)

    codes_str = ", ".join([f"'{c}'" for c in code_list])

    query = f"""
        SELECT
            code,
            date,
            open,
            high,
            low,
            close,
            ma20,
            ma60
        FROM tb_ilbong
        WHERE code IN ({codes_str})
        ORDER BY code, date ASC
    """

    df = con.execute(query).df()
    con.close()

    df = df.replace({np.nan: None})

    return {
        code: {
            'date': group['date'].tolist(),
            'open': group['open'].tolist(),
            'high': group['high'].tolist(),
            'low': group['low'].tolist(),
            'close': group['close'].tolist(),
            'ma20': group['ma20'].tolist(),
            'ma60': group['ma60'].tolist()
        }
        for code, group in df.groupby('code')
    }










def select_st_sales(mode: str):

    con = duckdb.connect(db_path)

    if mode == "buy":

        condition = """
            s1.매출 < s2.매출
            AND s2.매출 < s3.매출
            AND s3.매출 < s4.매출

            AND s1.영업이익 < s2.영업이익
            AND s2.영업이익 < s3.영업이익
            AND s3.영업이익 < s4.영업이익
        """

    elif mode == "sell":

        condition = """
            s1.매출 > s2.매출
            AND s2.매출 > s3.매출
            AND s3.매출 > s4.매출

            AND s1.영업이익 > s2.영업이익
            AND s2.영업이익 > s3.영업이익
            AND s3.영업이익 > s4.영업이익
        """

    else:

        condition = "1=1"

    query = f"""
WITH Q AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY 코드
               ORDER BY 기간 DESC
           ) RN
    FROM TB_NAVER_FIN
    WHERE 구분='분기'
      AND 기간 NOT LIKE '%(E)%'
)

SELECT
    K."코드" AS code,
    K."종목명" AS name
FROM
    (SELECT * FROM Q WHERE RN=4) S1
    JOIN (SELECT * FROM Q WHERE RN=3) S2
      ON S1.코드 = S2.코드
    JOIN (SELECT * FROM Q WHERE RN=2) S3
      ON S1.코드 = S3.코드
    JOIN (SELECT * FROM Q WHERE RN=1) S4
      ON S1.코드 = S4.코드
    JOIN TB_KOSPI K
      ON S1.코드 = K."코드"
WHERE
    {condition}
ORDER BY CAST(REPLACE(K."시가총액", ',', '') AS BIGINT) DESC
"""

    df = con.execute(query).df()

    con.close()

    return df.to_dict("records")


def select_st_sales_fin(code_list: list):
    con = duckdb.connect(db_path)

    codes_str = ", ".join([f"'{c}'" for c in code_list])

    query = f"""
        SELECT
            코드,
            기간,
            매출,
            영업이익
        FROM tb_naver_fin
        WHERE 구분='분기'
          AND 코드 IN ({codes_str})
        ORDER BY 코드, 기간
    """

    df = con.execute(query).df()
    con.close()

    df = df.replace({np.nan: None})

    return {
        code: group[['기간', '매출', '영업이익']].to_dict('records')
        for code, group in df.groupby('코드')
    }





def select_st_salesqoq(mode: str):

    con = duckdb.connect(db_path)

    if mode == "buy":

        condition = """
            S1.매출QOQ > 0
            AND S2.매출QOQ > 0
            AND S3.매출QOQ > 0
            AND S4.매출QOQ > 0

            AND S1.매출QOQ < S2.매출QOQ
            AND S2.매출QOQ < S3.매출QOQ
            AND S3.매출QOQ < S4.매출QOQ

            AND S1.영업이익QOQ > 0
            AND S2.영업이익QOQ > 0
            AND S3.영업이익QOQ > 0
            AND S4.영업이익QOQ > 0

            AND S1.영업이익QOQ < S2.영업이익QOQ
            AND S2.영업이익QOQ < S3.영업이익QOQ
            AND S3.영업이익QOQ < S4.영업이익QOQ
        """

    elif mode == "sell":

        condition = """
            S1.매출QOQ < 0
            AND S2.매출QOQ < 0
            AND S3.매출QOQ < 0
            AND S4.매출QOQ < 0

            AND S1.매출QOQ > S2.매출QOQ
            AND S2.매출QOQ > S3.매출QOQ
            AND S3.매출QOQ > S4.매출QOQ

            AND S1.영업이익QOQ < 0
            AND S2.영업이익QOQ < 0
            AND S3.영업이익QOQ < 0
            AND S4.영업이익QOQ < 0

            AND S1.영업이익QOQ > S2.영업이익QOQ
            AND S2.영업이익QOQ > S3.영업이익QOQ
            AND S3.영업이익QOQ > S4.영업이익QOQ
        """

    else:

        condition = "1=1"

    query = f"""
WITH A AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY 코드
               ORDER BY 기간 DESC
           ) AS RN
    FROM TB_NAVER_FIN
    WHERE 구분='분기'
      AND 기간 NOT LIKE '%(E)%'
)
SELECT
    K."코드" AS code,
    K."종목명" AS name
FROM
    (SELECT * FROM A WHERE RN=4) S1
    JOIN (SELECT * FROM A WHERE RN=3) S2
      ON S1.코드 = S2.코드
    JOIN (SELECT * FROM A WHERE RN=2) S3
      ON S1.코드 = S3.코드
    JOIN (SELECT * FROM A WHERE RN=1) S4
      ON S1.코드 = S4.코드
    JOIN TB_KOSPI K
      ON S1.코드 = K."코드"
WHERE
    {condition}
ORDER BY CAST(REPLACE(K."시가총액", ',', '') AS BIGINT) DESC
"""

    df = con.execute(query).df()

    con.close()

    return df.to_dict("records")


def select_st_salesqoq_fin(code_list: list):
    con = duckdb.connect(db_path)

    codes_str = ", ".join([f"'{c}'" for c in code_list])

    query = f"""
        SELECT
            코드,
            기간,
            매출QOQ,
            영업이익QOQ
        FROM tb_naver_fin
        WHERE 구분='분기'
          AND 코드 IN ({codes_str})
        ORDER BY 코드, 기간
    """

    df = con.execute(query).df()
    con.close()

    df = df.replace({np.nan: None})

    return {
        code: group[['기간', '매출QOQ', '영업이익QOQ']].to_dict('records')
        for code, group in df.groupby('코드')
    }









def select_st_asset(mode: str):

    con = duckdb.connect(db_path)

    if mode == "buy":

        condition = """
            S1.자산 < S2.자산
            AND S2.자산 < S3.자산
            AND S3.자산 < S4.자산
        """

    elif mode == "sell":

        condition = """
            S1.자산 > S2.자산
            AND S2.자산 > S3.자산
            AND S3.자산 > S4.자산
        """

    else:

        condition = "1=1"

    query = f"""
WITH A AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY 코드
               ORDER BY 기간 DESC
           ) AS RN
    FROM TB_NAVER_FIN
    WHERE 구분='연도'
      AND 기간 NOT LIKE '%(E)%'
)
SELECT
    K."코드" AS code,
    K."종목명" AS name
FROM
    (SELECT * FROM A WHERE RN=4) S1
    JOIN (SELECT * FROM A WHERE RN=3) S2
      ON S1.코드 = S2.코드
    JOIN (SELECT * FROM A WHERE RN=2) S3
      ON S1.코드 = S3.코드
    JOIN (SELECT * FROM A WHERE RN=1) S4
      ON S1.코드 = S4.코드
    JOIN TB_KOSPI K
      ON S1.코드 = K."코드"
WHERE
    {condition}
ORDER BY CAST(REPLACE(K."시가총액", ',', '') AS BIGINT) DESC
"""

    df = con.execute(query).df()

    con.close()

    return df.to_dict("records")


def select_st_asset_fin(code_list: list):
    con = duckdb.connect(db_path)

    codes_str = ", ".join([f"'{c}'" for c in code_list])

    query = f"""
        SELECT
            코드,
            기간,
            자산,
            부채
        FROM tb_naver_fin
        WHERE 구분='분기'
          AND 코드 IN ({codes_str})
        ORDER BY 코드, 기간
    """

    df = con.execute(query).df()
    con.close()

    df = df.replace({np.nan: None})

    return {
        code: group[['기간', '자산', '부채']].to_dict('records')
        for code, group in df.groupby('코드')
    }





def select_st_cf(mode: str):

    con = duckdb.connect(db_path)

    buy_condition = """
        S1.영업현금흐름 < S4.영업현금흐름
    """

    sell_condition = """
        S1.영업현금흐름 > S4.영업현금흐름
    """

    if mode == "buy":

        condition = buy_condition

    elif mode == "sell":

        condition = sell_condition

    else:

        condition = f"""
            NOT (
                ({buy_condition})
                OR
                ({sell_condition})
            )
        """

    query = f"""
WITH A AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY 코드
               ORDER BY 기간 DESC
           ) AS RN
    FROM TB_NAVER_FIN
    WHERE 구분='연도'
      AND 기간 NOT LIKE '%(E)%'
)
SELECT
    K."코드" AS code,
    K."종목명" AS name
FROM
    (SELECT * FROM A WHERE RN=4) S1
    JOIN (SELECT * FROM A WHERE RN=3) S2
      ON S1.코드 = S2.코드
    JOIN (SELECT * FROM A WHERE RN=2) S3
      ON S1.코드 = S3.코드
    JOIN (SELECT * FROM A WHERE RN=1) S4
      ON S1.코드 = S4.코드
    JOIN TB_KOSPI K
      ON S1.코드 = K."코드"
WHERE
    {condition}
ORDER BY CAST(REPLACE(K."시가총액", ',', '') AS BIGINT) DESC
"""

    df = con.execute(query).df()

    con.close()

    return df.to_dict("records")




def select_st_cf_fin(code_list: list):
    con = duckdb.connect(db_path)

    codes_str = ", ".join([f"'{c}'" for c in code_list])

    query = f"""
        SELECT
            코드,
            기간,
            영업현금흐름,
            투자현금흐름,
            재무현금흐름,
            FCF
        FROM tb_naver_fin
        WHERE 구분='분기'
          AND 코드 IN ({codes_str})
        ORDER BY 코드, 기간
    """

    df = con.execute(query).df()
    con.close()

    df = df.replace({np.nan: None})

    return {
        code: group[['기간', '영업현금흐름', '투자현금흐름', '재무현금흐름', 'FCF']].to_dict('records')
        for code, group in df.groupby('코드')
    }










def select_st_eps(mode: str):

    con = duckdb.connect(db_path)

    if mode == "buy":

        condition = """
            S1.EPS < S2.EPS
            AND S2.EPS < S3.EPS
            AND S3.EPS < S4.EPS
        """

    elif mode == "sell":

        condition = """
            S1.EPS > S2.EPS
            AND S2.EPS > S3.EPS
            AND S3.EPS > S4.EPS
        """

    else:

        condition = "1=1"

    query = f"""
WITH A AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY 코드
               ORDER BY 기간 DESC
           ) AS RN
    FROM TB_NAVER_FIN
    WHERE 구분='분기'
      AND 기간 NOT LIKE '%(E)%'
)
SELECT
    K."코드" AS code,
    K."종목명" AS name
FROM
    (SELECT * FROM A WHERE RN=4) S1
    JOIN (SELECT * FROM A WHERE RN=3) S2
      ON S1.코드 = S2.코드
    JOIN (SELECT * FROM A WHERE RN=2) S3
      ON S1.코드 = S3.코드
    JOIN (SELECT * FROM A WHERE RN=1) S4
      ON S1.코드 = S4.코드
    JOIN TB_KOSPI K
      ON S1.코드 = K."코드"
WHERE
    {condition}
ORDER BY CAST(REPLACE(k.시가총액, ',', '') AS BIGINT) DESC
"""

    df = con.execute(query).df()

    con.close()

    return df.to_dict("records")


def select_st_eps_fin(code_list: list):
    con = duckdb.connect(db_path)

    codes_str = ", ".join([f"'{c}'" for c in code_list])

    query = f"""
        SELECT
            코드,
            기간,
            EPS
        FROM tb_naver_fin
        WHERE 구분='분기'
          AND 코드 IN ({codes_str})
        ORDER BY 코드, 기간
    """

    df = con.execute(query).df()
    con.close()

    df = df.replace({np.nan: None})

    return {
        code: group[['기간', 'EPS']].to_dict('records')
        for code, group in df.groupby('코드')
    }










def select_st_epsqoq(mode: str):

    con = duckdb.connect(db_path)

    if mode == "buy":

        condition = """
            S2.EPSQOQ > 0
            AND S3.EPSQOQ > 0
            AND S4.EPSQOQ > 0
        """

    elif mode == "sell":

        condition = """
            S2.EPSQOQ < 0
            AND S3.EPSQOQ < 0
            AND S4.EPSQOQ < 0
        """

    else:

        condition = "1=1"

    query = f"""
WITH A AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY 코드
               ORDER BY 기간 DESC
           ) AS RN
    FROM TB_NAVER_FIN
    WHERE 구분='분기'
      AND 기간 NOT LIKE '%(E)%'
)
SELECT
    K."코드" AS code,
    K."종목명" AS name
FROM
    (SELECT * FROM A WHERE RN=3) S2
    JOIN (SELECT * FROM A WHERE RN=2) S3
      ON S2.코드 = S3.코드
    JOIN (SELECT * FROM A WHERE RN=1) S4
      ON S2.코드 = S4.코드
    JOIN TB_KOSPI K
      ON S2.코드 = K."코드"
WHERE {condition}
ORDER BY CAST(REPLACE(K."시가총액", ',', '') AS BIGINT) DESC
"
"""

    df = con.execute(query).df()

    con.close()

    return df.to_dict("records")

def select_st_epsqoq_fin(code_list: list):
    con = duckdb.connect(db_path)

    codes_str = ", ".join([f"'{c}'" for c in code_list])

    query = f"""
        SELECT
            코드,
            기간,
            EPSQOQ
        FROM tb_naver_fin
        WHERE 구분='분기'
          AND 코드 IN ({codes_str})
        ORDER BY 코드, 기간
    """

    df = con.execute(query).df()
    con.close()

    df = df.replace({np.nan: None})

    return {
        code: group[['기간', 'EPSQOQ']].to_dict('records')
        for code, group in df.groupby('코드')
    }





def select_st_margin(mode: str):

    con = duckdb.connect(db_path)

    buy_condition = """
        S1.영업이익률 < S2.영업이익률
        AND S2.영업이익률 < S3.영업이익률
        AND S3.영업이익률 < S4.영업이익률
    """

    sell_condition = """
        S1.영업이익률 > S2.영업이익률
        AND S2.영업이익률 > S3.영업이익률
        AND S3.영업이익률 > S4.영업이익률
    """

    if mode == "buy":

        condition = buy_condition

    elif mode == "sell":

        condition = sell_condition

    else:

        condition = f"""
            NOT (
                ({buy_condition})
                OR
                ({sell_condition})
            )
        """

    query = f"""
WITH A AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY 코드
               ORDER BY 기간 DESC
           ) AS RN
    FROM TB_NAVER_FIN
    WHERE 구분='분기'
      AND 기간 NOT LIKE '%(E)%'
)
SELECT
    K."코드" AS code,
    K."종목명" AS name
FROM
    (SELECT * FROM A WHERE RN=4) S1
    JOIN (SELECT * FROM A WHERE RN=3) S2
      ON S1.코드 = S2.코드
    JOIN (SELECT * FROM A WHERE RN=2) S3
      ON S1.코드 = S3.코드
    JOIN (SELECT * FROM A WHERE RN=1) S4
      ON S1.코드 = S4.코드
    JOIN TB_KOSPI K
      ON S1.코드 = K."코드"
WHERE {condition}
ORDER BY CAST(REPLACE(K."시가총액", ',', '') AS BIGINT) DESC

"""

    df = con.execute(query).df()

    con.close()

    return df.to_dict("records")


def select_st_margin_fin(code_list: list):
    con = duckdb.connect(db_path)

    codes_str = ", ".join([f"'{c}'" for c in code_list])

    query = f"""
        SELECT
            코드,
            기간,
            영업이익률
        FROM tb_naver_fin
        WHERE 구분='분기'
          AND 코드 IN ({codes_str})
        ORDER BY 코드, 기간
    """

    df = con.execute(query).df()
    con.close()

    df = df.replace({np.nan: None})

    return {
        code: group[['기간', '영업이익률']].to_dict('records')
        for code, group in df.groupby('코드')
    }





def select_st_roe(mode: str):

    con = duckdb.connect(db_path)

    buy_condition = """
        S1.ROE < S2.ROE
        AND S2.ROE < S3.ROE
        AND S3.ROE < S4.ROE
    """

    sell_condition = """
        S1.ROE > S2.ROE
        AND S2.ROE > S3.ROE
        AND S3.ROE > S4.ROE
    """

    if mode == "buy":

        condition = buy_condition

    elif mode == "sell":

        condition = sell_condition

    else:

        condition = f"""
            NOT (
                ({buy_condition})
                OR
                ({sell_condition})
            )
        """

    query = f"""
WITH A AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY 코드
               ORDER BY 기간 DESC
           ) AS RN
    FROM TB_NAVER_FIN
    WHERE 구분='분기'
      AND 기간 NOT LIKE '%(E)%'
)
SELECT
    K."코드" AS code,
    K."종목명" AS name
FROM
    (SELECT * FROM A WHERE RN=4) S1
    JOIN (SELECT * FROM A WHERE RN=3) S2
      ON S1.코드 = S2.코드
    JOIN (SELECT * FROM A WHERE RN=2) S3
      ON S1.코드 = S3.코드
    JOIN (SELECT * FROM A WHERE RN=1) S4
      ON S1.코드 = S4.코드
    JOIN TB_KOSPI K
      ON S1.코드 = K."코드"
WHERE {condition}
ORDER BY CAST(REPLACE(K."시가총액", ',', '') AS BIGINT) DESC

"""

    df = con.execute(query).df()

    con.close()

    return df.to_dict("records")

def select_st_roe_fin(code_list: list):
    con = duckdb.connect(db_path)

    codes_str = ", ".join([f"'{c}'" for c in code_list])

    query = f"""
        SELECT
            코드,
            기간,
            ROE
        FROM tb_naver_fin
        WHERE 구분='분기'
          AND 코드 IN ({codes_str})
        ORDER BY 코드, 기간
    """

    df = con.execute(query).df()
    con.close()

    df = df.replace({np.nan: None})

    return {
        code: group[['기간', 'ROE']].to_dict('records')
        for code, group in df.groupby('코드')
    }







def select_st_dept(mode: str):

    con = duckdb.connect(db_path)

    buy_condition = """
        S1.부채비율 > S2.부채비율
        AND S2.부채비율 > S3.부채비율
        AND S3.부채비율 > S4.부채비율
    """

    sell_condition = """
        S1.부채비율 < S2.부채비율
        AND S2.부채비율 < S3.부채비율
        AND S3.부채비율 < S4.부채비율
    """

    if mode == "buy":

        condition = buy_condition

    elif mode == "sell":

        condition = sell_condition

    else:

        condition = f"""
            NOT (
                ({buy_condition})
                OR
                ({sell_condition})
            )
        """

    query = f"""
WITH A AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY 코드
               ORDER BY 기간 DESC
           ) AS RN
    FROM TB_NAVER_FIN
    WHERE 구분='분기'
      AND 기간 NOT LIKE '%(E)%'
)
SELECT
    K."코드" AS code,
    K."종목명" AS name
FROM
    (SELECT * FROM A WHERE RN=4) S1
    JOIN (SELECT * FROM A WHERE RN=3) S2
      ON S1.코드 = S2.코드
    JOIN (SELECT * FROM A WHERE RN=2) S3
      ON S1.코드 = S3.코드
    JOIN (SELECT * FROM A WHERE RN=1) S4
      ON S1.코드 = S4.코드
    JOIN TB_KOSPI K
      ON S1.코드 = K."코드"
WHERE {condition}
ORDER BY CAST(REPLACE(K."시가총액", ',', '') AS BIGINT) DESC

"""

    df = con.execute(query).df()

    con.close()

    return df.to_dict("records")

def select_st_dept_fin(code_list: list):
    con = duckdb.connect(db_path)

    codes_str = ", ".join([f"'{c}'" for c in code_list])

    query = f"""
        SELECT
            코드,
            기간,
            부채비율
        FROM tb_naver_fin
        WHERE 구분='분기'
          AND 코드 IN ({codes_str})
        ORDER BY 코드, 기간
    """

    df = con.execute(query).df()
    con.close()

    df = df.replace({np.nan: None})

    return {
        code: group[['기간', '부채비율']].to_dict('records')
        for code, group in df.groupby('코드')
    }






























def insert_naver_fin(dict_total):
    """
    정통 SQL 쿼리 방식으로 데이터를 하나씩 삽입합니다.
    """
    code = dict_total['코드']
    
    # 1. 테이블 생성 (테이블이 없을 경우 대비)
    create_sql = """
    CREATE TABLE IF NOT EXISTS tb_naver_fin (
        코드 VARCHAR, 구분 VARCHAR, 기간 VARCHAR,
        매출 DOUBLE, 영업이익 DOUBLE, 당기순이익 DOUBLE, 자산 DOUBLE, 자본 DOUBLE, 부채 DOUBLE,
        영업이익률 DOUBLE, 부채비율 DOUBLE, 영업현금흐름 DOUBLE, 투자현금흐름 DOUBLE,
        재무현금흐름 DOUBLE, FCF DOUBLE, CAPEX DOUBLE, ROE DOUBLE,
        EPS DOUBLE, PER DOUBLE, BPS DOUBLE, PBR DOUBLE, 배당 DOUBLE, 업종 VARCHAR,
        매출QOQ DOUBLE, 영업이익QOQ DOUBLE, 자본QOQ DOUBLE, EPSQOQ DOUBLE,
        PRIMARY KEY (코드, 구분, 기간)
    );
    """
    
    # 2. 삽입 쿼리 (파라미터 바인딩 사용)
    insert_sql = """
    INSERT OR REPLACE INTO tb_naver_fin VALUES (
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
    );
    """

    try:
        with duckdb.connect(db_path) as conn:
            # 테이블 생성
            conn.execute(create_sql)
            
            # 데이터 삽입 루프
            for gubun in ['분기', '연도']:
                for period, data in dict_total[gubun].items():
                    매출성장 = data.get('매출QOQ') or data.get('매출YOY')
                    영업이익성장 = data.get('영업이익QOQ') or data.get('영업이익YOY')
                    자본성장 = data.get('자본QOQ') or data.get('자본YOY')
                    EPS성장 = data.get('EPSQOQ') or data.get('EPSYOY')
                    
                    params = (
                        code, gubun, period,
                        data.get('매출'), data.get('영업이익'), data.get('당기순이익'),
                        data.get('자산'), data.get('자본'), data.get('부채'), data.get('영업이익률'), data.get('부채비율'),
                        data.get('영업현금흐름'), data.get('투자현금흐름'), data.get('재무현금흐름'), data.get('FCF'), data.get('CAPEX'),
                        data.get('ROE'), data.get('EPS'), data.get('PER'), data.get('BPS'), data.get('PBR'), data.get('배당'), dict_total['업종'],
                        매출성장, 영업이익성장, 자본성장, EPS성장
                    )
                    conn.execute(insert_sql, params)
        
        # print(f"✅ {code} 재무 데이터 DB 삽입 완료! (정통 쿼리 방식)")
        return True
    
    except Exception as e:
        print(f"❌ DB 작업 중 오류 발생: {e}")
        return False










def select_naver_fin(code):

    query = """
    SELECT a.코드, a.구분, a.기간, a.매출, a.영업이익, a.당기순이익, a.자산, a.자본, a.부채, a.영업이익률, a.부채비율, a.영업현금흐름, a.투자현금흐름, a.재무현금흐름, a.FCF, a.CAPEX, a.ROE, a.EPS, a.PER, a.BPS, a.PBR, a.배당, a.업종, b.시가총액, a.매출QOQ, a.영업이익QOQ, a.자본QOQ, a.EPSQOQ
    FROM tb_naver_fin a
    LEFT JOIN tb_kospi b ON a.코드 = b.코드
    WHERE a.코드 = ?
    ORDER BY a.구분 DESC, a.기간 ASC
    """

    try:
        with duckdb.connect(db_path) as conn:
            df = conn.execute(query, [code]).df()

        return df.fillna(0)

    except Exception as e:
        print(f"❌ DB 조회 중 오류 발생: {e}")
        return pd.DataFrame()




def insert_tb_theme(list_theme):
    """
    수집된 테마 데이터 리스트를 받아 tb_theme 테이블을 재생성하고 적재합니다.
    Args:
        list_theme (list of dict): [{"stock_code": "...", "stock_name": "...", "theme_name": "..."}, ...]
    """
    if not list_theme:
        print("❌ 적재할 데이터가 없습니다.")
        return False

    try:
        with duckdb.connect(db_path) as conn:
            # 1. 테이블 초기화 및 생성
            conn.execute("DROP TABLE IF EXISTS tb_theme;")
            conn.execute("""
                CREATE TABLE tb_theme (
                    code VARCHAR,
                    name VARCHAR,
                    theme VARCHAR,
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_theme_code ON tb_theme (code);")
            
            # 2. 데이터 적재 (리스트를 판다스 데이터프레임으로 변환 후 적재)
            df = pd.DataFrame(list_theme)
            conn.execute("INSERT INTO tb_theme SELECT * FROM df")
            
        print(f"✅ tb_theme 테이블 재생성 및 {len(df)}건 적재 완료!")
        return True
        
    except Exception as e:
        print(f"❌ DB 작업 중 오류 발생: {e}")
        return False



















def create_tb_checkbox():

    with duckdb.connect(db_path) as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS tb_checkbox (
                checkbox_id VARCHAR PRIMARY KEY,
                checked BOOLEAN DEFAULT TRUE
            )
        """)

        conn.execute("""
            INSERT OR IGNORE INTO tb_checkbox VALUES
            ('toggleMA', TRUE),
            ('toggleEMA26', FALSE),
            ('toggleBollinger', FALSE),
            ('toggleIlmok', FALSE),
            ('toggleRSI', FALSE),
            ('toggleMACD', TRUE),
            ('toggleFlow', TRUE)
        """)







def update_tb_checkbox(checkbox_id, checked):

    with duckdb.connect(db_path) as conn:

        conn.execute("""
            INSERT OR REPLACE INTO tb_checkbox
            (checkbox_id, checked)
            VALUES (?, ?)
        """, [checkbox_id, checked])






def select_tb_checkbox():

    with duckdb.connect(db_path) as conn:

        rows = conn.execute("""
            SELECT checkbox_id, checked
            FROM tb_checkbox
        """).fetchall()

    return {row[0]: row[1] for row in rows}





create_tb_checkbox()

