# 🥕 미니 당근마켓

PostgreSQL + FastAPI + 바닐라 JS 로 구현한 미니 중고 거래 플랫폼입니다.

---

## 프로젝트 구조

```
FINAL_PROJECTS/
├── main.py           # FastAPI 백엔드 (API 라우트)
├── database.py       # PostgreSQL 연결 관리
├── models.py         # 요청/응답 데이터 스키마
├── schema.sql        # 테이블 생성 + 더미 데이터
├── queries.sql       # 핵심 쿼리 + 트랜잭션 SQL
├── requirements.txt  # 패키지 목록
└── static/
    └── index.html    # 프론트엔드 (바닐라 HTML/JS)
```

---

## 서버 켜는 방법

### 1. PostgreSQL 시작
```bash
brew services start postgresql@18
```

### 2. 서버 실행
```bash
cd ~/DB_class/FINAL_PROJECTS
uvicorn main:app --reload
```

### 3. 브라우저 접속
```
http://localhost:8000        ← 프론트엔드
http://localhost:8000/docs   ← API 문서 (자동 생성)
```

---

## 서버 끄는 방법

### 서버 종료
터미널에서 `Ctrl + C`

### PostgreSQL 종료 (선택)
```bash
brew services stop postgresql@18
```

---

## 처음 세팅할 때만 (최초 1회)

```bash
# 패키지 설치
pip install -r requirements.txt

# DB 생성
psql postgres
CREATE DATABASE carrot_db;
\q

# 테이블 + 더미 데이터 적용
psql -d carrot_db -f schema.sql
```

---

## 주요 기능

| 탭 | 기능 |
|---|---|
| 상품 목록 | 카테고리·가격·제목·판매자 필터 검색 |
| 상품 등록 | 판매자·카테고리·제목·가격 입력 후 등록 |
| 거래 내역 | 전체 거래 내역 조회 |
| 통계 | 카테고리별·판매자별 통계, 평균 초과 상품 |

---

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/products` | 상품 목록 + 필터 |
| POST | `/products` | 상품 등록 |
| GET | `/products/{id}` | 상품 단건 조회 |
| PATCH | `/products/{id}/status` | 상품 상태 변경 |
| POST | `/products/{id}/purchase` | 구매 처리 (트랜잭션) |
| GET | `/transactions` | 거래 내역 조회 |
| GET | `/stats/categories` | 카테고리별 통계 |
| GET | `/stats/sellers` | 판매자별 통계 |
| GET | `/stats/expensive` | 평균 초과 상품 |
| GET | `/categories` | 카테고리 목록 |
| POST | `/users` | 사용자 등록 |
| GET | `/users` | 사용자 목록 |

---

## 기술 스택

| 구분 | 기술 |
|---|---|
| DB | PostgreSQL 18 |
| 백엔드 | Python 3.13 + FastAPI |
| DB 드라이버 | psycopg2-binary |
| 프론트엔드 | HTML + 바닐라 JS |

---

## DB 스키마 요약

```
users        사용자 (id, nickname, created_at)
categories   카테고리 (id, name)
products     상품 (id, seller_id, category_id, title, price, status, created_at)
transactions 거래 내역 (id, product_id, buyer_id, price, created_at)
```

관계: users → products → transactions, categories → products
