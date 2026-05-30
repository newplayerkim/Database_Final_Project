"""
models.py — 요청(Request) / 응답(Response) 스키마

Pydantic v2 BaseModel 을 상속해서 정의.
FastAPI 가 자동으로 JSON 직렬화·검증에 사용함.
"""

from pydantic import BaseModel, Field
from datetime import datetime


# ── 공통 config ───────────────────────────────────────────────
class Base(BaseModel):
    model_config = {"from_attributes": True}


# ── 사용자 ────────────────────────────────────────────────────

class UserCreate(Base):
    """POST /users — 사용자 등록 요청"""
    nickname: str = Field(min_length=1, max_length=50)


class UserResponse(Base):
    """사용자 조회 응답"""
    id:         int
    nickname:   str
    created_at: datetime


# ── 카테고리 ──────────────────────────────────────────────────

class CategoryResponse(Base):
    """카테고리 조회 응답"""
    id:   int
    name: str


# ── 상품 ─────────────────────────────────────────────────────

class ProductCreate(Base):
    """POST /products — 상품 등록 요청"""
    seller_id:   int
    category_id: int
    title:       str = Field(min_length=1, max_length=100)
    price:       int = Field(ge=0)


class ProductResponse(Base):
    """상품 조회 응답"""
    id:          int
    title:       str
    price:       int
    status:      str
    category:    str       # categories.name
    seller:      str       # users.nickname
    created_at:  datetime


class StatusUpdate(Base):
    """PATCH /products/{id}/status — 상태 변경 요청"""
    status: str = Field(pattern="^(available|sold)$")


# ── 구매 처리 ─────────────────────────────────────────────────

class PurchaseRequest(Base):
    """POST /products/{product_id}/purchase — 구매 요청"""
    buyer_id: int


class PurchaseResponse(Base):
    """구매 완료 응답"""
    transaction_id: int
    product_id:     int
    buyer_id:       int
    price:          int
    created_at:     datetime


# ── 거래 내역 ─────────────────────────────────────────────────

class TransactionResponse(Base):
    """거래 내역 조회 응답"""
    transaction_id: int
    title:          str
    seller:         str
    buyer:          str
    price:          int
    created_at:     datetime


# ── 통계 ─────────────────────────────────────────────────────

class CategoryStat(Base):
    """Q2-1 — 카테고리별 통계 응답"""
    category:    str
    total_count: int
    avg_price:   int
    min_price:   int
    max_price:   int


class SellerStat(Base):
    """Q2-3 — 판매자별 통계 응답"""
    seller:          str
    total_listed:    int
    sold_count:      int
    available_count: int


class ExpensiveProduct(Base):
    """Q3-1 — 카테고리 평균보다 비싼 상품 응답"""
    title:         str
    price:         int
    category:      str
    seller:        str
    category_avg:  int
    diff_from_avg: int
