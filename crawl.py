import requests
from bs4 import BeautifulSoup
import os
import re # 정규표현식 추가


def send_discord(text):
    webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
    # 메시지가 너무 길어지는 것을 방지하기 위해 strip 적용
    if webhook_url:
        data = {"content": text.strip()}
        requests.post(webhook_url, json=data)

KEYWORDS = ["서울", "부산", "행복주택","모집"]

# 1. 모니터링할 사이트 리스트 (이름, URL, CSS 셀렉터)
# 사이트가 늘어나면 아래 리스트에 한 줄씩 추가만 하세요!
targets = [
   {
        "name": "청년안심주택", 
        "url": "https://soco.seoul.go.kr/youth/bbs/BMSR00015/list.do?menuNo=400008", 
        "selector": "#boardList tr:nth-of-type(1) td.align_left a" 
    },
   {
        "name": "LH임대주택공고", 
        "url": "https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancList.do?viewType=srch", 
        "selector": "#srchForm > section:nth-child(16) > div.bbs_ListA > table > tbody > tr:nth-child(1) > td.mVw.bbs_tit > a > span" 
    },
   {
        "name": "SH주택분양모집공", 
        "url": "https://www.i-sh.co.kr/app/lay2/program/S48T1581C1617/www/brd/m_244/list.do", 
        "selector": "#listTb > table > tbody > tr:nth-child(1) > td.txtL > a" 
    }
]

# 이전 기록 읽기 (파일이 없으면 빈 딕셔너리 생성)
history_file = "last_posts.txt"
history = {}
if os.path.exists(history_file):
    with open(history_file, "r", encoding="utf-8") as f:
        for line in f:
            if "||" in line:
                site_name, post_title = line.strip().split("||")
                history[site_name] = post_title

new_history = []

# 2. 반복문을 돌며 각 사이트 확인
for site in targets:
    try:
        response = requests.get(site["url"], timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 첫 번째 게시글 추출
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
