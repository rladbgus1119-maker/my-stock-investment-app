import streamlit as st
import pandas as pd
import yfinance as yf
import time
import numpy as np
import random

# 1. 페이지 설정 및 다이내믹 테마 시스템
st.set_page_config(page_title="AI 실시간 투자 & 퀴즈 센터", layout="wide")

st.sidebar.title("🎨 시스템 설정")
theme_choice = st.sidebar.radio("배경 테마 선택", ["라이트 모드", "다크 모드"])

if theme_choice == "다크 모드":
    bg, txt, card, border = "#0e1117", "#ffffff", "#1d2026", "#3d414a"
else:
    bg, txt, card, border = "#ffffff", "#000000", "#f8fafc", "#e2e8f0"

# 강화된 CSS: 다크 모드에서도 글자가 선명하게 보이도록 설정
st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg} !important; color: {txt} !important; }}
    h1, h2, h3, h4, p, span, div, label {{ color: {txt} !important; }}
    [data-testid="stWidgetLabel"] p {{ color: {txt} !important; font-weight: bold; }}
    .stMetric {{ background-color: {card} !important; padding: 15px; border-radius: 12px; border: 1px solid {border} !important; }}
    .rank-card {{ background-color: {card} !important; border-radius: 10px; padding: 10px; border: 1px solid {border} !important; margin-bottom: 5px; }}
    .quiz-container {{ background-color: {card} !important; padding: 20px; border-radius: 12px; border: 1px solid #3b82f6 !important; margin-bottom: 15px; }}
    .item-card {{ background-color: {card} !important; padding: 15px; border-radius: 10px; border: 1px solid {border} !important; text-align: center; }}
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

# 2. 새로운 주식 데이터 세트 (전자공학 제외)
stock_map = {
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "NVIDIA": "NVDA",
    "애플": "AAPL", "테슬라": "TSLA", "마이크로소프트": "MSFT", 
    "구글": "GOOGL", "현대차": "005380.KS", "넥슨": "3659.T", "아마존": "AMZN"
}

avatar_base = {"🛡️ 든든한 가디언": "🐢", "🚀 불타는 로켓": "🚀", "⚖️ 냉철한 분석가": "💻", "🌱 투자 꿈나무": "🌱", "🐣 분석 대기 중": "🥚"}

shop_items = {
    "👑 황금 왕관": {"price": 100, "emoji": "👑"},
    "💼 비즈니스 수트": {"price": 60, "emoji": "💼"},
    "🕶️ VIP 고글": {"price": 40, "emoji": "🕶️"},
    "📱 최신형 폴더블폰": {"price": 50, "emoji": "📱"},
    "🏎️ 슈퍼카 키": {"price": 150, "emoji": "🏎️"}
}

# [신규] 순수 주식 퀴즈 세트
quiz_pool = [
    {"q": "주식 시장에서 '상승장'을 상징하는 동물은 무엇인가요?", "a": "황소(Bull)", "o": ["황소(Bull)", "곰(Bear)", "사자(Lion)"]},
    {"q": "기업의 순이익 중 일부를 주주들에게 현금으로 나누어 주는 것은?", "a": "배당금", "o": ["배당금", "이자", "상여금"]},
    {"q": "상장 주식 전체를 현재 주가로 곱한 기업의 총 가치는?", "a": "시가총액", "o": ["매출액", "영업이익", "시가총액"]},
    {"q": "주가가 급격히 하락할 때 잠시 거래를 중단시키는 제도는?", "a": "서킷브레이커", "o": ["사이드카", "서킷브레이커", "데드캣바운스"]},
    {"q": "우량주를 뜻하는 용어로, 카지노의 가장 비싼 칩 색깔에서 유래된 말은?", "a": "블루칩", "o": ["레드칩", "블루칩", "옐로우칩"]}
]

# 3. 실시간 엔진
@st.cache_data(ttl=30)
def fetch_prices():
    prices = {}
    for name, ticker in stock_map.items():
        try:
            data = yf.Ticker(ticker); p = data.history(period="1d")['Close'].iloc[-1]
            if ".KS" not in ticker: p *= 1415 # 환율
            prices[name] = int(p * (1 + (np.random.rand()-0.5)*0.006))
        except: prices[name] = 100000
    return prices

# 4. 세션 상태 초기화 (퀴즈 완료 추적 변수 포함)
if 'user_name' not in st.session_state:
    st.session_state.update({
        'user_name': "", 'difficulty': "", 'balance': 0.0, 'points': 0,
        'portfolio': {s: 0 for s in stock_map}, 'trade_count': 0, 'tech_focus': 0,
        'avatar': "🐣 분석 대기 중", 'attendance': False,
        'inventory': [], 'equipped': "", 'bots': [],
        'quiz_cleared': [False] * len(quiz_pool) # 퀴즈 완료 여부 저장
    })

def init_bots(diff):
    names = ["퀀트마스터", "익산불개미", "여의도황소", "나스닥귀신", "버핏지망생", "단타의신", "월스트리트", "AI알고리즘", "풀매수전사"]
    base = {"초급": 50000000, "중급": 10000000, "상급": 1000000}[diff]
    return [{"닉네임": n, "자산": base * (1 + (random.random()-0.5)*0.15), "성향": random.choice(list(avatar_base.keys())[:4]), "난이도": diff} for n in names]

# 5. 로그인 화면
if not st.session_state.user_name:
    st.title("📈 실시간 행동분석 투자 시뮬레이션")
    with st.container(border=True):
        name = st.text_input("닉네임 입력")
        diff_choice = st.selectbox("등급 선택", ["초급 (5,000만)", "중급 (1,000만)", "상급 (100만)"])
        if st.button("시스템 가동"):
            if name:
                st.session_state.user_name = name; d_label = diff_choice.split()[0]
                st.session_state.difficulty = d_label; st.session_state.balance = 50000000.0 if "초급" in diff_choice else 10000000.0 if "중급" in diff_choice else 1000000.0
                st.session_state.bots = init_bots(d_label); st.rerun()
    st.stop()

# 6. 행동 분석 AI
tc = st.session_state.trade_count; tf = st.session_state.tech_focus
if tc >= 10: st.session_state.avatar = "⚖️ 냉철한 분석가"
elif tf >= 5: st.session_state.avatar = "🚀 불타는 로켓"
elif tc >= 1: st.session_state.avatar = "🛡️ 든든한 가디언"
else: st.session_state.avatar = "🌱 투자 꿈나무"

prices = fetch_prices()
total_assets = st.session_state.balance + sum(st.session_state.portfolio[s] * prices[s] for s in stock_map)
full_avatar = f"{avatar_base.get(st.session_state.avatar, '🥚')} {st.session_state.equipped}"

# 상단 대시보드
st.title(f"{full_avatar} {st.session_state.user_name} 관제 센터")
st.sidebar.metric("💎 나의 포인트", f"{st.session_state.points} P")

col_h1, col_h2, col_h3 = st.columns([1.5, 1.5, 1])
col_h1.metric("💵 현금 자산", f"{st.session_state.balance:,.0f}원")
col_h2.metric("🏆 총 자산", f"{total_assets:,.0f}원")
with col_h3:
    if not st.session_state.attendance:
        if st.button("📅 출석 체크 (+5만/10P)"):
            st.session_state.attendance = True; st.session_state.balance += 50000; st.session_state.points += 10; st.rerun()
    else: st.success("✅ 오늘 출석 완료")

st.divider()

# 7. 기능 탭
tab_market, tab_shop, tab_custom, tab_quiz, tab_academy = st.tabs(["🛒 거래소 & 랭킹", "🛍️ 포인트 상점", "👗 아바타 꾸미기", "❓ 미션 & 퀴즈", "📚 투자 사전"])

# [탭 1: 거래소 & 10인 랭킹]
with tab_market:
    c_m, c_r = st.columns([1.8, 1.2])
    with c_m:
        qty = st.number_input("거래 수량 설정", min_value=1, value=1)
        st_items = list(prices.items())
        for i in range(0, len(st_items), 2):
            cols = st.columns(2)
            for j in range(2):
                if i+j < len(st_items):
                    n, p = st_items[i+j]
                    with cols[j].container(border=True):
                        st.write(f"### {n}"); st.write(f"현재가: {p:,}원 | 보유: {st.session_state.portfolio[n]}주")
                        b, s = st.columns(2)
                        if b.button(f"매수", key=f"b_{n}"):
                            if st.session_state.balance >= p * qty:
                                st.session_state.balance -= p * qty; st.session_state.portfolio[n] += qty
                                st.session_state.trade_count += 1
                                if n in ["NVIDIA", "애플", "테슬라"]: st.session_state.tech_focus += 1
                                st.rerun()
                        if s.button(f"매도", key=f"s_{n}"):
                            if st.session_state.portfolio[n] >= qty:
                                st.session_state.balance += p * qty; st.session_state.portfolio[n] -= qty
                                st.session_state.trade_count += 1; st.rerun()
    with c_r:
        st.subheader(f"🏆 {st.session_state.difficulty} 실시간 랭킹")
        user_rank = {"닉네임": f"{st.session_state.user_name} ⭐", "성향": st.session_state.avatar, "자산": total_assets}
        for bot in st.session_state.bots: bot['자산'] *= (1 + (random.random()-0.5)*0.003)
        all_players = sorted(st.session_state.bots + [user_rank], key=lambda x: x["자산"], reverse=True)
        for idx, p in enumerate(all_players):
            medal = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else f"{idx+1}위"
            st.markdown(f'<div class="rank-card">{medal} {p["닉네임"]} <br> 자산: {p["자산"]:,.0f}원</div>', unsafe_allow_html=True)
        if st.button("🔄 시세/랭킹 새로고침"): st.rerun()

# [탭 2: 포인트 상점]
with tab_shop:
    st.header("🛍️ 포인트 상점")
    i_cols = st.columns(3)
    for idx, (name, info) in enumerate(shop_items.items()):
        with i_cols[idx % 3]:
            st.markdown(f'<div class="item-card"><h2>{info["emoji"]}</h2><b>{name}</b><br>{info["price"]} P</div>', unsafe_allow_html=True)
            if name in st.session_state.inventory: st.button("보유 중", key=f"o_{name}", disabled=True)
            elif st.button(f"구매", key=f"buy_{name}"):
                if st.session_state.points >= info['price']:
                    st.session_state.points -= info['price']; st.session_state.inventory.append(name); st.rerun()
                else: st.error("포인트 부족!")

# [탭 3: 아바타 꾸미기]
with tab_custom:
    st.header("👗 나의 드레스룸")
    if not st.session_state.inventory: st.info("상점에서 아이템을 구매해 보세요!")
    else:
        for item in st.session_state.inventory:
            c_i1, c_i2 = st.columns([3, 1])
            c_i1.write(f"### {item}")
            if st.session_state.equipped == shop_items[item]['emoji']:
                if c_i2.button("해제", key=f"un_{item}"): st.session_state.equipped = ""; st.rerun()
            elif c_i2.button("장착", key=f"eq_{item}"): st.session_state.equipped = shop_items[item]['emoji']; st.rerun()

# [탭 4: 미션 & 퀴즈 - 무제한 보상 버그 수정 완료]
with tab_quiz:
    st.subheader("🎯 오늘의 퀴즈")
    st.write("문제를 맞히면 보너스 자산과 포인트가 지급됩니다! (문제당 1회 한정)")
    
    for i, item in enumerate(quiz_pool):
        with st.container():
            st.markdown(f'<div class="quiz-container"><b>Q{i+1}. {item["q"]}</b></div>', unsafe_allow_html=True)
            
            # 이미 푼 문제는 입력 차단
            if st.session_state.quiz_cleared[i]:
                st.success(f"✅ 문제 {i+1} 완료! 보상이 지급되었습니다.")
            else:
                ans = st.radio(f"정답을 선택하세요 (Q{i+1})", item['o'], key=f"q_{i}", index=None)
                if st.button(f"정답 확인 (Q{i+1})", key=f"btn_{i}"):
                    if ans == item['a']:
                        st.session_state.quiz_cleared[i] = True # 완료 상태 저장
                        st.session_state.balance += 10000
                        st.session_state.points += 10
                        st.success("정답입니다! 10,000원과 10P가 지급되었습니다.")
                        time.sleep(0.5); st.rerun()
                    else:
                        st.error("오답입니다. 다시 시도해보세요!")
        st.write("---")

# [탭 5: 투자 사전 - 순수 주식 용어]
with tab_academy:
    st.header("📚 리얼 투자 사전")
    terms = {
        "코스피(KOSPI)": "국내 종합주가지수. 주로 대기업들이 상장되어 있습니다.",
        "매수/매도": "주식을 사는 것을 매수, 파는 것을 매도라고 합니다.",
        "우량주": "수익성이 높고 재무구조가 탄탄한 대형주 (예: 삼성전자)",
        "공매도": "주가 하락을 예상하고 주식을 빌려서 파는 투자 기법",
        "순절매": "더 큰 손실을 막기 위해 현재 손해를 감수하고 주식을 파는 것"
    }
    for k, v in terms.items(): st.write(f"**{k}**: {v}")
    if st.button("🔄 시스템 리셋 (모든 데이터 초기화)"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
