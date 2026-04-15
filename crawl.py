import requests
from bs4 import BeautifulSoup
import os


def send_discord(text):
    webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
    if webhook_url:
        data = {"content": text}
        requests.post(webhook_url, json=data)
        
# 1. 모니터링할 사이트 리스트 (이름, URL, CSS 셀렉터)
# 사이트가 늘어나면 아래 리스트에 한 줄씩 추가만 하세요!
targets = [
   {
        "name": "청년안심주택", 
        "url": "https://soco.seoul.go.kr/youth/bbs/BMSR00015/list.do?menuNo=400008", 
        "selector": "#boardList > tr:nth-child(1) > td.align_left > a" 
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
            latest_title = element.text.strip()
            
            # 이전 기록과 비교
            if history.get(site["name"]) != latest_title:
                send_discord(f"🔔 [{site['name']}] 새 글 발견!\n제목: {latest_title}\n바로가기: {site['url']}")
            
            new_history.append(f"{site['name']}||{latest_title}")
        else:
            new_history.append(f"{site['name']}||{history.get(site['name'], 'N/A')}")
            
    except Exception as e:
        print(f"{site['name']} 크롤링 중 오류 발생: {e}")
        new_history.append(f"{site['name']}||{history.get(site['name'], 'N/A')}")

# 3. 새로운 기록 저장
with open(history_file, "w", encoding="utf-8") as f:
    f.write("\n".join(new_history))
