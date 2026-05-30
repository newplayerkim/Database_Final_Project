"""
database.py — PostgreSQL 연결 관리

요청마다 새 커넥션을 열고 닫는 방식.
get_cursor() 컨텍스트 매니저를 통해 각 요청에서 사용.
"""

import os
import psycopg2
import psycopg2.extras
from contextlib import contextmanager

# ── DB 접속 정보 (환경변수 우선, 없으면 기본값) ───────────────
DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "carrot_db",
    "user":     "zzun",    # 맥 계정명
    "password": "",        # 비밀번호 없음
}


@contextmanager
def get_cursor():
    """
    요청마다 새 커넥션을 열고, 끝나면 닫음.
    RealDictCursor: 결과를 dict 형태로 반환 → JSON 변환 편리.

    - 정상 종료 → COMMIT
    - 예외 발생 → ROLLBACK

    사용법:
        with get_cursor() as cur:
            cur.execute("SELECT ...")
            rows = cur.fetchall()
    """
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
