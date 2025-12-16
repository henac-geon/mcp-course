"""
FastAPI + MCP 통합 서버

REST API와 MCP 동시 제공
- REST API: http://localhost:8000/api/...
- MCP: http://localhost:8000/mcp/sse
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import date
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os

# ============================================================
# 설정
# ============================================================

app = FastAPI(
    title="MES API + MCP",
    description="REST API와 MCP를 동시에 제공하는 통합 서버",
    version="1.0.0"
)

DB_URL = os.environ.get("DATABASE_URL", "postgresql://mcp:mcp1234@postgres:5432/mes")

# ============================================================
# Pydantic 모델
# ============================================================

class ProductionCreate(BaseModel):
    """생산 실적 등록 요청"""
    line_id: str
    product_id: str
    target_qty: int
    produced_qty: int
    defect_qty: int = 0


# ============================================================
# 공통 함수 (REST API와 MCP Tool이 공유)
# ============================================================

def db_query(sql: str, params: tuple = None, fetch: bool = True):
    """쿼리 실행 후 JSON 반환"""
    with psycopg2.connect(DB_URL) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            if fetch:
                return cur.fetchall()
            conn.commit()
            return cur.rowcount


def get_lines_data(status: str = None) -> list:
    """라인 데이터 조회 (공통)"""
    if status:
        return db_query(
            "SELECT * FROM production_lines WHERE status = %s ORDER BY line_id",
            (status,)
        )
    return db_query("SELECT * FROM production_lines ORDER BY line_id")


def get_products_data() -> list:
    """제품 데이터 조회 (공통)"""
    return db_query("SELECT * FROM products ORDER BY product_id")


def get_production_data(target_date: str = None, line_id: str = None) -> list:
    """생산 실적 조회 (공통)"""
    if not target_date:
        target_date = date.today().isoformat()
    
    sql = """
        SELECT r.line_id, r.product_id, r.production_date,
               r.target_qty, r.produced_qty, r.defect_qty,
               ROUND(r.produced_qty * 100.0 / r.target_qty, 1) as achievement
        FROM production_records r
        WHERE r.production_date = %s
    """
    params = [target_date]
    
    if line_id:
        sql += " AND r.line_id = %s"
        params.append(line_id)
    
    return db_query(sql, tuple(params))


def get_dashboard_data() -> dict:
    """대시보드 데이터 조회 (공통)"""
    lines = db_query(
        "SELECT status, COUNT(*) as cnt FROM production_lines GROUP BY status"
    )
    today = db_query("""
        SELECT COALESCE(SUM(produced_qty), 0) as produced,
               COALESCE(SUM(defect_qty), 0) as defects
        FROM production_records 
        WHERE production_date = CURRENT_DATE
    """)
    defects = db_query("""
        SELECT defect_type, SUM(defect_count) as cnt
        FROM quality_inspections 
        GROUP BY defect_type
        ORDER BY cnt DESC LIMIT 3
    """)
    
    return {
        "lines": lines,
        "today": today[0] if today else {},
        "top_defects": defects
    }


def add_production_data(line_id: str, product_id: str, 
                        target_qty: int, produced_qty: int, defect_qty: int) -> bool:
    """생산 실적 등록 (공통)"""
    db_query("""
        INSERT INTO production_records 
        (line_id, product_id, target_qty, produced_qty, defect_qty)
        VALUES (%s, %s, %s, %s, %s)
    """, (line_id, product_id, target_qty, produced_qty, defect_qty), fetch=False)
    return True


# ============================================================
# REST API 엔드포인트
# ============================================================

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "MES API + MCP",
        "endpoints": {
            "rest_api": "/api/...",
            "swagger": "/docs",
            "mcp": "/mcp/sse"
        }
    }


@app.get("/api/lines")
def api_get_lines(status: Optional[str] = None):
    """라인 목록 조회"""
    data = get_lines_data(status)
    return {"data": data, "count": len(data)}


@app.get("/api/products")
def api_get_products():
    """제품 목록 조회"""
    data = get_products_data()
    return {"data": data, "count": len(data)}


@app.get("/api/production")
def api_get_production(target_date: Optional[str] = None, line_id: Optional[str] = None):
    """생산 실적 조회"""
    data = get_production_data(target_date, line_id)
    return {"data": data, "count": len(data)}


@app.post("/api/production")
def api_create_production(body: ProductionCreate):
    """생산 실적 등록"""
    add_production_data(
        body.line_id, body.product_id,
        body.target_qty, body.produced_qty, body.defect_qty
    )
    return {"success": True}


@app.get("/api/dashboard")
def api_get_dashboard():
    """대시보드"""
    return get_dashboard_data()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)