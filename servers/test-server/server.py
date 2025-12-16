from fastmcp import FastMCP
import sys
import os
from datetime import datetime

# MCP 서버 인스턴스 생성
mcp = FastMCP("TestServer")

# 함수를 MCP 도구로 등록하는 데코레이터
@mcp.tool
def hello_mcp() -> str:
    """
    MCP 연결 테스트를 위한 간단한 도구입니다.
    환경이 정상적으로 구성되었는지 확인할 때 사용합니다.
    
    Returns:
        환영 메시지와 현재 시간
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"MCP 서버가 정상 작동 중입니다! (서버 시간: {current_time})"


@mcp.tool
def add_numbers(a: int, b: int) -> int:
    """
    두 숫자를 더합니다.
    파라미터 전달이 정상적으로 작동하는지 테스트합니다.
    
    Args:
        a: 첫 번째 정수
        b: 두 번째 정수
    
    Returns:
        두 숫자의 합
    """
    return a + b


@mcp.tool
def get_system_info() -> dict:
    """
    서버의 시스템 정보를 반환합니다.
    복잡한 데이터 타입(dict) 반환을 테스트합니다.
    
    Returns:
        Python 버전, 실행 환경 등의 시스템 정보
    """
    return {
        "python_version": sys.version,
        "platform": sys.platform,
        "working_directory": os.getcwd(),
        "environment": "docker" if os.path.exists("/.dockerenv") else "local",
        "server_name": "TestServer",
        "transport": "HTTP (SSE)",
        "status": "operational"
    }


@mcp.tool
def echo_message(message: str, uppercase: bool = False) -> str:
    """
    입력받은 메시지를 그대로 반환합니다.
    선택적 파라미터(기본값이 있는 파라미터) 테스트용입니다.
    
    Args:
        message: 반환할 메시지
        uppercase: True이면 대문자로 변환 (기본값: False)
    
    Returns:
        입력 메시지 (또는 대문자 변환된 메시지)
    """
    if uppercase:
        return message.upper()
    return message

if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8000)