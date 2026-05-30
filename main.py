"""
main.py — 미니 중고 거래 플랫폼 FastAPI 백엔드

실행:
    uvicorn main:app --reload

API 문서:
    http://localhost:8000/docs
"""

import psycopg2
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Optional

from database import get_cursor
from models import (
    ProductCreate, ProductResponse, StatusUpdate,
    UserCreate, UserResponse,
    CategoryResponse,
    PurchaseRequest, PurchaseResponse,
    TransactionResponse,
    CategoryStat, SellerStat,
    ExpensiveProduct,
)

app = FastAPI(
    title="미니 중고 거래 플랫폼",
    description="PostgreSQL + FastAPI 로 구현한 미니 당근마켓",
    version="1.0.0",
)

# ── CORS ─────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ════════════════════════════════════════════════════════════
#  사용자
# ════════════════════════════════════════════════════════════

@app.post("/users", response_model=UserResponse, tags=["users"])
def create_user(body: UserCreate):
    """사용자 등록"""
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (nickname)
                VALUES (%s)
                RETURNING id, nickname, created_at
                """,
                (body.nickname,),
            )
            return cur.fetchone()
    except psycopg2.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="이미 사용 중인 닉네임입니다")
    except Exception:
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다")


@app.get("/users", response_model=list[UserResponse], tags=["users"])
def list_users():
    """사용자 전체 목록 (프론트엔드 셀렉트박스용)"""
    try:
        with get_cursor() as cur:
            cur.execute("SELECT id, nickname, created_at FROM users ORDER BY id")
            return cur.fetchall()
    except Exception:
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다")


# ════════════════════════════════════════════════════════════
#  카테고리
# ════════════════════════════════════════════════════════════

@app.get("/categories", response_model=list[CategoryResponse], tags=["categories"])
def list_categories():
    """카테고리 전체 목록"""
    try:
        with get_cursor() as cur:
            cur.execute("SELECT id, name FROM categories ORDER BY id")
            return cur.fetchall()
    except Exception:
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다")


# ════════════════════════════════════════════════════════════
#  상품 — Q1 JOIN 쿼리
# ════════════════════════════════════════════════════════════

@app.get("/products", response_model=list[ProductResponse], tags=["products"])
def list_products(
    category:  Optional[str] = Query(None, description="카테고리 이름"),
    min_price: Optional[int] = Query(None, ge=0, description="최소 가격"),
    max_price: Optional[int] = Query(None, ge=0, description="최대 가격"),
    seller:    Optional[str] = Query(None, description="판매자 닉네임"),
    keyword:   Optional[str] = Query(None, description="제목 검색 키워드"),
    status:    str           = Query("available", description="available / sold / all"),
):
    """
    상품 목록 조회 (Q1 — JOIN + 동적 필터)

    - category, min_price, max_price, seller, keyword 자유롭게 조합
    - status=all 이면 sold 포함 전체 조회
    """
    sql = """
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
        WHERE 1=1
    """
    params = []

    if status != "all":
        sql += " AND p.status = %s"
        params.append(status)
    if category:
        sql += " AND c.name = %s"
        params.append(category)
    if min_price is not None:
        sql += " AND p.price >= %s"
        params.append(min_price)
    if max_price is not None:
        sql += " AND p.price <= %s"
        params.append(max_price)
    if seller:
        sql += " AND u.nickname = %s"
        params.append(seller)
    if keyword:
        sql += " AND p.title LIKE %s"
        params.append(f"%{keyword}%")

    sql += " ORDER BY p.created_at DESC"

    try:
        with get_cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    except Exception:
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다")


@app.get("/products/{product_id}", response_model=ProductResponse, tags=["products"])
def get_product(product_id: int):
    """상품 단건 조회"""
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT
                    p.id, p.title, p.price, p.status,
                    c.name     AS category,
                    u.nickname AS seller,
                    p.created_at
                FROM products p
                JOIN users      u ON p.seller_id   = u.id
                JOIN categories c ON p.category_id = c.id
                WHERE p.id = %s
                """,
                (product_id,),
            )
            row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")
        return row
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다")


@app.post("/products", response_model=ProductResponse, tags=["products"])
def create_product(body: ProductCreate):
    """상품 등록"""
    try:
        with get_cursor() as cur:
            # seller, category 존재 여부 확인
            cur.execute("SELECT id FROM users WHERE id = %s", (body.seller_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="존재하지 않는 판매자입니다")

            cur.execute("SELECT id FROM categories WHERE id = %s", (body.category_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="존재하지 않는 카테고리입니다")

            cur.execute(
                """
                INSERT INTO products (seller_id, category_id, title, price)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (body.seller_id, body.category_id, body.title, body.price),
            )
            new_id = cur.fetchone()["id"]

            cur.execute(
                """
                SELECT
                    p.id, p.title, p.price, p.status,
                    c.name     AS category,
                    u.nickname AS seller,
                    p.created_at
                FROM products p
                JOIN users      u ON p.seller_id   = u.id
                JOIN categories c ON p.category_id = c.id
                WHERE p.id = %s
                """,
                (new_id,),
            )
            return cur.fetchone()
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다")


@app.patch("/products/{product_id}/status", response_model=ProductResponse, tags=["products"])
def update_product_status(product_id: int, body: StatusUpdate):
    """
    상품 상태 변경 (판매자가 직접 available ↔ sold 변경)
    """
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                UPDATE products
                SET    status = %s
                WHERE  id     = %s
                """,
                (body.status, product_id),
            )
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")

            cur.execute(
                """
                SELECT
                    p.id, p.title, p.price, p.status,
                    c.name     AS category,
                    u.nickname AS seller,
                    p.created_at
                FROM products p
                JOIN users      u ON p.seller_id   = u.id
                JOIN categories c ON p.category_id = c.id
                WHERE p.id = %s
                """,
                (product_id,),
            )
            return cur.fetchone()
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다")


# ════════════════════════════════════════════════════════════
#  구매 처리 — T1 트랜잭션
# ════════════════════════════════════════════════════════════

@app.post(
    "/products/{product_id}/purchase",
    response_model=PurchaseResponse,
    tags=["purchase"],
)
def purchase_product(product_id: int, body: PurchaseRequest):
    """
    상품 구매 처리 (T1 — 트랜잭션)

    1. FOR UPDATE 로 행 잠금 (동시 구매 방지)
    2. status = 'available' 인 경우에만 UPDATE → 0행이면 409
    3. transactions 에 거래 내역 INSERT
    → UPDATE 와 INSERT 가 반드시 함께 성공하거나 함께 실패 (원자성)
    """
    try:
        with get_cursor() as cur:
            # ① 상품 조회 + 행 잠금
            cur.execute(
                "SELECT id, price, status, seller_id FROM products WHERE id = %s FOR UPDATE",
                (product_id,),
            )
            product = cur.fetchone()
            if not product:
                raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")

            # ② 구매자 존재 여부 확인
            cur.execute("SELECT id FROM users WHERE id = %s", (body.buyer_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="존재하지 않는 구매자입니다")

            # ③ 본인 상품 구매 방지
            if product["seller_id"] == body.buyer_id:
                raise HTTPException(status_code=400, detail="본인 상품은 구매할 수 없습니다")

            # ④ 상태 변경 (available 인 경우에만)
            cur.execute(
                """
                UPDATE products
                SET    status = 'sold'
                WHERE  id     = %s
                  AND  status = 'available'
                """,
                (product_id,),
            )
            if cur.rowcount == 0:
                raise HTTPException(status_code=409, detail="이미 판매된 상품입니다")

            # ⑤ 거래 내역 INSERT
            cur.execute(
                """
                INSERT INTO transactions (product_id, buyer_id, price)
                VALUES (%s, %s, %s)
                RETURNING id AS transaction_id, product_id, buyer_id, price, created_at
                """,
                (product_id, body.buyer_id, product["price"]),
            )
            return cur.fetchone()

    except HTTPException:
        raise
    except psycopg2.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="이미 거래된 상품입니다")
    except Exception:
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다")


# ════════════════════════════════════════════════════════════
#  거래 내역 — Q4
# ════════════════════════════════════════════════════════════

@app.get("/transactions", response_model=list[TransactionResponse], tags=["transactions"])
def list_transactions():
    """거래 내역 전체 조회 (Q4 — JOIN)"""
    try:
        with get_cursor() as cur:
            cur.execute(
                """
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
                ORDER BY t.created_at DESC
                """
            )
            return cur.fetchall()
    except Exception:
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다")


# ════════════════════════════════════════════════════════════
#  통계 — Q2 GROUP BY / Q3 서브쿼리
# ════════════════════════════════════════════════════════════

@app.get("/stats/categories", response_model=list[CategoryStat], tags=["stats"])
def category_stats():
    """카테고리별 상품 통계 (Q2-1 — GROUP BY)"""
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT
                    c.name                   AS category,
                    COUNT(p.id)              AS total_count,
                    ROUND(AVG(p.price))::INT AS avg_price,
                    MIN(p.price)             AS min_price,
                    MAX(p.price)             AS max_price
                FROM categories c
                LEFT JOIN products p ON c.id = p.category_id
                GROUP BY c.id, c.name
                ORDER BY total_count DESC
                """
            )
            return cur.fetchall()
    except Exception:
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다")


@app.get("/stats/sellers", response_model=list[SellerStat], tags=["stats"])
def seller_stats():
    """판매자별 등록·판매 통계 (Q2-3 — GROUP BY + CASE WHEN)"""
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT
                    u.nickname                                         AS seller,
                    COUNT(p.id)                                        AS total_listed,
                    COUNT(CASE WHEN p.status = 'sold'      THEN 1 END) AS sold_count,
                    COUNT(CASE WHEN p.status = 'available' THEN 1 END) AS available_count
                FROM users u
                LEFT JOIN products p ON u.id = p.seller_id
                GROUP BY u.id, u.nickname
                ORDER BY total_listed DESC
                """
            )
            return cur.fetchall()
    except Exception:
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다")


@app.get("/stats/expensive", response_model=list[ExpensiveProduct], tags=["stats"])
def expensive_products():
    """카테고리 평균보다 비싼 상품 (Q3-1 — CTE + 서브쿼리)"""
    try:
        with get_cursor() as cur:
            cur.execute(
                """
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
                    c.name                 AS category,
                    u.nickname             AS seller,
                    ca.avg_price           AS category_avg,
                    p.price - ca.avg_price AS diff_from_avg
                FROM products p
                JOIN users        u  ON p.seller_id   = u.id
                JOIN categories   c  ON p.category_id = c.id
                JOIN category_avg ca ON p.category_id = ca.category_id
                WHERE p.status = 'available'
                  AND p.price  > ca.avg_price
                ORDER BY c.name, p.price DESC
                """
            )
            return cur.fetchall()
    except Exception:
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다")

# ── 정적 파일 서빙 ─────────────────────────────────────────────
# API 라우트보다 반드시 뒤에 선언해야 함
# http://localhost:8000 → static/index.html
app.mount("/", StaticFiles(directory="static", html=True), name="static")
