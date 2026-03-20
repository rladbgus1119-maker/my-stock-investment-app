import streamlit as st
import pandas as pd
import yfinance as yf
import time
import numpy as np
import random

# 1. 페이지 설정 및 테마 시스템
st.set_page_config(page_title="원광대 AI 투자 & 아카데미 v6.0", layout="wide")

# 사이드바 설정 (테마 및 포인트 표시)
st.sidebar.title("⚙️ 시스템 설정")
theme_choice = st.sidebar.radio("배경 테마 선택", ["라이트 모드", "다크 모드"])

if theme_choice == "다크 모드":
    bg, txt, card, border = "#0e1117", "#ffffff", "#262730", "#444"
else:
    bg, txt, card, border = "#ffffff", "#000000", "#f8fafc", "#e2e8f0"

# 커스텀 CSS 적용
st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg}; color: {txt}; }}
    h1, h2, h3, h4, p, span, label {{ color: {txt} !important; }}
    .stMetric {{ background-color: {card}; padding: 12px; border-radius: 12px; border: 1px solid {border}; }}
    .rank-card {{ background-color: {card}; border-radius: 10px; padding: 10px; border: 1px solid {border}; margin-bottom: 5px; }}
    .item-card {{ background-color: {card}; padding: 15px; border-radius: 10px; border: 1px solid {border}; text-align: center; margin-bottom: 10px; }}
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 세트 및 아바타 설정
stock_map = {
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "NVIDIA": "NVDA",
    "애플": "AAPL", "테슬라": "TSLA", "현대차": "005380.KS", "넥슨": "3659.T"
}

avatar_base = {"🛡️ 든든한 가디언": "🐢", "🚀 불타는 로켓": "🚀", "⚖️ 냉철한 분석가": "💻", "🌱 투자 꿈나무": "🌱", "🐣 분석 대기 중": "🥚"}

shop_items = {
    "👑 황금 왕관": {"price": 100, "emoji": "👑"},
    "🥼 연구실 실험복": {"price": 50, "emoji": "🥼"},
    "🎮 드론 컨트롤러": {"price": 30, "emoji": "🎮"},
    "🏎️ RC카 조종기": {"price": 30, "emoji": "🏎️"},
    "🎓 원광대 학사모": {"price": 80, "emoji": "🎓"},
    "🕶️ 테크니컬 고글": {"price": 40, "emoji": "🕶️"}
}

quiz_pool = [
    {"q": "기업이 이익의 일부를 주주에게 나누어 주는 보너스는?", "a": "배당금", "o": ["배당금", "이자", "상여금"]},
    {"q": "주식 수량에 현재가를 곱한 기업의 전체 가치는?", "a": "시가총액", "o": ["자본금", "시가총액", "매출액"]},
    {"q": "PER이 낮을수록 이익 대비 주가가 저평가된 것이다?", "a": "O", "o": ["O", "X"]}
]

# 3. 실시간 가격 엔진
@st.cache_data(ttl=30)
def fetch_prices():
    prices = {}
    for name, ticker in stock_map.items():
        try:
            data = yf.Ticker(ticker); p = data.history(period="1d")['Close'].iloc[-1]
            if ".KS" not in ticker: p *= 1415 # 환율
            prices[name] = int(p * (1 + (np.random.rand()-0.5)*0.005))
        except: prices[name] = 100000
    return prices

# 4. 세션 상태 초기화
if 'user_name' not in st.session_state:
    st.session_state.update({
        'user_name': "", 'difficulty': "", 'balance': 0.0, 'points': 0,
        'portfolio': {s: 0 for s in stock_map}, 'trade_count': 0, 'tech_focus': 0,
        'avatar': "🐣 분석 대기 중", 'attendance': False,
        'inventory': [], 'equipped': "", 'bots': []
    })

def init_bots(diff):
    names = ["퀀트장인", "익산불개미", "반도체박사", "나스닥귀신", "워런버핏봇", "단타의신", "원광대우등생", "AI알고리즘", "풀매수전사"]
    base = {"초급": 50000000, "중급": 10000000, "상급": 1000000}[diff]
    return [{"닉네임": n, "자산": base * (1 + (random.random()-0.5)*0.1), "성향": random.choice(list(avatar_base.keys())[:4]), "난이도": diff} for n in names]

# 5. 로그인 화면
if not st.session_state.user_name:
    st.title("👨‍🔬 원광대 행동분석 AI 투자 센터")
    with st.container(border=True):
        name = st.text_input("닉네임 입력")
        diff_choice = st.selectbox("등급 선택", ["초급 (5,000만)", "중급 (1,000만)", "상급 (100만)"])
        if st.button("시스템 가동"):
            if name:
                st.session_state.user_name = name
                d_label = diff_choice.split()[0]
                st.session_state.difficulty = d_label
                st.session_state.balance = 50000000.0 if "초급" in diff_choice else 10000000.0 if "중급" in diff_choice else 1000000.0
                st.session_state.bots = init_bots(d_label)
                st.rerun()
    st.stop()

# 6. 행동 분석 AI 엔진
def analyze_personality():
    tc = st.session_state.trade_count
    tf = st.session_state.tech_focus
    if tc >= 10: st.session_state.avatar = "⚖️ 냉철한 분석가"
    elif tf >= 5: st.session_state.avatar = "🚀 불타는 로켓"
    elif tc >= 1: st.session_state.avatar = "🛡️ 든든한 가디언"
    else: st.session_state.avatar = "🌱 투자 꿈나무"

analyze_personality()

# 7. 상단 대시보드
prices = fetch_prices()
total_stock_val = sum(st.session_state.portfolio[s] * prices[s] for s in stock_map)
total_assets = st.session_state.balance + total_stock_val

# 아바타 조합 (베이스 + 아이템)
full_avatar = f"{avatar_base.get(st.session_state.avatar, '🥚')} {st.session_state.equipped}"

st.title(f"{full_avatar} {st.session_state.user_name} 관제 센터")
st.sidebar.metric("💎 나의 포인트", f"{st.session_state.points} P")

col_h1, col_h2, col_h3 = st.columns([1.5, 1.5, 1])
col_h1.metric("💵 현금 자산", f"{st.session_state.balance:,.0f}원")
col_h2.metric("🏆 총 자산", f"{total_assets:,.0f}원")
with col_h3:
    if not st.session_state.attendance:
        if st.button("📅 출석 체크 (+5만/10P)"):
            st.session_state.attendance = True; st.session_state.balance += 50000; st.session_state.points += 10; st.rerun()
    else: st.success("✅ 출석 완료")

st.divider()

# 8. 기능 통합 탭
tab_market, tab_shop, tab_custom, tab_quiz = st.tabs(["🛒 거래소 & 랭킹", "🛍️ 포인트 상점", "👗 아바타 꾸미기", "❓ 미션 & 퀴즈"])

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
                        st.write(f"### {n}"); st.write(f"가: {p:,}원 | 보: {st.session_state.portfolio[n]}주")
                        b, s = st.columns(2)
                        if b.button(f"매수", key=f"b_{n}"):
                            if st.session_state.balance >= p * qty:
                                st.session_state.balance -= p * qty; st.session_state.portfolio[n] += qty
                                st.session_state.trade_count += 1
                                if n in ["NVIDIA", "테슬라"]: st.session_state.tech_focus += 1
                                st.rerun()
                        if s.button(f"매도", key=f"s_{n}"):
                            if st.session_state.portfolio[n] >= qty:
                                st.session_state.balance += p * qty; st.session_state.portfolio[n] -= qty
                                st.session_state.trade_count += 1; st.rerun()
    with c_r:
        st.subheader(f"🏆 {st.session_state.difficulty} 10인 랭킹")
        user_rank = {"닉네임": f"{st.session_state.user_name} ⭐", "성향": st.session_state.avatar, "자산": total_assets}
        for bot in st.session_state.bots: bot['자산'] *= (1 + (random.random()-0.5)*0.002) # 봇 자산 역동성
        all_players = sorted(st.session_state.bots + [user_rank], key=lambda x: x["자산"], reverse=True)
        for idx, p in enumerate(all_players):
            medal = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else f"{idx+1}위"
            st.markdown(f'<div class="rank-card">{medal} {p["닉네임"]} <br> {p["자산"]:,.0f}원</div>', unsafe_allow_html=True)
        if st.button("🔄 시세/랭킹 새로고침"): st.rerun()

# [탭 2: 포인트 상점]
with tab_shop:
    st.header("🛍️ 포인트 상점")
    item_cols = st.columns(3)
    for idx, (name, info) in enumerate(shop_items.items()):
        with item_cols[idx % 3]:
            st.markdown(f'<div class="item-card"><h2>{info["emoji"]}</h2><b>{name}</b><br>{info["price"]} P</div>', unsafe_allow_html=True)
            if name in st.session_state.inventory:
                st.button("보유 중", key=f"owned_{name}", disabled=True, use_container_width=True)
            else:
                if st.button(f"구매", key=f"buy_{name}", use_container_width=True):
                    if st.session_state.points >= info['price']:
                        st.session_state.points -= info['price']; st.session_state.inventory.append(name); st.rerun()
                    else: st.error("포인트 부족!")

# [탭 3: 아바타 꾸미기]
with tab_custom:
    st.header("👗 나의 드레스룸")
    if not st.session_state.inventory:
        st.info("상점에서 아이템을 먼저 구매해 보세요!")
    else:
        for item in st.session_state.inventory:
            col_i1, col_i2 = st.columns([3, 1])
            col_i1.write(f"### {item}")
            if st.session_state.equipped == shop_items[item]['emoji']:
                if col_i2.button("해제", key=f"un_{item}"): st.session_state.equipped = ""; st.rerun()
            else:
                if col_i2.button("장착", key=f"eq_{item}"): st.session_state.equipped = shop_items[item]['emoji']; st.rerun()

# [탭 4: 미션 & 퀴즈]
with tab_quiz:
    st.subheader("🎯 특별 미션")
    if total_assets >= 100000000:
        if st.button("🚩 자산 1억 달성 보상 받기 (+100P)"): st.session_state.points += 100; st.rerun()
    
    st.divider()
    st.subheader("🧠 지식 퀴즈 (정답 시 10P + 1만 원)")
    for i, item in enumerate(quiz_pool):
        with st.container(border=True):
            st.markdown(f"#### Q{i+1}. {item['q']}")
            ans = st.radio(f"정답 선택 (Q{i+1})", item['o'], key=f"q_{i}")
            if st.button(f"정답 제출", key=f"btn_{i}"):
                if ans == item['a']:
                    st.success("정답! 보상이 지급되었습니다."); st.session_state.balance += 10000; st.session_state.points += 10; st.rerun()
                else: st.error("오답입니다!")

    if st.button("🔄 전체 초기화"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

st.latex(r"Asset_{total} = Balance + \sum (Price_{real} \times Qty)")
