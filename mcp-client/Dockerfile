FROM python:3.11-slim

WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 복사
COPY . .

# 기본 명령 (docker run 시 덮어쓰기 가능)
CMD ["python", "basic_client.py"]