import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import numpy as np
import random
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. 시스템 설정
st.set_page_config(page_title="AI 퀀트 유니버스 v27", layout="wide")
st_autorefresh(interval=2000, key="global_refresh")

# 2. 세션 상태 초기화 (대규모 확장)
if 'user_name' not in st.session_state:
    st.session_state.update({
        'user_name': "", 'tier': "초급", 'balance': 0.0, 'points': 0,
        'portfolio': {}, 'trade_log': [], 'messages': [], # 실시간 커뮤니티용
        'inventory': [], 'equipped': "🥚", 'daily_quiz': False, 'daily_check': False,
        'trade_count': 0, 'risk_score': 0, 'avatar_type': "🌱 투자 꿈나무",
        'season_end': None, 'quiz_cleared': [False]*5, 'term_idx': 0
    })

# 3. 데이터 및 상수 정의
stock_map = {"삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "NVIDIA": "NVDA", "애플": "AAPL", "테슬라": "TSLA"}
tier_info = {
    "초급": {"seed": 50000000, "multiplier": 1.0, "min_asset": 100000},
    "중급": {"seed": 10000000, "multiplier": 2.5, "min_asset": 50000},
    "상급": {"seed": 1000000, "multiplier": 5.0, "min_asset": 10000}
}
shop_items = {
    "초급": {"🎈 풍선": 10, "👓 연습용 안경": 30},
    "중급": {"💼 서류가방": 100, "📱 최신 폰": 250},
    "상급": {"👑 황금 왕관": 1000, "🏎️ 슈퍼카": 5000}
}

# 4. CSS 스타일링
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .metric-card { background: #1d2026; padding: 15px; border-radius: 15px; border: 1px solid #3d414a; }
    .chat-box { background: #161b22; padding: 10px; border-radius: 10px; height: 300px; overflow-y: auto; border: 1px solid #30363d; }
    .rank-tag { padding: 2px 8px; border-radius: 5px; font-size: 0.8rem; font-weight: bold; }
    .tier-beginner { background: #238636; } .tier-mid { background: #1f6feb; } .tier-pro { background: #8957e5; }
    </style>
""", unsafe_allow_html=True)

# 5. 유틸리티 함수
def fetch_data(name):
    try:
        df = yf.download(stock_map[name], period="1mo", interval="60m", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        curr = int(df['Close'].iloc[-1] * (1 if ".KS" in stock_map[name] else 1410))
        return curr, df
    except: return 100000, None

def get_ai_avatar(count, risk):
    if count > 20: return "⚖️ 냉철한 분석가", "💻"
    if risk > 10: return "🚀 불타는 로켓", "🔥"
    return "🌱 투자 꿈나무", "🌱"

# 6. 메인 로직: 로그인 및 페이지 네비게이션
if not st.session_state.user_name:
    st.title("🚀 AI 투자 RPG: 유니버스")
    name = st.text_input("닉네임")
    choice = st.selectbox("리그 선택", ["초급", "중급", "상급"])
    if st.button("시작"):
        st.session_state.update({'user_name': name, 'tier': choice, 'balance': tier_info[choice]['seed'], 'portfolio': {s:0 for s in stock_map}})
        st.rerun()
    st.stop()

# --- 사이드바 네비게이션 ---
page = st.sidebar.radio("📌 메뉴", ["🏠 홈/대시보드", "🛒 거래소/랭킹", "📚 아카데미", "💬 커뮤니티", "🛍️ 포인트 상점"])

# 실시간 자산 계산
total_stock_val = 0
for s in stock_map:
    p, _ = fetch_data(s)
    total_stock_val += st.session_state.portfolio.get(s, 0) * p
total_assets = st.session_state.balance + total_stock_val

# --- 왕초보 구제 시스템 (Safety Net) ---
if total_assets < tier_info[st.session_state.tier]['min_asset']:
    st.warning("⚠️ 긴급 자금 수혈! 시드머니가 충전되었습니다.")
    st.session_state.balance += 500000
    st.rerun()

# --- 페이지 1: 홈/대시보드 ---
if page == "🏠 홈/대시보드":
    st.title(f"{st.session_state.equipped} {st.session_state.user_name}님 환영합니다!")
    
    # AI 성향 분석 업데이트
    st.session_state.avatar_type, emoji = get_ai_avatar(st.session_state.trade_count, st.session_state.tech_focus)
    
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("💰 총 자산", f"{total_assets:,.0f}원")
    with col2: st.metric("💎 포인트", f"{st.session_state.points}P")
    with col3: st.metric("🏆 리그", st.session_state.tier)

    st.info(f"🤖 AI 분석 결과: 귀하는 **[{st.session_state.avatar_type}]** 성향입니다.")
    
    # 일일 미션
    with st.expander("📅 일일 미션 현황"):
        if not st.session_state.daily_check:
            if st.button("출석체크 (+50P)"):
                st.session_state.points += 50; st.session_state.daily_check = True; st.rerun()
        else: st.success("✅ 출석 완료")
        st.write("- 주식 1회 매수하기 (미완료)" if st.session_state.trade_count == 0 else "✅ 주식 매수 완료")

# --- 페이지 2: 거래소/랭킹 ---
elif page == "🛒 거래소/랭킹":
    m_col, r_col = st.columns([1.8, 1.2])
    with m_col:
        target = st.selectbox("분석 종목", list(stock_map.keys()))
        p, df = fetch_data(target)
        if df is not None:
            fig = go.Figure(data=[go.Candlestick(x=df.index.strftime('%H:%M'), open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
            fig.update_layout(xaxis_type='category', template="plotly_dark", height=400, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
        
        qty = st.number_input("수량", min_value=1, value=1)
        b, s = st.columns(2)
        if b.button("매수"):
            if st.session_state.balance >= p*qty:
                st.session_state.balance -= p*qty; st.session_state.portfolio[target] += qty
                st.session_state.trade_count += 1; st.rerun()
        if s.button("매도"):
            if st.session_state.portfolio[target] >= qty:
                st.session_state.balance += p*qty; st.session_state.portfolio[target] -= qty
                st.session_state.trade_count += 1; st.rerun()

    with r_col:
        st.subheader(f"🏆 {st.session_state.tier} 리그 랭킹")
        # 실제로는 DB 연동이 필요하나, 여기선 데모용 가상 데이터
        st.markdown(f"<div class='rank-card'>🥇 {st.session_state.user_name} (나) <br> {total_assets:,.0f}원</div>", unsafe_allow_html=True)
        st.caption("※ 상위 리그로 갈수록 포인트 획득량이 최대 5배 증가합니다!")

# --- 페이지 3: 아카데미 (팁, 용어, 퀴즈) ---
elif page == "📚 아카데미":
    t1, t2, t3 = st.tabs(["💡 투자 팁", "📖 용어 사전", "❓ 주식 퀴즈"])
    with t1:
        st.write("### 오늘의 투자 팁\n1. 분산 투자는 위험을 줄이는 기본입니다.\n2. 공포에 사서 환희에 파세요.")
    with t2:
        start = st.session_state.term_idx
        for t in ["코스피", "블루칩", "배당금", "시가총액", "서킷브레이커"]:
            st.markdown(f"**{t}**: 관련 설명 데이터...")
    with t3:
        st.subheader("포인트 획득 퀴즈")
        if not st.session_state.daily_quiz:
            ans = st.radio("상승장을 뜻하는 동물은?", ["황소", "곰", "사자"])
            if st.button("정답 확인"):
                if ans == "황소":
                    st.session_state.points += 100; st.session_state.daily_quiz = True; st.rerun()
        else: st.success("오늘의 퀴즈를 완료했습니다!")

# --- 페이지 4: 커뮤니티 ---
elif page == "💬 커뮤니티":
    st.title("🤝 실시간 투자자 광장")
    with st.container():
        st.markdown('<div class="chat-box">', unsafe_allow_html=True)
        for msg in st.session_state.messages[-10:]: # 최근 10개만
            st.write(f"**{msg['user']}**: {msg['text']}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    new_msg = st.text_input("메시지 입력", key="chat_input")
    if st.button("전송"):
        st.session_state.messages.append({"user": st.session_state.user_name, "text": new_msg})
        st.rerun()

# --- 페이지 5: 포인트 상점 ---
elif page == "🛍️ 포인트 상점":
    st.title("🎭 액세서리 샵")
    st.info(f"현재 리그: {st.session_state.tier} (리그에 따라 상품이 해금됩니다)")
    
    for tier, items in shop_items.items():
        st.subheader(f"[{tier} 등급용 상품]")
        cols = st.columns(len(items))
        for i, (item_name, price) in enumerate(items.items()):
            with cols[i]:
                st.write(f"**{item_name}**")
                st.write(f"💰 {price} P")
                # 본인 티어보다 높으면 잠금
                lock = (tier == "상급" and st.session_state.tier != "상급") or (tier == "중급" and st.session_state.tier == "초급")
                if lock:
                    st.button("🔒 잠김", key=f"lock_{item_name}", disabled=True)
                elif item_name in st.session_state.inventory:
                    if st.button("장착하기", key=f"eq_{item_name}"):
                        st.session_state.equipped = item_name.split()[-1]
                else:
                    if st.button("구매", key=f"buy_{item_name}"):
                        if st.session_state.points >= price:
                            st.session_state.points -= price; st.session_state.inventory.append(item_name); st.rerun()
