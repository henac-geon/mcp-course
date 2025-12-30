import asyncio
import json
import os
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main():
    server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8003/mcp")
    print(f"서버 연결 중: {server_url}")
    
    try:
        async with streamablehttp_client(url=server_url) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                print("✓ 서버 연결 성공\n")
                
                # Tool 목록 로드
                tools_result = await session.list_tools()
                tools = {tool.name: tool for tool in tools_result.tools}
                
                print("=" * 50)
                print("MCP 대화형 클라이언트")
                print("=" * 50)
                print("명령어: tools, info <tool>, <tool> [params], quit")
                print("=" * 50)
                
                while True:
                    try:
                        user_input = input("\n> ").strip()
                        
                        if not user_input:
                            continue
                        
                        if user_input.lower() == 'quit':
                            break
                        
                        if user_input.lower() == 'tools':
                            print("\n사용 가능한 Tools:")
                            for name in tools:
                                print(f"  - {name}")
                            continue
                        
                        if user_input.lower().startswith('info '):
                            tool_name = user_input[5:].strip()
                            if tool_name in tools:
                                tool = tools[tool_name]
                                print(f"\n[{tool.name}]")
                                print(f"설명: {tool.description}")
                            else:
                                print(f"Tool을 찾을 수 없습니다: {tool_name}")
                            continue
                        
                        # Tool 호출 파싱
                        parts = user_input.split()
                        tool_name = parts[0]
                        params = {}
                        for part in parts[1:]:
                            if '=' in part:
                                key, value = part.split('=', 1)
                                try:
                                    value = int(value)
                                except ValueError:
                                    pass
                                params[key] = value
                        
                        if tool_name in tools:
                            print(f"호출: {tool_name}({params})")
                            result = await session.call_tool(tool_name, params)
                            try:
                                parsed = json.loads(result.content[0].text)
                                print(json.dumps(parsed, indent=2, ensure_ascii=False))
                            except:
                                print(result.content[0].text)
                        else:
                            print(f"Tool을 찾을 수 없습니다: {tool_name}")
                    
                    except KeyboardInterrupt:
                        print("\n")
                        break
                    except Exception as e:
                        print(f"오류: {e}")
        
        print("연결 종료됨")
        
    except Exception as e:
        print(f"연결 오류: {e}")


if __name__ == "__main__":
    asyncio.run(main())