import cloudscraper  # requests 대신 cloudscraper 사용
from bs4 import BeautifulSoup
import os
import re # 정규표현식 추가
import csv


def send_discord(text):
    webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
    # 메시지가 너무 길어지는 것을 방지하기 위해 strip 적용
    if webhook_url:
        data = {"content": text.strip()}
        requests.post(webhook_url, json=data)


# 1. 키워드 파일(keywords.txt) 읽기
KEYWORDS = []
if os.path.exists('keywords.txt'):
    with open('keywords.txt', 'r', encoding='utf-8') as f:
        KEYWORDS = [line.strip() for line in f if line.strip()]
else:
    # 파일이 없을 경우 대비한 기본값
    KEYWORDS = [" "]


# 2. 타겟 파일(targets.csv) 읽기
targets = []
try:
    with open('targets.csv', mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            targets.append(row)
except Exception as e:
    print(f"CSV 읽기 에러: {e}")


# 3. 이전 기록 읽기 (파일이 없으면 빈 딕셔너리 생성)
history_file = "last_posts.txt"
history = {}
if os.path.exists(history_file):
    with open(history_file, "r", encoding="utf-8") as f:
        for line in f:
            if "||" in line:
                parts = line.strip().split("||")
                if len(parts) == 2:
                    history[parts[0]] = parts[1]

new_history = []

# 크롤러 객체 생성
scraper = cloudscraper.create_scraper()

# crawl.py 수정 스니펫
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

        
# 4. 크롤링 시작
for site in targets:
    try:
        # 1. 청년안심주택 전용 API 로직
        if site["name"] == "청년안심주택":
            api_url = "https://soco.seoul.go.kr/youth/bbs/BMSR00015/list.do"
            params = {"menuNo": "400008"}
            response = scraper.post(api_url, data=params, timeout=20)
        
        # 2. 나머지 사이트 일반 크롤링 로직
        else:
            # scraper.get을 사용하면 보안 차단을 더 잘 우회합니다.
            # response = scraper.get(site["url"], timeout=20)
            # headers를 추가해서 사람인 척 접속합니다.
            response = requests.get(site["url"], headers=headers, timeout=15)

        # 3. 공통 데이터 추출 (BeautifulSoup)
        soup = BeautifulSoup(response.text, 'html.parser')
        element = soup.select_one(site["selector"])
        
        if element:
            # [수정 포인트] 모든 줄바꿈(\n), 탭(\t), 연속된 공백을 단일 공백으로 치환하고 앞뒤 공백 제거
            raw_title = element.get_text(separator=" ", strip=True)
            latest_title = " ".join(raw_title.split())
            # 비교 시에도 양쪽 공백 제거 후 비교
            prev_title = history.get(site["name"], "").strip()
            
            if history.get(site["name"], "").strip() != latest_title:
                # [중요] 서울 또는 부산 키워드가 있을 때만 디스코드로 발송
                if any(kw in latest_title for kw in KEYWORDS):
                    send_discord(f"🔔 **[{site['name']}]** 맞춤 공고 발견!\n제목: {latest_title}\n링크: {site['url']}")
                else:
                    print(f"필터링됨 (키워드 없음): {latest_title}")
                    
            new_history.append(f"{site['name']}||{latest_title}")
        else:
            new_history.append(f"{site['name']}||{history.get(site['name'], 'N/A')}")
    except Exception as e:
        print(f"{site['name']} 크롤링 중 오류 발생: {e}")
        new_history.append(f"{site['name']}||{history.get(site['name'], 'N/A')}")

# 3. 새로운 기록 저장
with open(history_file, "w", encoding="utf-8") as f:
    f.write("\n".join(new_history))
