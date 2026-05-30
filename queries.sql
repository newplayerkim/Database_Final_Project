-- ============================================================
--  미니 중고 거래 플랫폼 — 핵심 쿼리 + 트랜잭션
--  PostgreSQL 기준
-- ============================================================


-- ────────────────────────────────────────────────────────────
--  Q1. JOIN — 상품 목록 조회 + 필터
--
--  users, categories, products 세 테이블을 JOIN해서
--  카테고리명·판매자 닉네임을 포함한 상품 목록 조회.
--  WHERE 조건을 조합해 카테고리·가격·판매자·제목 필터 적용.
-- ────────────────────────────────────────────────────────────

-- Q1-1. 기본 상품 목록 (판매중인 것만, 최신순)
SELECT
    p.id,
    p.title,
    p.price,
    p.status,
    c.name     AS category,
    u.nickname AS seller,
    p.created_at
FROM products p
JOIN users      u ON p.seller_id   = u.id
JOIN categories c ON p.category_id = c.id
WHERE p.status = 'available'
ORDER BY p.created_at DESC;


-- Q1-2. 카테고리 필터 (전자기기만)
SELECT
    p.id,
    p.title,
    p.price,
    c.name     AS category,
    u.nickname AS seller
FROM products p
JOIN users      u ON p.seller_id   = u.id
JOIN categories c ON p.category_id = c.id
WHERE p.status = 'available'
  AND c.name   = '전자기기'
ORDER BY p.price DESC;


-- Q1-3. 가격 범위 필터 (5만원 ~ 20만원)
SELECT
    p.id,
    p.title,
    p.price,
    c.name     AS category,
    u.nickname AS seller
FROM products p
JOIN users      u ON p.seller_id   = u.id
JOIN categories c ON p.category_id = c.id
WHERE p.status = 'available'
  AND p.price BETWEEN 50000 AND 200000
ORDER BY p.price ASC;


-- Q1-4. 판매자 필터 (김민준이 올린 상품)
SELECT
    p.id,
    p.title,
    p.price,
    p.status,
    c.name AS category
FROM products p
JOIN users      u ON p.seller_id   = u.id
JOIN categories c ON p.category_id = c.id
WHERE u.nickname = '김민준'
ORDER BY p.created_at DESC;


-- Q1-5. 제목 검색 (키워드: '맥북')
SELECT
    p.id,
    p.title,
    p.price,
    c.name     AS category,
    u.nickname AS seller
FROM products p
JOIN users      u ON p.seller_id   = u.id
JOIN categories c ON p.category_id = c.id
WHERE p.status = 'available'
  AND p.title LIKE '%맥북%'
ORDER BY p.created_at DESC;


-- Q1-6. 복합 필터 (전자기기 + 50만원 이하 + 판매중)
SELECT
    p.id,
    p.title,
    p.price,
    c.name     AS category,
    u.nickname AS seller
FROM products p
JOIN users      u ON p.seller_id   = u.id
JOIN categories c ON p.category_id = c.id
WHERE p.status = 'available'
  AND c.name   = '전자기기'
  AND p.price <= 500000
ORDER BY p.price ASC;


-- ────────────────────────────────────────────────────────────
--  Q2. GROUP BY — 카테고리별 통계 집계
--
--  categories와 products를 JOIN한 뒤 카테고리 기준으로 묶어
--  상품 수·평균가·최저가·최고가를 집계.
--  ROUND(AVG())::INT 로 소수점 없이 정수 반환.
-- ────────────────────────────────────────────────────────────

-- Q2-1. 카테고리별 전체 상품 통계
SELECT
    c.name                          AS category,
    COUNT(p.id)                     AS total_count,
    ROUND(AVG(p.price))::INT        AS avg_price,
    MIN(p.price)                    AS min_price,
    MAX(p.price)                    AS max_price
FROM categories c
LEFT JOIN products p ON c.id = p.category_id
GROUP BY c.id, c.name
ORDER BY total_count DESC;


-- Q2-2. 판매중인 상품만 집계 (sold 제외)
SELECT
    c.name                          AS category,
    COUNT(p.id)                     AS available_count,
    ROUND(AVG(p.price))::INT        AS avg_price,
    MIN(p.price)                    AS min_price,
    MAX(p.price)                    AS max_price
FROM categories c
LEFT JOIN products p ON c.id        = p.category_id
                     AND p.status   = 'available'
GROUP BY c.id, c.name
ORDER BY available_count DESC;


-- Q2-3. 판매자별 등록·판매완료·판매중 건수
SELECT
    u.nickname                                         AS seller,
    COUNT(p.id)                                        AS total_listed,
    COUNT(CASE WHEN p.status = 'sold'      THEN 1 END) AS sold_count,
    COUNT(CASE WHEN p.status = 'available' THEN 1 END) AS available_count
FROM users u
LEFT JOIN products p ON u.id = p.seller_id
GROUP BY u.id, u.nickname
ORDER BY total_listed DESC;


-- ────────────────────────────────────────────────────────────
--  Q3. 서브쿼리 — 카테고리 평균보다 비싼 상품
--
--  CTE(WITH)로 카테고리별 평균가를 미리 한 번만 계산한 뒤
--  메인 쿼리에서 JOIN해서 사용.
--  → 상관 서브쿼리 반복 실행 없이 성능·가독성 개선.
-- ────────────────────────────────────────────────────────────

-- Q3-1. 카테고리 평균보다 비싼 상품 (CTE 활용)
WITH category_avg AS (
    SELECT
        category_id,
        ROUND(AVG(price))::INT AS avg_price
    FROM products
    GROUP BY category_id
)
SELECT
    p.title,
    p.price,
    c.name                     AS category,
    u.nickname                 AS seller,
    ca.avg_price               AS category_avg,
    p.price - ca.avg_price     AS diff_from_avg
FROM products p
JOIN users        u  ON p.seller_id   = u.id
JOIN categories   c  ON p.category_id = c.id
JOIN category_avg ca ON p.category_id = ca.category_id
WHERE p.status = 'available'
  AND p.price  > ca.avg_price
ORDER BY c.name, p.price DESC;


-- Q3-2. 전체 평균보다 비싼 상품 (단순 서브쿼리)
SELECT
    p.title,
    p.price,
    c.name                                    AS category,
    u.nickname                                AS seller,
    (SELECT ROUND(AVG(price))::INT
     FROM products)                           AS overall_avg
FROM products p
JOIN users      u ON p.seller_id   = u.id
JOIN categories c ON p.category_id = c.id
WHERE p.status = 'available'
  AND p.price  > (SELECT AVG(price) FROM products)
ORDER BY p.price DESC;


-- ────────────────────────────────────────────────────────────
--  Q4. JOIN — 거래 내역 전체 조회
--
--  transactions, products, users(판매자·구매자) 를 JOIN해서
--  거래 내역을 한눈에 조회.
--  FastAPI /transactions 엔드포인트에서 그대로 사용.
-- ────────────────────────────────────────────────────────────
SELECT
    t.id            AS transaction_id,
    p.title,
    seller.nickname AS seller,
    buyer.nickname  AS buyer,
    t.price,
    t.created_at
FROM transactions t
JOIN products p      ON t.product_id = p.id
JOIN users    seller ON p.seller_id  = seller.id
JOIN users    buyer  ON t.buyer_id   = buyer.id
ORDER BY t.created_at DESC;


-- ────────────────────────────────────────────────────────────
--  T1. 트랜잭션 — 구매 처리
--
--  DO $$ 블록 안에서:
--    ① FOR UPDATE 로 행 잠금 (동시 구매 방지)
--    ② UPDATE products.status → 'sold'
--    ③ GET DIAGNOSTICS 로 업데이트 행 수 확인
--       0행이면 이미 판매된 상품 → RAISE EXCEPTION → 자동 ROLLBACK
--    ④ INSERT INTO transactions
--  예외 없이 끝까지 실행되면 자동 COMMIT.
-- ────────────────────────────────────────────────────────────

-- T1-1. 정상 구매 처리 (product_id=1, buyer_id=2)
DO $$
DECLARE
    updated_rows INT;
    bought_price INT;
BEGIN
    -- ① 행 잠금: 다른 트랜잭션이 같은 상품을 동시에 구매하지 못하도록
    SELECT price INTO bought_price
    FROM   products
    WHERE  id = 1
    FOR UPDATE;

    -- ② 상태 변경 (available 인 경우에만)
    UPDATE products
    SET    status = 'sold'
    WHERE  id     = 1
      AND  status = 'available';

    -- ③ 업데이트된 행 수 확인
    GET DIAGNOSTICS updated_rows = ROW_COUNT;

    IF updated_rows = 0 THEN
        RAISE EXCEPTION '이미 판매된 상품입니다 (product_id=1)';
        -- RAISE 시 자동 ROLLBACK → transactions INSERT 실행 안 됨
    END IF;

    -- ④ 거래 내역 기록 (거래 당시 가격 그대로 보존)
    INSERT INTO transactions (product_id, buyer_id, price)
    VALUES (1, 2, bought_price);

END;
$$;


-- T1-2. 실패 케이스 — 이미 sold 상품 구매 시도
--        (product_id=10 은 더미 데이터에서 이미 sold)
DO $$
DECLARE
    updated_rows INT;
    bought_price INT;
BEGIN
    SELECT price INTO bought_price
    FROM   products
    WHERE  id = 10
    FOR UPDATE;

    UPDATE products
    SET    status = 'sold'
    WHERE  id     = 10
      AND  status = 'available';

    GET DIAGNOSTICS updated_rows = ROW_COUNT;

    IF updated_rows = 0 THEN
        RAISE EXCEPTION '이미 판매된 상품입니다 (product_id=10)';
    END IF;

    INSERT INTO transactions (product_id, buyer_id, price)
    VALUES (10, 3, bought_price);

END;
$$;
-- → "이미 판매된 상품입니다" 예외 발생 + 자동 ROLLBACK
-- → transactions 에 아무것도 INSERT 되지 않음


-- T1-3. 결과 확인
SELECT
    t.id            AS transaction_id,
    p.title,
    p.status,
    seller.nickname AS seller,
    buyer.nickname  AS buyer,
    t.price,
    t.created_at
FROM transactions t
JOIN products p      ON t.product_id = p.id
JOIN users    seller ON p.seller_id  = seller.id
JOIN users    buyer  ON t.buyer_id   = buyer.id
ORDER BY t.created_at DESC;
