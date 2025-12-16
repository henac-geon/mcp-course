from fastmcp import FastMCP
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# 서버 인스턴스 생성
mcp = FastMCP("ResourceServer")

# 데이터 디렉토리 경로
DATA_DIR = Path(__file__).parent / "data"


@mcp.resource("config://app/settings")
def get_app_settings() -> str:
    """애플리케이션 설정 정보를 반환합니다."""
    config_path = DATA_DIR / "config.json"
    if config_path.exists():
        return config_path.read_text(encoding="utf-8")
    return json.dumps({"error": "Config file not found"})


@mcp.resource("logs://app/current")
def get_current_logs() -> str:
    """현재 애플리케이션 로그를 반환합니다."""
    log_path = DATA_DIR / "logs" / "app.log"
    if log_path.exists():
        return log_path.read_text(encoding="utf-8")
    return "No logs available"


@mcp.resource("logs://level/{level}")
def get_logs_by_level(level: str) -> str:
    """특정 로그 레벨만 필터링하여 반환합니다. (동적 Resource 예시)"""
    log_path = DATA_DIR / "logs" / "app.log"
    level = level.upper()
    if log_path.exists():
        lines = log_path.read_text(encoding="utf-8").splitlines()
        filtered = [line for line in lines if level in line]
        return "\n".join(filtered) if filtered else f"No {level} logs found"
    return "No logs available"

@mcp.prompt()
def code_review(language: str, code: str) -> str:
    """코드 리뷰를 요청합니다."""
    return f"""
        다음 {language} 코드를 리뷰해주세요.
        분석 항목: 코드 품질, 버그 가능성, 개선점
        ````
            {language}
            {code}
        ```
    """
			

@mcp.prompt()
def daily_report(date: str, line_id: str) -> str:
    """일일 생산 보고서 작성을 요청합니다."""
    return f"""
        다음 조건으로 일일 생산 보고서를 작성해주세요.
        날짜: {date}
        생산라인: {line_id}
        포함 항목: 생산 실적, 품질 현황, 특이사항
    """


if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8000)