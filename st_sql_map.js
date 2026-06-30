const SQL_MAP = {

    st_macd: `
SELECT ... tb_ilbong, tb_kospi
`,

    st_hoga: `
SELECT
    code,
    offer1, offer_rem1, bid1, bid_rem1,
    offer2, offer_rem2, bid2, bid_rem2,
    offer3, offer_rem3, bid3, bid_rem3,
    offer4, offer_rem4, bid4, bid_rem4,
    offer5, offer_rem5, bid5, bid_rem5,
    offer6, offer_rem6, bid6, bid_rem6,
    offer7, offer_rem7, bid7, bid_rem7,
    offer8, offer_rem8, bid8, bid_rem8,
    offer9, offer_rem9, bid9, bid_rem9,
    offer10, offer_rem10, bid10, bid_rem10,
    updated_at
FROM TB_HOGA
WHERE code = '005930'
`,


    st_rsi: `
SELECT ... RSI, tb_ilbong, tb_kospi
`,



    st_bol: `
SELECT ... bol, tb_ilbong, tb_kospi
`,


    st_ilmok: `
SELECT ... ilmok, tb_ilbong, tb_kospi
`,


    st_vol: `
SELECT ... vol, tb_ilbong, tb_kospi
`,


    st_ma5: `
SELECT ... ma5, tb_ilbong, tb_kospi
`,


    st_ma20: `
SELECT ... ma20, tb_ilbong, tb_kospi
`,


    st_sales: `
SELECT ... sales, tb_ilbong, tb_kospi
`,


    st_salesqoq: `
SELECT ... salesqoq, tb_ilbong, tb_kospi
`,


    st_asset: `
SELECT ... asset, tb_ilbong, tb_kospi
`,


    st_cf: `
SELECT ... cf, tb_ilbong, tb_kospi
`,


    st_eps: `
SELECT ... eps, tb_ilbong, tb_kospi
`,


    st_epsqoq: `
SELECT ... epsqoq, tb_ilbong, tb_kospi
`,


    st_margin: `
SELECT ... margin, tb_ilbong, tb_kospi
`,


    st_roe: `
SELECT ... roe, tb_ilbong, tb_kospi
`,


    st_dept: `
SELECT ... dept, tb_ilbong, tb_kospi
`,















    

    st_top: `
SELECT ...
`

}



















const TABLE_MAP = {

TB_ILBONG: `
CREATE TABLE TB_ILBONG (
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
`,

TB_NAVER_FIN: `
CREATE TABLE TB_NAVER_FIN (
    코드 VARCHAR,
    구분 VARCHAR,
    기간 VARCHAR,
    매출 DOUBLE,
    영업이익 DOUBLE,
    당기순이익 DOUBLE,
    자산 DOUBLE,
    자본 DOUBLE,
    부채 DOUBLE,
    영업이익률 DOUBLE,
    부채비율 DOUBLE,
    영업현금흐름 DOUBLE,
    투자현금흐름 DOUBLE,
    재무현금흐름 DOUBLE,
    FCF DOUBLE,
    CAPEX DOUBLE,
    ROE DOUBLE,
    EPS DOUBLE,
    PER DOUBLE,
    BPS DOUBLE,
    PBR DOUBLE,
    배당 DOUBLE,
    업종 VARCHAR,
    매출QOQ DOUBLE,
    영업이익QOQ DOUBLE,
    자본QOQ DOUBLE,
    EPSQOQ DOUBLE,
    PRIMARY KEY (코드, 구분, 기간)
)
`,

TB_KOSPI: `
CREATE TABLE TB_KOSPI (
    코드 VARCHAR PRIMARY KEY,
    종목명 VARCHAR,
    현재가 VARCHAR,
    등락률 VARCHAR,
    시가총액 VARCHAR,
    매출 VARCHAR,
    영업이익 VARCHAR,
    당기순이익 VARCHAR,
    주당순이익 VARCHAR,
    배당금 VARCHAR,
    외국인 VARCHAR,
    PER VARCHAR,
    ROE VARCHAR,
    시장 VARCHAR,
    순위 BIGINT
)
`,


TB_HOGA: `
CREATE TABLE TB_HOGA (
    code VARCHAR PRIMARY KEY,

    offer1 INTEGER,
    offer_rem1 INTEGER,
    bid1 INTEGER,
    bid_rem1 INTEGER,

    offer2 INTEGER,
    offer_rem2 INTEGER,
    bid2 INTEGER,
    bid_rem2 INTEGER,

    offer3 INTEGER,
    offer_rem3 INTEGER,
    bid3 INTEGER,
    bid_rem3 INTEGER,

    offer4 INTEGER,
    offer_rem4 INTEGER,
    bid4 INTEGER,
    bid_rem4 INTEGER,

    offer5 INTEGER,
    offer_rem5 INTEGER,
    bid5 INTEGER,
    bid_rem5 INTEGER,

    offer6 INTEGER,
    offer_rem6 INTEGER,
    bid6 INTEGER,
    bid_rem6 INTEGER,

    offer7 INTEGER,
    offer_rem7 INTEGER,
    bid7 INTEGER,
    bid_rem7 INTEGER,

    offer8 INTEGER,
    offer_rem8 INTEGER,
    bid8 INTEGER,
    bid_rem8 INTEGER,

    offer9 INTEGER,
    offer_rem9 INTEGER,
    bid9 INTEGER,
    bid_rem9 INTEGER,

    offer10 INTEGER,
    offer_rem10 INTEGER,
    bid10 INTEGER,
    bid_rem10 INTEGER,

    updated_at TIMESTAMP
)
`,



}



