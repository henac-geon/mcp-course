import asyncio
import os
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main():
    """MCP 서버 연결 및 기본 작업"""
    
    server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8003/mcp")
    print(f"서버 연결 중: {server_url}")
    
    try:
        # HTTP 연결 생성
        async with streamablehttp_client(url=server_url) as (read, write, _):
            # 클라이언트 세션 생성
            async with ClientSession(read, write) as session:
                # 1. 초기화
                await session.initialize()
                print("✓ 서버 연결 성공\n")
                
                # 2. Tool 목록 조회
                print("=" * 50)
                print("사용 가능한 Tools:")
                print("=" * 50)
                
                tools_result = await session.list_tools()
                
                for tool in tools_result.tools:
                    print(f"\n[{tool.name}]")
                    print(f"  설명: {tool.description}")
                    if tool.inputSchema.get("properties"):
                        print(f"  파라미터:")
                        for param, info in tool.inputSchema["properties"].items():
                            desc = info.get("description", "")
                            print(f"    - {param}: {desc}")
                
                # 3. Tool 호출 예시
                print("\n" + "=" * 50)
                print("Tool 호출 테스트:")
                print("=" * 50)
                
                # authenticate 호출
                print("\n1. authenticate 호출...")
                result = await session.call_tool(
                    "authenticate",
                    {"api_key": "admin-key-123"}
                )
                print(f"   결과: {result.content[0].text}")
                
                # get_lines 호출
                print("\n2. get_lines 호출...")
                result = await session.call_tool("get_lines", {})
                print(f"   결과: {result.content[0].text}")
                
                # get_dashboard 호출
                print("\n3. get_dashboard 호출...")
                result = await session.call_tool("get_dashboard", {})
                print(f"   결과: {result.content[0].text}")
                
    except Exception as e:
        import traceback
        traceback.print_exc()  # 상세 에러 출력
        print(f"오류 발생: {e}")


if __name__ == "__main__":
    asyncio.run(main())