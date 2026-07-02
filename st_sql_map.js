const SQL_MAP = {

    st_macd: `
WITH A AS (
    SELECT
        CODE, DATE, MACD, MACD9,
        MACD - MACD9 AS HIST,
        LAG(MACD - MACD9, 1) OVER (PARTITION BY CODE ORDER BY DATE) AS HIST_1,
        LAG(MACD - MACD9, 2) OVER (PARTITION BY CODE ORDER BY DATE) AS HIST_2,
        LAG(MACD - MACD9, 3) OVER (PARTITION BY CODE ORDER BY DATE) AS HIST_3,
        LAG(MACD - MACD9, 5) OVER (PARTITION BY CODE ORDER BY DATE) AS HIST_5,
        LAG(MACD - MACD9, 7) OVER (PARTITION BY CODE ORDER BY DATE) AS HIST_7,
        LAG(MACD - MACD9, 10) OVER (PARTITION BY CODE ORDER BY DATE) AS HIST_10,
        LAG(MACD - MACD9, 12) OVER (PARTITION BY CODE ORDER BY DATE) AS HIST_12,
        ROW_NUMBER() OVER (PARTITION BY CODE ORDER BY DATE DESC) AS ROW_NO
    FROM TB_ILBONG
)
SELECT
    A.CODE AS code,
    K."종목명" AS name
FROM A
JOIN TB_KOSPI K ON A.CODE = K."코드"
WHERE
    ROW_NO = 1

    /* ================= BUY ================= */
    AND (
        HIST_10 < HIST_3 AND HIST_7 < HIST_3 AND HIST_7 < HIST_1
        AND HIST_5 < HIST_1 AND HIST_3 < HIST_1
        AND HIST_12 < HIST AND HIST_5 < HIST AND HIST_3 < HIST
        AND HIST_2 < HIST AND HIST_1 < HIST
        AND ABS(HIST) / GREATEST(ABS(MACD9), 0.001) <= 0.1
    )

    /* ================= SELL ================= */
    -- AND (
    --     HIST_10 > HIST_3 AND HIST_7 > HIST_3 AND HIST_7 > HIST_1
    --     AND HIST_5 > HIST_1 AND HIST_3 > HIST_1
    --     AND HIST_12 > HIST AND HIST_5 > HIST AND HIST_3 > HIST
    --     AND HIST_2 > HIST AND HIST_1 > HIST
    --     AND ABS(HIST) / GREATEST(ABS(MACD9), 0.001) <= 0.1
    -- )

    /* ================= ETC ================= */
    -- AND NOT (
    --     (
    --         HIST_10 < HIST_3 AND HIST_7 < HIST_3 AND HIST_7 < HIST_1
    --         AND HIST_5 < HIST_1 AND HIST_3 < HIST_1
    --         AND HIST_12 < HIST AND HIST_5 < HIST AND HIST_3 < HIST
    --         AND HIST_2 < HIST AND HIST_1 < HIST
    --         AND ABS(HIST) / GREATEST(ABS(MACD9), 0.001) <= 0.1
    --     )
    --     OR
    --     (
    --         HIST_10 > HIST_3 AND HIST_7 > HIST_3 AND HIST_7 > HIST_1
    --         AND HIST_5 > HIST_1 AND HIST_3 > HIST_1
    --         AND HIST_12 > HIST AND HIST_5 > HIST AND HIST_3 > HIST
    --         AND HIST_2 > HIST AND HIST_1 > HIST
    --         AND ABS(HIST) / GREATEST(ABS(MACD9), 0.001) <= 0.1
    --     )
    -- )
ORDER BY CAST(REPLACE(K."시가총액", ',', '') AS BIGINT) DESC
`,

    st_hoga: `
SELECT 
    a.code,
    b.종목명 as name,
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
    strftime(a.updated_at, '%H:%M:%S') as updated_at,
    GREATEST(
        offer_rem1, offer_rem2, offer_rem3, offer_rem4, offer_rem5,
        offer_rem6, offer_rem7, offer_rem8, offer_rem9, offer_rem10,
        bid_rem1, bid_rem2, bid_rem3, bid_rem4, bid_rem5,
        bid_rem6, bid_rem7, bid_rem8, bid_rem9, bid_rem10
    ) as max_rem
FROM tb_hoga a
INNER JOIN tb_kospi b ON a.code = b.코드
WHERE 
    -- BUY 조건
    bid_rem1 > 500
    AND (bid_rem1 / 10.0) > offer_rem1
    AND (bid_rem1 / 10.0) > offer_rem2
    AND (bid_rem1 / 10.0) > offer_rem3
    AND (bid_rem1 / 10.0) > offer_rem4
    AND (bid_rem1 / 10.0) > offer_rem5

    AND (bid_rem2 / 5.0) > offer_rem1
    AND (bid_rem2 / 5.0) > offer_rem2
    AND (bid_rem2 / 5.0) > offer_rem3
    AND (bid_rem2 / 5.0) > offer_rem4
    AND (bid_rem2 / 5.0) > offer_rem5

    /*
    -- SELL 조건
    offer_rem1 > 500
    AND (offer_rem1 / 10.0) > bid_rem1
    AND (offer_rem1 / 10.0) > bid_rem2
    AND (offer_rem1 / 10.0) > bid_rem3
    AND (offer_rem1 / 10.0) > bid_rem4
    AND (offer_rem1 / 10.0) > bid_rem5

    AND (offer_rem2 / 5.0) > bid_rem1
    AND (offer_rem2 / 5.0) > bid_rem2
    AND (offer_rem2 / 5.0) > bid_rem3
    AND (offer_rem2 / 5.0) > bid_rem4
    AND (offer_rem2 / 5.0) > bid_rem5

    -- ETC 조건
    NOT (
        (BUY 조건)
        OR
        (SELL 조건)
    )
    */
`,


    st_rsi: `
WITH T AS (
    SELECT CODE, DATE, RSI14,
           LAG(RSI14) OVER (PARTITION BY CODE ORDER BY DATE) AS PREV_RSI,
           ROW_NUMBER() OVER (PARTITION BY CODE ORDER BY DATE DESC) AS ROW_NO
    FROM TB_ILBONG
)
SELECT T.CODE AS code, K."종목명" AS name
FROM T
JOIN TB_KOSPI K ON T.CODE = K."코드"
WHERE ROW_NO = 1
  AND PREV_RSI < 30
  AND RSI14 > PREV_RSI
ORDER BY CAST(REPLACE(K."시가총액", ',', '') AS BIGINT) DESC
`,



    st_bol: `
WITH A AS (
    SELECT CODE, DATE, CLOSE, BOL_U, BOL_L,
           (CLOSE - BOL_L) / NULLIF(BOL_U - BOL_L,0) AS POS,
           LAG(CLOSE,1) OVER (PARTITION BY CODE ORDER BY DATE) AS CLOSE1,
           LAG((CLOSE - BOL_L) / NULLIF(BOL_U - BOL_L,0),1) OVER (PARTITION BY CODE ORDER BY DATE) AS POS1,
           LAG((CLOSE - BOL_L) / NULLIF(BOL_U - BOL_L,0),3) OVER (PARTITION BY CODE ORDER BY DATE) AS POS3,
           LAG((CLOSE - BOL_L) / NULLIF(BOL_U - BOL_L,0),5) OVER (PARTITION BY CODE ORDER BY DATE) AS POS5,
           LAG((CLOSE - BOL_L) / NULLIF(BOL_U - BOL_L,0),7) OVER (PARTITION BY CODE ORDER BY DATE) AS POS7,
           LAG((CLOSE - BOL_L) / NULLIF(BOL_U - BOL_L,0),10) OVER (PARTITION BY CODE ORDER BY DATE) AS POS10,
           LAG((CLOSE - BOL_L) / NULLIF(BOL_U - BOL_L,0),15) OVER (PARTITION BY CODE ORDER BY DATE) AS POS15,
           ROW_NUMBER() OVER (PARTITION BY CODE ORDER BY DATE DESC) AS ROW_NO
    FROM TB_ILBONG
)
SELECT A.CODE AS code, K."종목명" AS name
FROM A
JOIN TB_KOSPI K ON A.CODE = K."코드"
WHERE ROW_NO = 1
  AND POS <= 0.15
  AND POS15 > POS7
  AND POS10 > POS3
  AND POS7 > POS3
  AND POS5 > POS1
  AND POS1 < POS
  AND CLOSE > CLOSE1

/*
SELL
AND ROW_NO = 1
AND POS >= 0.85
AND POS15 < POS7
AND POS10 < POS3
AND POS7 < POS3
AND POS5 < POS1
AND POS1 > POS
AND CLOSE < CLOSE1

ETC
AND ROW_NO = 1
AND NOT (
    (
        POS <= 0.15
        AND POS15 > POS7
        AND POS10 > POS3
        AND POS7 > POS3
        AND POS5 > POS1
        AND POS1 < POS
        AND CLOSE > CLOSE1
    )
    OR
    (
        POS >= 0.85
        AND POS15 < POS7
        AND POS10 < POS3
        AND POS7 < POS3
        AND POS5 < POS1
        AND POS1 > POS
        AND CLOSE < CLOSE1
    )
)
*/

ORDER BY CAST(REPLACE(K."시가총액", ',', '') AS BIGINT) DESC
`,










    st_ilmok: `
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
WHERE ROW_NO = 1

-- BUY
AND ILMOK_DOLPA = '상향돌파'
AND COALESCE(DOLPA3, '') != '상향돌파'
AND COALESCE(DOLPA5, '') != '상향돌파'
AND COALESCE(DOLPA10, '') != '상향돌파'

-- SELL
-- AND ILMOK_DOLPA = '하향돌파'
-- AND COALESCE(DOLPA3, '') != '하향돌파'
-- AND COALESCE(DOLPA5, '') != '하향돌파'
-- AND COALESCE(DOLPA10, '') != '하향돌파'

-- ETC (BUY/SELL 제외)
-- AND NOT (
--     (
--         ILMOK_DOLPA = '상향돌파'
--         AND COALESCE(DOLPA3, '') != '상향돌파'
--         AND COALESCE(DOLPA5, '') != '상향돌파'
--         AND COALESCE(DOLPA10, '') != '상향돌파'
--     )
--     OR
--     (
--         ILMOK_DOLPA = '하향돌파'
--         AND COALESCE(DOLPA3, '') != '하향돌파'
--         AND COALESCE(DOLPA5, '') != '하향돌파'
--         AND COALESCE(DOLPA10, '') != '하향돌파'
--     )
-- )

ORDER BY CAST(REPLACE(K."시가총액", ',', '') AS BIGINT) DESC;
`,









    st_ilmok: `
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
WHERE ROW_NO = 1

-- BUY
AND ILMOK_DOLPA = '상향돌파'
AND COALESCE(DOLPA3, '') != '상향돌파'
AND COALESCE(DOLPA5, '') != '상향돌파'
AND COALESCE(DOLPA10, '') != '상향돌파'

-- SELL
-- AND ILMOK_DOLPA = '하향돌파'
-- AND COALESCE(DOLPA3, '') != '하향돌파'
-- AND COALESCE(DOLPA5, '') != '하향돌파'
-- AND COALESCE(DOLPA10, '') != '하향돌파'

-- ETC (BUY/SELL 제외)
-- AND NOT (
--     (
--         ILMOK_DOLPA = '상향돌파'
--         AND COALESCE(DOLPA3, '') != '상향돌파'
--         AND COALESCE(DOLPA5, '') != '상향돌파'
--         AND COALESCE(DOLPA10, '') != '상향돌파'
--     )
--     OR
--     (
--         ILMOK_DOLPA = '하향돌파'
--         AND COALESCE(DOLPA3, '') != '하향돌파'
--         AND COALESCE(DOLPA5, '') != '하향돌파'
--         AND COALESCE(DOLPA10, '') != '하향돌파'
--     )
-- )

ORDER BY CAST(REPLACE(K."시가총액", ',', '') AS BIGINT) DESC;
`,








    st_vol: `
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
JOIN TB_KOSPI K ON A.CODE = K."코드"
WHERE ROW_NO = 1

-- BUY
AND VOL15 > VOL7
AND VOL15 > VOL3
AND VOL10 > VOL3
AND VOL7 > VOL3
AND VOL5 > VOL1
AND VOL3 > VOL1
AND VOL2 > VOL1
AND VOLUME >= VOL1 * 2

-- SELL
-- AND VOL15 < VOL7
-- AND VOL15 < VOL3
-- AND VOL10 < VOL3
-- AND VOL7 < VOL3
-- AND VOL5 < VOL1
-- AND VOL3 < VOL1
-- AND VOL2 < VOL1
-- AND VOLUME <= VOL1 * 0.5

-- ETC (BUY/SELL 제외)
-- AND NOT (
--     (
--         VOL15 > VOL7
--         AND VOL15 > VOL3
--         AND VOL10 > VOL3
--         AND VOL7 > VOL3
--         AND VOL5 > VOL1
--         AND VOL3 > VOL1
--         AND VOL2 > VOL1
--         AND VOLUME >= VOL1 * 2
--     )
--     OR
--     (
--         VOL15 < VOL7
--         AND VOL15 < VOL3
--         AND VOL10 < VOL3
--         AND VOL7 < VOL3
--         AND VOL5 < VOL1
--         AND VOL3 < VOL1
--         AND VOL2 < VOL1
--         AND VOLUME <= VOL1 * 0.5
--     )
-- )

ORDER BY CAST(REPLACE(K."시가총액", ',', '') AS BIGINT) DESC;
`,


    st_ma20: `
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
SELECT A.CODE, K."종목명", A.DATE, A.MA20, A.MA60
FROM A
JOIN TB_KOSPI K
  ON A.CODE = K."코드"
WHERE
    ROW_NO = 1

    -- BUY : 20일선이 60일선으로 접근(골든크로스 직전)
    AND DIFF15 < DIFF7
    AND DIFF15 < DIFF3
    AND DIFF10 < DIFF3
    AND DIFF7 < DIFF3
    AND DIFF5 < DIFF1
    AND DIFF3 < DIFF
    AND DIFF2 < DIFF
    AND DIFF1 < DIFF
    AND ABS(DIFF) / GREATEST(MA60, 1) <= 0.05

    -- SELL : 20일선이 60일선으로 접근(데드크로스 직전)
    -- AND DIFF15 > DIFF7
    -- AND DIFF15 > DIFF3
    -- AND DIFF10 > DIFF3
    -- AND DIFF7 > DIFF3
    -- AND DIFF5 > DIFF1
    -- AND DIFF3 > DIFF
    -- AND DIFF2 > DIFF
    -- AND DIFF1 > DIFF
    -- AND ABS(DIFF) / GREATEST(MA60, 1) <= 0.05

ORDER BY A.CODE;
`,


    st_sales: `
WITH A AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY 코드
               ORDER BY 기간 DESC
           ) AS RN
    FROM TB_NAVER_FIN
    WHERE 구분 = '분기'
      AND 기간 NOT LIKE '%(E)%'
)
SELECT
    K."코드",
    K."종목명",
    S1.기간,
    S1.매출 AS 매출1,
    S2.매출 AS 매출2,
    S3.매출 AS 매출3,
    S4.매출 AS 매출4,
    S1.영업이익 AS 영업이익1,
    S2.영업이익 AS 영업이익2,
    S3.영업이익 AS 영업이익3,
    S4.영업이익 AS 영업이익4
FROM
    (SELECT * FROM A WHERE RN = 4) S1
    JOIN (SELECT * FROM A WHERE RN = 3) S2
      ON S1.코드 = S2.코드
    JOIN (SELECT * FROM A WHERE RN = 2) S3
      ON S1.코드 = S3.코드
    JOIN (SELECT * FROM A WHERE RN = 1) S4
      ON S1.코드 = S4.코드
    JOIN TB_KOSPI K
      ON S1.코드 = K."코드"
WHERE

    -- BUY : 최근 4개 분기 연속 증가
    S1.매출 < S2.매출
    AND S2.매출 < S3.매출
    AND S3.매출 < S4.매출
    AND S1.영업이익 < S2.영업이익
    AND S2.영업이익 < S3.영업이익
    AND S3.영업이익 < S4.영업이익

    -- SELL : 최근 4개 분기 연속 감소
    -- S1.매출 > S2.매출
    -- AND S2.매출 > S3.매출
    -- AND S3.매출 > S4.매출
    -- AND S1.영업이익 > S2.영업이익
    -- AND S2.영업이익 > S3.영업이익
    -- AND S3.영업이익 > S4.영업이익

ORDER BY K."종목명";
`,


    st_salesqoq: `
WITH A AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY 코드
               ORDER BY 기간 DESC
           ) AS RN
    FROM TB_NAVER_FIN
    WHERE 구분 = '분기'
      AND 기간 NOT LIKE '%(E)%'
)
SELECT
    K."코드",
    K."종목명",
    S1.기간,
    S1.매출QOQ AS 매출QOQ1,
    S2.매출QOQ AS 매출QOQ2,
    S3.매출QOQ AS 매출QOQ3,
    S4.매출QOQ AS 매출QOQ4,
    S1.영업이익QOQ AS 영업이익QOQ1,
    S2.영업이익QOQ AS 영업이익QOQ2,
    S3.영업이익QOQ AS 영업이익QOQ3,
    S4.영업이익QOQ AS 영업이익QOQ4
FROM
    (SELECT * FROM A WHERE RN = 4) S1
    JOIN (SELECT * FROM A WHERE RN = 3) S2
      ON S1.코드 = S2.코드
    JOIN (SELECT * FROM A WHERE RN = 2) S3
      ON S1.코드 = S3.코드
    JOIN (SELECT * FROM A WHERE RN = 1) S4
      ON S1.코드 = S4.코드
    JOIN TB_KOSPI K
      ON S1.코드 = K."코드"
WHERE

    -- BUY : 최근 4개 분기 모두 양수
    S1.매출QOQ > 0
    AND S2.매출QOQ > 0
    AND S3.매출QOQ > 0
    AND S4.매출QOQ > 0
    AND S1.영업이익QOQ > 0
    AND S2.영업이익QOQ > 0
    AND S3.영업이익QOQ > 0
    AND S4.영업이익QOQ > 0

    -- SELL : 최근 4개 분기 모두 음수
    -- S1.매출QOQ < 0
    -- AND S2.매출QOQ < 0
    -- AND S3.매출QOQ < 0
    -- AND S4.매출QOQ < 0
    -- AND S1.영업이익QOQ < 0
    -- AND S2.영업이익QOQ < 0
    -- AND S3.영업이익QOQ < 0
    -- AND S4.영업이익QOQ < 0

ORDER BY K."종목명";
`,


    st_asset: `
WITH A AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY 코드
               ORDER BY 기간 DESC
           ) AS RN
    FROM TB_NAVER_FIN
    WHERE 구분 = '연도'
      AND 기간 NOT LIKE '%(E)%'
)
SELECT
    K."코드",
    K."종목명",
    S1.기간,
    S1.자산 AS 자산1,
    S2.자산 AS 자산2,
    S3.자산 AS 자산3,
    S4.자산 AS 자산4
FROM
    (SELECT * FROM A WHERE RN = 4) S1
    JOIN (SELECT * FROM A WHERE RN = 3) S2
      ON S1.코드 = S2.코드
    JOIN (SELECT * FROM A WHERE RN = 2) S3
      ON S1.코드 = S3.코드
    JOIN (SELECT * FROM A WHERE RN = 1) S4
      ON S1.코드 = S4.코드
    JOIN TB_KOSPI K
      ON S1.코드 = K."코드"
WHERE

    -- BUY : 최근 4년 연속 자산 증가
    S1.자산 < S2.자산
    AND S2.자산 < S3.자산
    AND S3.자산 < S4.자산

    -- SELL : 최근 4년 연속 자산 감소
    -- S1.자산 > S2.자산
    -- AND S2.자산 > S3.자산
    -- AND S3.자산 > S4.자산

ORDER BY K."종목명";
`,


    st_cf: `
WITH A AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY 코드
               ORDER BY 기간 DESC
           ) AS RN
    FROM TB_NAVER_FIN
    WHERE 구분 = '연도'
      AND 기간 NOT LIKE '%(E)%'
)
SELECT
    K."코드",
    K."종목명",
    S1.기간,
    S1.영업현금흐름 AS 현금흐름1,
    S2.영업현금흐름 AS 현금흐름2,
    S3.영업현금흐름 AS 현금흐름3,
    S4.영업현금흐름 AS 현금흐름4
FROM
    (SELECT * FROM A WHERE RN = 4) S1
    JOIN (SELECT * FROM A WHERE RN = 3) S2
      ON S1.코드 = S2.코드
    JOIN (SELECT * FROM A WHERE RN = 2) S3
      ON S1.코드 = S3.코드
    JOIN (SELECT * FROM A WHERE RN = 1) S4
      ON S1.코드 = S4.코드
    JOIN TB_KOSPI K
      ON S1.코드 = K."코드"
WHERE

    -- BUY : 최근 영업현금흐름 > 3년 전
    S1.영업현금흐름 < S4.영업현금흐름

    -- SELL : 최근 영업현금흐름 < 3년 전
    -- S1.영업현금흐름 > S4.영업현금흐름

    -- ETC : BUY, SELL 제외
    -- NOT (
    --     S1.영업현금흐름 < S4.영업현금흐름
    --     OR
    --     S1.영업현금흐름 > S4.영업현금흐름
    -- )

ORDER BY K."종목명";
`,


    st_eps: `
WITH A AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY 코드
               ORDER BY 기간 DESC
           ) AS RN
    FROM TB_NAVER_FIN
    WHERE 구분 = '분기'
      AND 기간 NOT LIKE '%(E)%'
)
SELECT
    K."코드",
    K."종목명",
    S1.기간,
    S1.EPS AS EPS1,
    S2.EPS AS EPS2,
    S3.EPS AS EPS3,
    S4.EPS AS EPS4
FROM
    (SELECT * FROM A WHERE RN = 4) S1
    JOIN (SELECT * FROM A WHERE RN = 3) S2
      ON S1.코드 = S2.코드
    JOIN (SELECT * FROM A WHERE RN = 2) S3
      ON S1.코드 = S3.코드
    JOIN (SELECT * FROM A WHERE RN = 1) S4
      ON S1.코드 = S4.코드
    JOIN TB_KOSPI K
      ON S1.코드 = K."코드"
WHERE

    -- BUY : 최근 4개 분기 EPS 연속 증가
    S1.EPS < S2.EPS
    AND S2.EPS < S3.EPS
    AND S3.EPS < S4.EPS

    -- SELL : 최근 4개 분기 EPS 연속 감소
    -- S1.EPS > S2.EPS
    -- AND S2.EPS > S3.EPS
    -- AND S3.EPS > S4.EPS

ORDER BY K."종목명";
`,


    st_epsqoq: `
WITH A AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY 코드
               ORDER BY 기간 DESC
           ) AS RN
    FROM TB_NAVER_FIN
    WHERE 구분 = '분기'
      AND 기간 NOT LIKE '%(E)%'
)
SELECT
    K."코드",
    K."종목명",
    S2.기간,
    S2.EPSQOQ AS EPSQOQ2,
    S3.EPSQOQ AS EPSQOQ3,
    S4.EPSQOQ AS EPSQOQ4
FROM
    (SELECT * FROM A WHERE RN = 3) S2
    JOIN (SELECT * FROM A WHERE RN = 2) S3
      ON S2.코드 = S3.코드
    JOIN (SELECT * FROM A WHERE RN = 1) S4
      ON S2.코드 = S4.코드
    JOIN TB_KOSPI K
      ON S2.코드 = K."코드"
WHERE

    -- BUY : 최근 3개 분기 EPSQOQ 모두 양수
    S2.EPSQOQ > 0
    AND S3.EPSQOQ > 0
    AND S4.EPSQOQ > 0

    -- SELL : 최근 3개 분기 EPSQOQ 모두 음수
    -- S2.EPSQOQ < 0
    -- AND S3.EPSQOQ < 0
    -- AND S4.EPSQOQ < 0

ORDER BY K."종목명";
`,


    st_margin: `
WITH A AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY 코드
               ORDER BY 기간 DESC
           ) AS RN
    FROM TB_NAVER_FIN
    WHERE 구분 = '분기'
      AND 기간 NOT LIKE '%(E)%'
)
SELECT
    K."코드",
    K."종목명",
    S1.기간,
    S1.영업이익률 AS 영업이익률1,
    S2.영업이익률 AS 영업이익률2,
    S3.영업이익률 AS 영업이익률3,
    S4.영업이익률 AS 영업이익률4
FROM
    (SELECT * FROM A WHERE RN = 4) S1
    JOIN (SELECT * FROM A WHERE RN = 3) S2
      ON S1.코드 = S2.코드
    JOIN (SELECT * FROM A WHERE RN = 2) S3
      ON S1.코드 = S3.코드
    JOIN (SELECT * FROM A WHERE RN = 1) S4
      ON S1.코드 = S4.코드
    JOIN TB_KOSPI K
      ON S1.코드 = K."코드"
WHERE

    -- BUY : 최근 4개 분기 영업이익률 연속 증가
    S1.영업이익률 < S2.영업이익률
    AND S2.영업이익률 < S3.영업이익률
    AND S3.영업이익률 < S4.영업이익률

    -- SELL : 최근 4개 분기 영업이익률 연속 감소
    -- S1.영업이익률 > S2.영업이익률
    -- AND S2.영업이익률 > S3.영업이익률
    -- AND S3.영업이익률 > S4.영업이익률

    -- ETC : BUY, SELL 제외
    -- NOT (
    --     (
    --         S1.영업이익률 < S2.영업이익률
    --         AND S2.영업이익률 < S3.영업이익률
    --         AND S3.영업이익률 < S4.영업이익률
    --     )
    --     OR
    --     (
    --         S1.영업이익률 > S2.영업이익률
    --         AND S2.영업이익률 > S3.영업이익률
    --         AND S3.영업이익률 > S4.영업이익률
    --     )
    -- )

ORDER BY
`,


    st_roe: `
WITH A AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY 코드
               ORDER BY 기간 DESC
           ) AS RN
    FROM TB_NAVER_FIN
    WHERE 구분 = '분기'
      AND 기간 NOT LIKE '%(E)%'
)
SELECT
    K."코드",
    K."종목명",
    S1.기간,
    S1.ROE AS ROE1,
    S2.ROE AS ROE2,
    S3.ROE AS ROE3,
    S4.ROE AS ROE4
FROM
    (SELECT * FROM A WHERE RN = 4) S1
    JOIN (SELECT * FROM A WHERE RN = 3) S2
      ON S1.코드 = S2.코드
    JOIN (SELECT * FROM A WHERE RN = 2) S3
      ON S1.코드 = S3.코드
    JOIN (SELECT * FROM A WHERE RN = 1) S4
      ON S1.코드 = S4.코드
    JOIN TB_KOSPI K
      ON S1.코드 = K."코드"
WHERE

    -- BUY : 최근 4개 분기 ROE 연속 증가
    S1.ROE < S2.ROE
    AND S2.ROE < S3.ROE
    AND S3.ROE < S4.ROE

    -- SELL : 최근 4개 분기 ROE 연속 감소
    -- S1.ROE > S2.ROE
    -- AND S2.ROE > S3.ROE
    -- AND S3.ROE > S4.ROE

    -- ETC : BUY, SELL 제외
    -- NOT (
    --     (
    --         S1.ROE < S2.ROE
    --         AND S2.ROE < S3.ROE
    --         AND S3.ROE < S4.ROE
    --     )
    --     OR
    --     (
    --         S1.ROE > S2.ROE
    --         AND S2.ROE > S3.ROE
    --         AND S3.ROE > S4.ROE
    --     )
    -- )

ORDER BY K."종목명";
`,


    st_dept: `
WITH A AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY 코드
               ORDER BY 기간 DESC
           ) AS RN
    FROM TB_NAVER_FIN
    WHERE 구분 = '분기'
      AND 기간 NOT LIKE '%(E)%'
)
SELECT
    K."코드",
    K."종목명",
    S1.기간,
    S1.부채비율 AS 부채비율1,
    S2.부채비율 AS 부채비율2,
    S3.부채비율 AS 부채비율3,
    S4.부채비율 AS 부채비율4
FROM
    (SELECT * FROM A WHERE RN = 4) S1
    JOIN (SELECT * FROM A WHERE RN = 3) S2
      ON S1.코드 = S2.코드
    JOIN (SELECT * FROM A WHERE RN = 2) S3
      ON S1.코드 = S3.코드
    JOIN (SELECT * FROM A WHERE RN = 1) S4
      ON S1.코드 = S4.코드
    JOIN TB_KOSPI K
      ON S1.코드 = K."코드"
WHERE

    -- BUY : 최근 4개 분기 부채비율 연속 감소
    S1.부채비율 > S2.부채비율
    AND S2.부채비율 > S3.부채비율
    AND S3.부채비율 > S4.부채비율

    -- SELL : 최근 4개 분기 부채비율 연속 증가
    -- S1.부채비율 < S2.부채비율
    -- AND S2.부채비율 < S3.부채비율
    -- AND S3.부채비율 < S4.부채비율

    -- ETC : BUY, SELL 제외
    -- NOT (
    --     (
    --         S1.부채비율 > S2.부채비율
    --         AND S2.부채비율 > S3.부채비율
    --         AND S3.부채비율 > S4.부채비율
    --     )
    --     OR
    --     (
    --         S1.부채비율 < S2.부채비율
    --         AND S2.부채비율 < S3.부채비율
    --         AND S3.부채비율 < S4.부채비율
    --     )
    -- )

ORDER BY K."종목명";
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



