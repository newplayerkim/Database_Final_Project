-- ============================================================
--  미니 중고 거래 플랫폼 — DDL + 더미 데이터
--  PostgreSQL 기준
-- ============================================================


-- ────────────────────────────────────────────────────────────
--  0. 초기화 (재실행 시 깔끔하게)
--     참조하는 쪽(자식)부터 DROP해야 FK 에러 없음
-- ────────────────────────────────────────────────────────────
DROP INDEX IF EXISTS idx_products_seller;
DROP INDEX IF EXISTS idx_products_category;
DROP INDEX IF EXISTS idx_products_status;
DROP INDEX IF EXISTS idx_products_price;

DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS users;


-- ────────────────────────────────────────────────────────────
--  1. users
-- ────────────────────────────────────────────────────────────
CREATE TABLE users (
    id         SERIAL      PRIMARY KEY,
    nickname   VARCHAR(50) NOT NULL UNIQUE,
    created_at TIMESTAMP   NOT NULL DEFAULT NOW()
);


-- ────────────────────────────────────────────────────────────
--  2. categories
-- ────────────────────────────────────────────────────────────
CREATE TABLE categories (
    id   SERIAL      PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);


-- ────────────────────────────────────────────────────────────
--  3. products
-- ────────────────────────────────────────────────────────────
CREATE TABLE products (
    id          SERIAL       PRIMARY KEY,
    seller_id   INT          NOT NULL
                             REFERENCES users(id) ON DELETE RESTRICT,
    category_id INT          NOT NULL
                             REFERENCES categories(id) ON DELETE RESTRICT,
    title       VARCHAR(100) NOT NULL,
    price       INT          NOT NULL CHECK (price >= 0),
    status      VARCHAR(10)  NOT NULL DEFAULT 'available'
                             CHECK (status IN ('available', 'sold')),
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- 자주 쓰는 검색 컬럼에 인덱스
--   (PK인 id는 자동 인덱스 생성되므로 제외)
CREATE INDEX idx_products_seller   ON products(seller_id);
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_status   ON products(status);
CREATE INDEX idx_products_price    ON products(price);


-- ────────────────────────────────────────────────────────────
--  4. transactions
-- ────────────────────────────────────────────────────────────
CREATE TABLE transactions (
    id         SERIAL    PRIMARY KEY,
    product_id INT       NOT NULL UNIQUE                      -- 같은 상품 이중 거래 차단
                         REFERENCES products(id) ON DELETE RESTRICT,
    buyer_id   INT       NOT NULL
                         REFERENCES users(id) ON DELETE RESTRICT,
    price      INT       NOT NULL CHECK (price >= 0),         -- 거래 당시 가격 별도 보존
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);


-- ────────────────────────────────────────────────────────────
--  5. 더미 데이터
-- ────────────────────────────────────────────────────────────

-- 사용자 6명
INSERT INTO users (nickname) VALUES
    ('김민준'),
    ('이서연'),
    ('박지호'),
    ('최유나'),
    ('정도윤'),
    ('한소희');

-- 카테고리 5개
INSERT INTO categories (name) VALUES
    ('전자기기'),
    ('의류'),
    ('도서'),
    ('가구'),
    ('스포츠');

-- 상품 12개 (available 9개, sold 3개)
INSERT INTO products (seller_id, category_id, title, price, status) VALUES
    (1, 1, '아이폰 14 Pro 256GB',   850000, 'available'),
    (1, 1, '갤럭시 버즈2 Pro',       95000, 'available'),
    (2, 2, '나이키 에어포스 275',     65000, 'available'),
    (2, 3, '클린코드 (로버트 마틴)',   18000, 'available'),
    (3, 1, '맥북 에어 M2',          950000, 'available'),
    (3, 4, '이케아 책상 (MICKE)',     55000, 'available'),
    (4, 5, '요넥스 배드민턴 라켓',     45000, 'available'),
    (4, 2, '유니클로 후리스 L',       22000, 'available'),
    (5, 3, '파친코 (이민진)',         12000, 'available'),
    -- 이미 거래 완료된 상품
    (1, 4, '허먼밀러 의자',          450000, 'sold'),
    (3, 2, '아디다스 트레이닝복',      38000, 'sold'),
    (5, 1, '아이패드 Air 5세대',     520000, 'sold');

-- 거래 내역 3건 (sold 상품에 대응)
INSERT INTO transactions (product_id, buyer_id, price) VALUES
    (10, 3, 450000),   -- 허먼밀러 의자:      김민준 → 박지호
    (11, 6, 38000),    -- 아디다스 트레이닝복: 박지호 → 한소희
    (12, 2, 520000);   -- 아이패드 Air 5세대: 정도윤 → 이서연
