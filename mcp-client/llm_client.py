"""
llm_client.py - OpenAI API + MCP 통합 클라이언트
"""
import asyncio
import json
import os
from dotenv import load_dotenv
from openai import OpenAI
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

load_dotenv()


async def main():
    server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8003/mcp")
    print(f"MCP 서버 연결 중: {server_url}")
    
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    conversation_history = []
    
    try:
        async with streamablehttp_client(url=server_url) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                print("✓ MCP 서버 연결 성공")
                
                # Tool 목록 로드
                tools_result = await session.list_tools()
                tools = []
                for tool in tools_result.tools:
                    tools.append({
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.inputSchema
                        }
                    })
                print(f"✓ {len(tools)}개 Tool 로드 완료\n")
                
                print("=" * 60)
                print("MES AI 어시스턴트 (OpenAI)")
                print("=" * 60)
                print("자연어로 질문하세요. 종료: 'quit', 초기화: 'clear'")
                print("=" * 60)
                
                system_message = {
                    "role": "system",
                    "content": """당신은 MES(제조실행시스템) 어시스턴트입니다.
사용자의 질문에 답하기 위해 제공된 도구를 사용하세요.

중요: 데이터를 조회하려면 먼저 authenticate 도구로 인증해야 합니다.
- 관리자: api_key="admin-key-123"
- 조회자: api_key="viewer-key-456"

인증 후 필요한 도구를 사용하여 정보를 조회하고 답변하세요."""
                }
                
                while True:
                    try:
                        user_input = input("\n사용자: ").strip()
                        
                        if not user_input:
                            continue
                        
                        if user_input.lower() == 'quit':
                            break
                        
                        if user_input.lower() == 'clear':
                            conversation_history = []
                            print("대화 기록이 초기화되었습니다.")
                            continue
                        
                        print("\n처리 중...")
                        
                        # 사용자 메시지 추가
                        conversation_history.append({
                            "role": "user",
                            "content": user_input
                        })
                        
                        messages = [system_message] + conversation_history
                        
                        # OpenAI API 호출
                        response = openai_client.chat.completions.create(
                            model="gpt-4o",
                            messages=messages,
                            tools=tools if tools else None
                        )
                        
                        # Tool 사용 루프
                        while response.choices[0].finish_reason == "tool_calls":
                            assistant_message = response.choices[0].message
                            
                            conversation_history.append({
                                "role": "assistant",
                                "content": assistant_message.content,
                                "tool_calls": [
                                    {
                                        "id": tc.id,
                                        "type": "function",
                                        "function": {
                                            "name": tc.function.name,
                                            "arguments": tc.function.arguments
                                        }
                                    }
                                    for tc in assistant_message.tool_calls
                                ]
                            })
                            
                            for tool_call in assistant_message.tool_calls:
                                tool_name = tool_call.function.name
                                tool_input = json.loads(tool_call.function.arguments)
                                
                                print(f"  [Tool 호출] {tool_name}({tool_input})")
                                
                                # MCP Tool 실행
                                result = await session.call_tool(tool_name, tool_input)
                                tool_result = result.content[0].text
                                
                                conversation_history.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "content": tool_result
                                })
                            
                            messages = [system_message] + conversation_history
                            response = openai_client.chat.completions.create(
                                model="gpt-4o",
                                messages=messages,
                                tools=tools if tools else None
                            )
                        
                        # 최종 응답
                        final_response = response.choices[0].message.content or ""
                        conversation_history.append({
                            "role": "assistant",
                            "content": final_response
                        })
                        
                        print(f"\n어시스턴트: {final_response}")
                        
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