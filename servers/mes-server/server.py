from fastmcp import FastMCP
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os
from datetime import date

mcp = FastMCP("MESDatabase")
DB_URL = os.environ.get("DATABASE_URL", "postgresql://mcp:mcp1234@postgres:5432/mes")


def query(sql: str, params: tuple = None) -> str:
    """쿼리 실행 후 JSON 반환"""
    try:
        with psycopg2.connect(DB_URL) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params)
                if cur.description:  # SELECT
                    return json.dumps(cur.fetchall(), default=str, ensure_ascii=False)
                conn.commit()  # INSERT/UPDATE
                return json.dumps({"success": True, "affected": cur.rowcount})
    except Exception as e:
        return json.dumps({"error": str(e)})


# 라인 조회
@mcp.tool
def get_lines(status: str = None) -> str:
    """
    생산 라인 목록 조회
    
    Args:
        status: 상태 필터 (running, stopped, maintenance). 미지정 시 전체.
    
    Returns:
        라인 목록 (line_id, line_name, status)
    """
    if status:
        return query("SELECT * FROM production_lines WHERE status = %s", (status,))
    return query("SELECT * FROM production_lines")


# 제품 조회
@mcp.tool
def get_products() -> str:
    """
    제품 목록 조회
    
    Returns:
        제품 목록 (product_id, product_name, unit_price)
    """
    return query("SELECT * FROM products")


# 일일 실적
@mcp.tool
def get_daily_production(target_date: str = None) -> str:
    """
    일일 생산 실적 조회
    
    Args:
        target_date: 조회 날짜 (YYYY-MM-DD). 미지정 시 오늘.
    
    Returns:
        라인별 생산 실적 및 달성률
    """
    if not target_date:
        target_date = date.today().isoformat()
    return query("""
        SELECT r.line_id, r.product_id, r.target_qty, r.produced_qty, r.defect_qty,
               ROUND(r.produced_qty * 100.0 / r.target_qty, 1) as achievement
        FROM production_records r
        WHERE r.production_date = %s
    """, (target_date,))


# 실적 요약
@mcp.tool
def get_production_summary(days: int = 7) -> str:
    """
    기간별 라인 실적 요약 조회
    
    Args:
        days: 조회 기간 (일). 기본값 7일.
    
    Returns:
        라인별 총생산, 총불량, 불량률
    """
    return query("""
        SELECT line_id, SUM(produced_qty) as total_produced, SUM(defect_qty) as total_defects,
               ROUND(SUM(defect_qty) * 100.0 / SUM(produced_qty), 2) as defect_rate
        FROM production_records
        WHERE production_date >= CURRENT_DATE - %s
        GROUP BY line_id
    """, (days,))


# 불량 내역
@mcp.tool
def get_defects(line_id: str = None) -> str:
    """
    불량 상세 내역 조회
    
    Args:
        line_id: 라인 ID 필터. 미지정 시 전체 요약.
    
    Returns:
        불량 유형별 내역
    """
    if line_id:
        return query("""
            SELECT r.line_id, r.production_date, q.defect_type, q.defect_count
            FROM quality_inspections q
            JOIN production_records r ON q.record_id = r.record_id
            WHERE r.line_id = %s
        """, (line_id,))
    return query("""
        SELECT r.line_id, q.defect_type, SUM(q.defect_count) as total
        FROM quality_inspections q
        JOIN production_records r ON q.record_id = r.record_id
        GROUP BY r.line_id, q.defect_type
    """)


# 실적 등록
@mcp.tool
def add_production(line_id: str, product_id: str, target_qty: int, produced_qty: int, defect_qty: int = 0) -> str:
    """
    생산 실적 등록
    
    Args:
        line_id: 라인 ID (예: LINE-01)
        product_id: 제품 ID (예: PROD-A)
        target_qty: 목표 수량
        produced_qty: 생산 수량
        defect_qty: 불량 수량. 기본값 0.
    
    Returns:
        등록 결과
    """
    return query("""
        INSERT INTO production_records (line_id, product_id, target_qty, produced_qty, defect_qty)
        VALUES (%s, %s, %s, %s, %s)
    """, (line_id, product_id, target_qty, produced_qty, defect_qty))


# 대시보드
@mcp.tool
def get_dashboard() -> str:
    """
    종합 대시보드 데이터 조회
    
    Returns:
        라인 상태 요약, 오늘 실적, 불량 Top 3
    """
    try:
        with psycopg2.connect(DB_URL) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT status, COUNT(*) as cnt FROM production_lines GROUP BY status")
                lines = cur.fetchall()
                
                cur.execute("""
                    SELECT SUM(produced_qty) as produced, SUM(defect_qty) as defects
                    FROM production_records WHERE production_date = CURRENT_DATE
                """)
                today = cur.fetchone()
                
                cur.execute("""
                    SELECT defect_type, SUM(defect_count) as cnt
                    FROM quality_inspections GROUP BY defect_type
                    ORDER BY cnt DESC LIMIT 3
                """)
                defects = cur.fetchall()
                
                return json.dumps({
                    "lines": lines,
                    "today": today,
                    "top_defects": defects
                }, default=str, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8000)