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



    st_ma5: `
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
JOIN TB_KOSPI K ON A.CODE = K."코드"
WHERE ROW_NO = 1

/* BUY */
AND COALESCE(DIFF15 < DIFF7, FALSE)
AND COALESCE(DIFF15 < DIFF3, FALSE)
AND COALESCE(DIFF10 < DIFF3, FALSE)
AND COALESCE(DIFF7 < DIFF3, FALSE)
AND COALESCE(DIFF5 < DIFF1, FALSE)
AND COALESCE(DIFF3 < DIFF, FALSE)
AND COALESCE(DIFF2 < DIFF, FALSE)
AND COALESCE(DIFF1 < DIFF, FALSE)
AND COALESCE(ABS(DIFF) / GREATEST(MA20, 1) <= 0.1, FALSE)

/* SELL */
/*
AND COALESCE(DIFF15 > DIFF7, FALSE)
AND COALESCE(DIFF15 > DIFF3, FALSE)
AND COALESCE(DIFF10 > DIFF3, FALSE)
AND COALESCE(DIFF7 > DIFF3, FALSE)
AND COALESCE(DIFF5 > DIFF1, FALSE)
AND COALESCE(DIFF3 > DIFF, FALSE)
AND COALESCE(DIFF2 > DIFF, FALSE)
AND COALESCE(DIFF1 > DIFF, FALSE)
AND COALESCE(ABS(DIFF) / GREATEST(MA20, 1) <= 0.1, FALSE)
*/


/* ETC (BUY/SELL 제외) */
/*
AND NOT (
    (
        COALESCE(DIFF15 < DIFF7, FALSE)
        AND COALESCE(DIFF15 < DIFF3, FALSE)
        AND COALESCE(DIFF10 < DIFF3, FALSE)
        AND COALESCE(DIFF7 < DIFF3, FALSE)
        AND COALESCE(DIFF5 < DIFF1, FALSE)
        AND COALESCE(DIFF3 < DIFF, FALSE)
        AND COALESCE(DIFF2 < DIFF, FALSE)
        AND COALESCE(DIFF1 < DIFF, FALSE)
        AND COALESCE(ABS(DIFF) / GREATEST(MA20, 1) <= 0.1, FALSE)
    )
    OR
    (
        COALESCE(DIFF15 > DIFF7, FALSE)
        AND COALESCE(DIFF15 > DIFF3, FALSE)
        AND COALESCE(DIFF10 > DIFF3, FALSE)
        AND COALESCE(DIFF7 > DIFF3, FALSE)
        AND COALESCE(DIFF5 > DIFF1, FALSE)
        AND COALESCE(DIFF3 > DIFF, FALSE)
        AND COALESCE(DIFF2 > DIFF, FALSE)
        AND COALESCE(DIFF1 > DIFF, FALSE)
        AND COALESCE(ABS(DIFF) / GREATEST(MA20, 1) <= 0.1, FALSE)
    )
)
*/

ORDER BY CAST(REPLACE(K."시가총액", ',', '') AS BIGINT) DESC;
`,




    st_ma20: `
WITH A AS (
    SELECT CODE, DATE, MA20, MA60,
           MA20 - MA60 AS DIFF,
           LAG(MA20 - MA60,1) OVER (PARTITION BY CODE ORDER BY DATE) AS DIFF1,
           LAG(MA20 - MA60,2) OVER (PARTITION BY CODE ORDER BY DATE) AS DIFF2,
           LAG(MA20 - MA60,3) OVER (PARTITION BY CODE ORDER BY DATE) AS DIFF3,
           LAG(MA20 - MA60,5) OVER (PARTITION BY CODE ORDER BY DATE) AS DIFF5,
           LAG(MA20 - MA60,7) OVER (PARTITION BY CODE ORDER BY DATE) AS DIFF7,
           LAG(MA20 - MA60,10) OVER (PARTITION BY CODE ORDER BY DATE) AS DIFF10,
           LAG(MA20 - MA60,15) OVER (PARTITION BY CODE ORDER BY DATE) AS DIFF15,
           ROW_NUMBER() OVER (PARTITION BY CODE ORDER BY DATE DESC) AS ROW_NO
    FROM TB_ILBONG
)
SELECT A.CODE AS code,K."종목명" AS name
FROM A
JOIN TB_KOSPI K ON A.CODE=K."코드"
WHERE ROW_NO=1

/* BUY */
AND DIFF15<DIFF7
AND DIFF15<DIFF3
AND DIFF10<DIFF3
AND DIFF7<DIFF3
AND DIFF5<DIFF1
AND DIFF3<DIFF
AND DIFF2<DIFF
AND DIFF1<DIFF
AND ABS(DIFF)/GREATEST(MA60,1)<=0.05

/* SELL */
/*
AND DIFF15>DIFF7
AND DIFF15>DIFF3
AND DIFF10>DIFF3
AND DIFF7>DIFF3
AND DIFF5>DIFF1
AND DIFF3>DIFF
AND DIFF2>DIFF
AND DIFF1>DIFF
AND ABS(DIFF)/GREATEST(MA60,1)<=0.05
*/

/* ETC */
/*
AND NOT (
    (
        COALESCE(DIFF15<DIFF7,FALSE)
        AND COALESCE(DIFF15<DIFF3,FALSE)
        AND COALESCE(DIFF10<DIFF3,FALSE)
        AND COALESCE(DIFF7<DIFF3,FALSE)
        AND COALESCE(DIFF5<DIFF1,FALSE)
        AND COALESCE(DIFF3<DIFF,FALSE)
        AND COALESCE(DIFF2<DIFF,FALSE)
        AND COALESCE(DIFF1<DIFF,FALSE)
        AND COALESCE(ABS(DIFF)/GREATEST(MA60,1)<=0.05,FALSE)
    )
    OR
    (
        COALESCE(DIFF15>DIFF7,FALSE)
        AND COALESCE(DIFF15>DIFF3,FALSE)
        AND COALESCE(DIFF10>DIFF3,FALSE)
        AND COALESCE(DIFF7>DIFF3,FALSE)
        AND COALESCE(DIFF5>DIFF1,FALSE)
        AND COALESCE(DIFF3>DIFF,FALSE)
        AND COALESCE(DIFF2>DIFF,FALSE)
        AND COALESCE(DIFF1>DIFF,FALSE)
        AND COALESCE(ABS(DIFF)/GREATEST(MA60,1)<=0.05,FALSE)
    )
)
*/

ORDER BY CAST(REPLACE(K."시가총액",',','') AS BIGINT) DESC
`,


    st_sales: `
WITH Q AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY 코드
               ORDER BY 기간 DESC
           ) AS RN
    FROM TB_NAVER_FIN
    WHERE 구분 = '분기'
      AND 기간 NOT LIKE '%(E)%'
      AND 매출 IS NOT NULL
      AND 영업이익 IS NOT NULL
)

SELECT
    K."코드" AS code,
    K."종목명" AS name
FROM
    (SELECT * FROM Q WHERE RN=1) S1
    JOIN (SELECT * FROM Q WHERE RN=2) S2
      ON S1.코드 = S2.코드
    JOIN (SELECT * FROM Q WHERE RN=3) S3
      ON S1.코드 = S3.코드
    JOIN TB_KOSPI K
      ON S1.코드 = K."코드"
WHERE 1=1 AND

    /* =========================
       BUY (ACTIVE)
    ========================= */
    (
        S1.매출 > S2.매출
        AND S2.매출 > S3.매출
        AND S1.영업이익 > S2.영업이익
        AND S2.영업이익 > S3.영업이익
    )

    /* =========================
       SELL (DISABLED)
    ========================= */
    /*
    (
        S1.매출 < S2.매출
        AND S2.매출 < S3.매출
        AND S1.영업이익 < S2.영업이익
        AND S2.영업이익 < S3.영업이익
    )
    */

    /* =========================
       ETC (DISABLED or OPTIONAL)
       → BUY/SELL 둘 다 아닌 구간
    ========================= */
    /*
    NOT (
        (
            S1.매출 > S2.매출
            AND S2.매출 > S3.매출
            AND S1.영업이익 > S2.영업이익
            AND S2.영업이익 > S3.영업이익
        )
        OR
        (
            S1.매출 < S2.매출
            AND S2.매출 < S3.매출
            AND S1.영업이익 < S2.영업이익
            AND S2.영업이익 < S3.영업이익
        )
    )
    */

ORDER BY CAST(REPLACE(K."시가총액", ',', '') AS BIGINT) DESC
`,


    st_salesqoq: `
WITH Q AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY 코드
               ORDER BY 기간 DESC
           ) AS RN
    FROM TB_NAVER_FIN
    WHERE 구분 = '분기'
      AND 기간 NOT LIKE '%(E)%'
      AND 매출QOQ IS NOT NULL
      AND 영업이익QOQ IS NOT NULL
)

SELECT
    K."코드" AS code,
    K."종목명" AS name
FROM
    (SELECT * FROM Q WHERE RN=1) S1
    JOIN (SELECT * FROM Q WHERE RN=2) S2
      ON S1.코드 = S2.코드
    JOIN (SELECT * FROM Q WHERE RN=3) S3
      ON S1.코드 = S3.코드
    JOIN TB_KOSPI K
      ON S1.코드 = K."코드"
WHERE

1=1

/* =========================
   BUY (ACTIVE)
========================= */
AND (
    S1.매출QOQ > 0
    AND S2.매출QOQ > 0
    AND S3.매출QOQ > 0
    AND S1.영업이익QOQ > 0
    AND S2.영업이익QOQ > 0
    AND S3.영업이익QOQ > 0
)

/* =========================
   SELL (DISABLED)
========================= */
/*
AND (
    S1.매출QOQ < 0
    AND S2.매출QOQ < 0
    AND S3.매출QOQ < 0
    AND S1.영업이익QOQ < 0
    AND S2.영업이익QOQ < 0
    AND S3.영업이익QOQ < 0
)
*/

/* =========================
   ETC (DISABLED)
========================= */
/*
AND NOT (
    (
        S1.매출QOQ > 0
        AND S2.매출QOQ > 0
        AND S3.매출QOQ > 0
        AND S1.영업이익QOQ > 0
        AND S2.영업이익QOQ > 0
        AND S3.영업이익QOQ > 0
    )
    OR
    (
        S1.매출QOQ < 0
        AND S2.매출QOQ < 0
        AND S3.매출QOQ < 0
        AND S1.영업이익QOQ < 0
        AND S2.영업이익QOQ < 0
        AND S3.영업이익QOQ < 0
    )
)
*/

ORDER BY CAST(REPLACE(K."시가총액", ',', '') AS BIGINT) DESC
`,


    st_asset: `
WITH A AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY 코드
               ORDER BY 기간 DESC
           ) AS RN
    FROM TB_NAVER_FIN
    WHERE 구분 = '분기'
      AND 기간 NOT LIKE '%(E)%'
      AND 자산 IS NOT NULL
      AND 자산 != 0
)
SELECT
    K."코드" AS code,
    K."종목명" AS name
FROM
    (SELECT * FROM A WHERE RN=1) S1
    JOIN (SELECT * FROM A WHERE RN=2) S2
      ON S1.코드 = S2.코드
    JOIN (SELECT * FROM A WHERE RN=3) S3
      ON S1.코드 = S3.코드
    JOIN TB_KOSPI K
      ON S1.코드 = K."코드"
WHERE 1=1

-- BUY (ACTIVE)
AND (
    S1.자산 > S2.자산
    AND S2.자산 > S3.자산
)


-- SELL (DISABLED)
/*
AND (
    S1.자산 < S2.자산
    AND S2.자산 < S3.자산
)
*/


-- ETC
/*
AND NOT (
    (
        S1.자산 > S2.자산
        AND S2.자산 > S3.자산
    )
    OR
    (
        S1.자산 < S2.자산
        AND S2.자산 < S3.자산
    )
)
*/

ORDER BY CAST(REPLACE(K."시가총액", ',', '') AS BIGINT) DESC;
`,


    st_cf: `
WITH A AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY 코드
               ORDER BY 기간 DESC
           ) AS RN
    FROM TB_NAVER_FIN
    WHERE 구분 = '분기'
      AND 기간 NOT LIKE '%(E)%'
      AND 영업현금흐름 IS NOT NULL
)
SELECT
    K."코드" AS code,
    K."종목명" AS name
FROM
    (SELECT * FROM A WHERE RN=1) S1
    JOIN (SELECT * FROM A WHERE RN=2) S2
      ON S1.코드 = S2.코드
    JOIN (SELECT * FROM A WHERE RN=3) S3
      ON S1.코드 = S3.코드
    JOIN TB_KOSPI K
      ON S1.코드 = K."코드"
WHERE 1=1

-- BUY
AND (
    S1.영업현금흐름 > S2.영업현금흐름
    AND S2.영업현금흐름 > S3.영업현금흐름
)

-- SELL
/*
AND (
    S1.영업현금흐름 < S2.영업현금흐름
    AND S2.영업현금흐름 < S3.영업현금흐름
)
*/

-- ETC
/*
AND NOT (
    (
        S1.영업현금흐름 > S2.영업현금흐름
        AND S2.영업현금흐름 > S3.영업현금흐름
    )
    OR
    (
        S1.영업현금흐름 < S2.영업현금흐름
        AND S2.영업현금흐름 < S3.영업현금흐름
    )
)
*/

ORDER BY CAST(REPLACE(K."시가총액", ',', '') AS BIGINT) DESC
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
      AND EPS IS NOT NULL
)
SELECT
    K."코드" AS code,
    K."종목명" AS name
FROM
    (SELECT * FROM A WHERE RN=1) S1
    JOIN (SELECT * FROM A WHERE RN=2) S2
      ON S1.코드 = S2.코드
    JOIN (SELECT * FROM A WHERE RN=3) S3
      ON S1.코드 = S3.코드
    JOIN (SELECT * FROM A WHERE RN=4) S4
      ON S1.코드 = S4.코드
    JOIN TB_KOSPI K
      ON S1.코드 = K."코드"
WHERE 1=1

-- BUY
AND (
    S1.EPS > S2.EPS
    AND S2.EPS > S3.EPS
    AND S3.EPS > S4.EPS
)

-- SELL
/*
AND (
    S1.EPS < S2.EPS
    AND S2.EPS < S3.EPS
    AND S3.EPS < S4.EPS
)
*/

-- ETC
/*
AND NOT (
    (
        S1.EPS > S2.EPS
        AND S2.EPS > S3.EPS
        AND S3.EPS > S4.EPS
    )
    OR
    (
        S1.EPS < S2.EPS
        AND S2.EPS < S3.EPS
        AND S3.EPS < S4.EPS
    )
)
*/

ORDER BY CAST(REPLACE(K."시가총액", ',', '') AS BIGINT) DESC
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
      AND EPSQOQ IS NOT NULL
)
SELECT
    K."코드" AS code,
    K."종목명" AS name
FROM
    (SELECT * FROM A WHERE RN=1) S1
    JOIN (SELECT * FROM A WHERE RN=2) S2
      ON S1.코드 = S2.코드
    JOIN (SELECT * FROM A WHERE RN=3) S3
      ON S1.코드 = S3.코드
    JOIN (SELECT * FROM A WHERE RN=4) S4
      ON S1.코드 = S4.코드
    JOIN TB_KOSPI K
      ON S1.코드 = K."코드"
WHERE 1=1

-- BUY
AND (
    S1.EPSQOQ > S2.EPSQOQ
    AND S2.EPSQOQ > S3.EPSQOQ
    AND S3.EPSQOQ > S4.EPSQOQ
)

-- SELL
/*
AND (
    S1.EPSQOQ < S2.EPSQOQ
    AND S2.EPSQOQ < S3.EPSQOQ
    AND S3.EPSQOQ < S4.EPSQOQ
)
*/

-- ETC
/*
AND NOT (
    (
        S1.EPSQOQ > S2.EPSQOQ
        AND S2.EPSQOQ > S3.EPSQOQ
        AND S3.EPSQOQ > S4.EPSQOQ
    )
    OR
    (
        S1.EPSQOQ < S2.EPSQOQ
        AND S2.EPSQOQ < S3.EPSQOQ
        AND S3.EPSQOQ < S4.EPSQOQ
    )
)
*/

ORDER BY CAST(REPLACE(K."시가총액", ',', '') AS BIGINT) DESC
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
      AND 영업이익률 IS NOT NULL
)

SELECT
    K."코드" AS code,
    K."종목명" AS name
FROM
    (SELECT * FROM A WHERE RN=1) S1
    JOIN (SELECT * FROM A WHERE RN=2) S2
      ON S1.코드 = S2.코드
    JOIN (SELECT * FROM A WHERE RN=3) S3
      ON S1.코드 = S3.코드
    JOIN (SELECT * FROM A WHERE RN=4) S4
      ON S1.코드 = S4.코드
    JOIN TB_KOSPI K
      ON S1.코드 = K."코드"
WHERE 1=1

-- BUY
AND (
    S1.영업이익률 > S2.영업이익률
    AND S2.영업이익률 > S3.영업이익률
    AND S3.영업이익률 > S4.영업이익률
)

-- SELL
/*
AND (
    S1.영업이익률 < S2.영업이익률
    AND S2.영업이익률 < S3.영업이익률
    AND S3.영업이익률 < S4.영업이익률
)
*/

-- ETC
/*
AND NOT (
    (
        S1.영업이익률 > S2.영업이익률
        AND S2.영업이익률 > S3.영업이익률
        AND S3.영업이익률 > S4.영업이익률
    )
    OR
    (
        S1.영업이익률 < S2.영업이익률
        AND S2.영업이익률 < S3.영업이익률
        AND S3.영업이익률 < S4.영업이익률
    )
)
*/

ORDER BY CAST(REPLACE(K."시가총액", ',', '') AS BIGINT) DESC
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
      AND ROE IS NOT NULL
)
SELECT
    K."코드" AS code,
    K."종목명" AS name
FROM
    (SELECT * FROM A WHERE RN=1) S1
    JOIN (SELECT * FROM A WHERE RN=2) S2
      ON S1.코드 = S2.코드
    JOIN (SELECT * FROM A WHERE RN=3) S3
      ON S1.코드 = S3.코드
    JOIN (SELECT * FROM A WHERE RN=4) S4
      ON S1.코드 = S4.코드
    JOIN TB_KOSPI K
      ON S1.코드 = K."코드"
WHERE 1=1

-- BUY
AND (
    S1.ROE > S2.ROE
    AND S2.ROE > S3.ROE
    AND S3.ROE > S4.ROE
)

-- SELL
/*
AND (
    S1.ROE < S2.ROE
    AND S2.ROE < S3.ROE
    AND S3.ROE < S4.ROE
)
*/

-- ETC
/*
AND NOT (
    (
        S1.ROE > S2.ROE
        AND S2.ROE > S3.ROE
        AND S3.ROE > S4.ROE
    )
    OR
    (
        S1.ROE < S2.ROE
        AND S2.ROE < S3.ROE
        AND S3.ROE < S4.ROE
    )
)
*/

ORDER BY CAST(REPLACE(K."시가총액", ',', '') AS BIGINT) DESC
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
      AND 부채비율 IS NOT NULL
)
SELECT
    K."코드" AS code,
    K."종목명" AS name
FROM
    (SELECT * FROM A WHERE RN=1) S1
    JOIN (SELECT * FROM A WHERE RN=2) S2
      ON S1.코드 = S2.코드
    JOIN (SELECT * FROM A WHERE RN=3) S3
      ON S1.코드 = S3.코드
    JOIN (SELECT * FROM A WHERE RN=4) S4
      ON S1.코드 = S4.코드
    JOIN TB_KOSPI K
      ON S1.코드 = K."코드"
WHERE 1=1

-- BUY
AND (
    S1.부채비율 < S2.부채비율
    AND S2.부채비율 < S3.부채비율
    AND S3.부채비율 < S4.부채비율
)

-- SELL
/*
AND (
    S1.부채비율 > S2.부채비율
    AND S2.부채비율 > S3.부채비율
    AND S3.부채비율 > S4.부채비율
)
*/

-- ETC
/*
AND NOT (
    (
        S1.부채비율 < S2.부채비율
        AND S2.부채비율 < S3.부채비율
        AND S3.부채비율 < S4.부채비율
    )
    OR
    (
        S1.부채비율 > S2.부채비율
        AND S2.부채비율 > S3.부채비율
        AND S3.부채비율 > S4.부채비율
    )
)
*/

ORDER BY CAST(REPLACE(K."시가총액", ',', '') AS BIGINT) DESC
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



