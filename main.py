import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import numpy as np
import random
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. 시스템 설정 및 실시간 틱
st.set_page_config(page_title="AI 투자 유니버스 v28", layout="wide")
st_autorefresh(interval=2000, key="global_tick")

# 2. 세션 상태 초기화 (AttributeError 해결 포인트)
if 'user_name' not in st.session_state:
    st.session_state.update({
        'user_name': "", 'tier': "초급", 'balance': 0.0, 'points': 0,
        'portfolio': {}, 'trade_log': [], 'messages': [], # 커뮤니티용
        'inventory': [], 'equipped': "", 'daily_quiz': False, 'daily_check': False,
        'trade_count': 0, 'tech_focus': 0, # 💡 오류 해결: 여기서 초기화
        'avatar_type': "🌱 투자 꿈나무", 'season_end': None, 
        'quiz_cleared': [False]*5, 'term_idx': 0
    })

# 3. 데이터 및 상수
stock_map = {
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", 
    "NVIDIA": "NVDA", "애플": "AAPL", "테슬라": "TSLA"
}

# 티어별 혜택 및 구제 자금 설정
tier_cfg = {
    "초급": {"seed": 50000000, "pt_mul": 1.0, "safe_net": 500000, "limit": 100000, "color": "#238636"},
    "중급": {"seed": 10000000, "pt_mul": 2.5, "safe_net": 100000, "limit": 50000, "color": "#1f6feb"},
    "상급": {"seed": 1000000, "pt_mul": 5.0, "safe_net": 10000, "limit": 5000, "color": "#8957e5"}
}

# 티어별 해금 아이템
shop_items = {
    "초급": {"🎈 풍선": 50, "👓 연습용 안경": 100},
    "중급": {"💼 비즈니스 가방": 500, "📱 최신 스마트폰": 1200},
    "상급": {"👑 황금 왕관": 5000, "🏎️ 슈퍼카": 15000}
}

# 4. CSS 스타일 (다크모드 가독성 및 UI 최적화)
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0e1117; color: white; }}
    .metric-card {{ background: #1d2026; padding: 20px; border-radius: 15px; border: 1px solid #3d414a; }}
    .rank-card {{ background: #161b22; padding: 12px; border-radius: 10px; border-left: 5px solid #3b82f6; margin-bottom: 8px; }}
    .chat-box {{ background: #0d1117; border: 1px solid #30363d; height: 350px; overflow-y: auto; padding: 15px; border-radius: 10px; }}
    .timer-box {{ background: #ef4444; color: white; padding: 15px; border-radius: 12px; text-align: center; font-weight: bold; }}
    </style>
""", unsafe_allow_html=True)

# 5. 핵심 엔진 함수
@st.cache_data(ttl=30)
def fetch_stock(name):
    try:
        df = yf.download(stock_map[name], period="5d", interval="30m", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        curr = int(df['Close'].iloc[-1] * (1 if ".KS" in stock_map[name] else 1410))
        return curr, df
    except: return 100000, None

def analyze_ai(count, tech):
    if count > 20: return "⚖️ 냉철한 분석가", "💻"
    if tech > 10: return "🚀 테크주 매니아", "⚡"
    return "🌱 투자 꿈나무", "🌱"

# 6. 로그인 관문 (시작 버튼)
if not st.session_state.user_name:
    st.title("🚀 AI 투자 RPG: 퀀트 유니버스")
    name = st.text_input("닉네임을 입력하세요")
    league = st.selectbox("참여 리그 선택", ["초급", "중급", "상급"])
    if st.button("시작"):
        if name:
            st.session_state.update({
                'user_name': name, 'tier': league, 
                'balance': tier_cfg[league]['seed'], 
                'portfolio': {s: 0 for s in stock_map},
                'season_end': datetime.now() + timedelta(minutes=5)
            })
            st.rerun()
    st.stop()

# 실시간 데이터 및 총 자산 계산
current_prices = {}; total_stock_val = 0
for s in stock_map:
    p, _ = fetch_stock(s)
    current_prices[s] = p
    total_stock_val += st.session_state.portfolio.get(s, 0) * p
total_assets = st.session_state.balance + total_stock_val

# --- 왕초보 구제 시스템 (시드머니 0원 방지) ---
if total_assets < tier_cfg[st.session_state.tier]['limit']:
    st.session_state.balance += tier_cfg[st.session_state.tier]['safe_net']
    st.warning(f"💸 파산 위기! {st.session_state.tier} 리그 긴급 지원금이 지급되었습니다.")

# --- 메인 네비게이션 ---
page = st.sidebar.radio("🧭 메뉴 이동", ["🏠 홈", "🛒 거래소/랭킹", "📚 아카데미(팁/퀴즈)", "💬 커뮤니티", "🛍️ 포인트 샵"])

# 페이지 1: 홈 (환영 인사 & AI 성향)
if page == "🏠 홈":
    st.title(f"{st.session_state.equipped} {st.session_state.user_name}님 환영합니다!")
    
    # AI 성향 자동 업데이트
    st.session_state.avatar_type, avatar_emoji = analyze_ai(st.session_state.trade_count, st.session_state.tech_focus)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("🏆 리그", st.session_state.tier)
    c2.metric("💰 총 자산", f"{total_assets:,.0f}원")
    c3.metric("💎 포인트", f"{st.session_state.points}P")
    
    st.info(f"🤖 AI 분석: 귀하는 현재 **[{st.session_state.avatar_type}]** 상태입니다.")
    
    # 일일 미션
    st.subheader("🎯 일일 미션")
    if not st.session_state.daily_check:
        if st.button("출석 체크하고 50P 받기"):
            st.session_state.points += 50; st.session_state.daily_check = True; st.rerun()
    else: st.success("✅ 오늘의 출석 완료")

# 페이지 2: 거래소 및 티어별 랭킹
elif page == "🛒 거래소/랭킹":
    m_col, r_col = st.columns([1.8, 1.2])
    with m_col:
        target = st.selectbox("종목 선택", list(stock_map.keys()))
        p, df = fetch_stock(target)
        if df is not None:
            # 연속형 그래프 (X축 카테고리 설정)
            fig = go.Figure(data=[go.Candlestick(x=df.index.strftime('%H:%M'), open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], increasing_line_color='#ef4444', decreasing_line_color='#3b82f6')])
            fig.update_layout(xaxis_type='category', template="plotly_dark", height=400, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
        
        qty = st.number_input("거래 수량", min_value=1, value=1)
        b, s = st.columns(2)
        if b.button("매수"):
            if st.session_state.balance >= p * qty:
                st.session_state.balance -= p * qty; st.session_state.portfolio[target] += qty
                st.session_state.trade_count += 1
                if target in ["NVIDIA", "테슬라", "애플"]: st.session_state.tech_focus += 1
                st.rerun()
        if s.button("매도"):
            if st.session_state.portfolio[target] >= qty:
                st.session_state.balance += p * qty; st.session_state.portfolio[target] -= qty
                st.session_state.trade_count += 1; st.rerun()

    with r_col:
        # 타이머
        tl = st.session_state.season_end - datetime.now()
        sl = max(0, tl.total_seconds())
        if sl > 0: st.markdown(f'<div class="timer-box">⏳ 시즌 종료: {int(sl//60)}분 {int(sl%60)}초</div>', unsafe_allow_html=True)
        else: st.error("🏁 시즌 종료!")
        
        st.subheader(f"🏆 {st.session_state.tier} 리그 랭킹")
        st.markdown(f"<div class='rank-card'>🥇 {st.session_state.user_name} (나) <br> 자산: {total_assets:,.0f}원</div>", unsafe_allow_html=True)
        st.caption("※ 상급 리그일수록 포인트 배율이 5배까지 증가합니다!")

# 페이지 3: 아카데미 (팁, 용어, 퀴즈)
elif page == "📚 아카데미(팁/퀴즈)":
    t1, t2, t3 = st.tabs(["💡 투자 팁", "📖 용어 사전", "❓ 주식 퀴즈"])
    with t1:
        st.write("### 💎 리그별 혜택 안내")
        st.success("**상급 리그:** 상점의 '슈퍼카'와 '황금 왕관' 구매 권한 해금, 포인트 5배 적립")
        st.info("**중급 리그:** 비즈니스 아이템 해금, 포인트 2.5배 적립")
    with t2:
        st.subheader("📖 주식 사전")
        terms = ["코스피", "블루칩", "배당금", "시가총액", "PER"]
        for t in terms: st.write(f"**{t}**: 관련 정의 및 시장 데이터...")
    with t3:
        if not st.session_state.daily_quiz:
            st.subheader("오늘의 퀴즈 (+100P)")
            ans = st.radio("기업의 가치를 주식 수로 나눈 것은?", ["주가", "배당", "시가총액"])
            if st.button("정답 확인"):
                if ans == "주가":
                    st.session_state.points += 100; st.session_state.daily_quiz = True; st.rerun()
        else: st.success("✅ 오늘의 퀴즈 완료!")

# 페이지 4: 커뮤니티 (실시간 채팅)
elif page == "💬 커뮤니티":
    st.title("💬 투자자 실시간 광장")
    chat_container = st.container()
    with chat_container:
        st.markdown('<div class="chat-box">', unsafe_allow_html=True)
        for m in st.session_state.messages[-15:]:
            st.write(f"**{m['user']}**: {m['text']}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with st.form("chat_form", clear_on_submit=True):
        msg = st.text_input("메시지를 입력하세요")
        if st.form_submit_button("전송"):
            st.session_state.messages.append({"user": st.session_state.user_name, "text": msg})
            st.rerun()

# 페이지 5: 포인트 샵 (티어별 아이템 해금)
elif page == "🛍️ 포인트 샵":
    st.title("🛍️ 포인트 상점")
    st.write(f"보유 포인트: **{st.session_state.points} P**")
    
    for tier, items in shop_items.items():
        st.subheader(f"[{tier} 전용 아이템]")
        cols = st.columns(len(items))
        for i, (name, price) in enumerate(items.items()):
            # 잠금 로직: 본인 티어가 낮으면 구매 불가
            is_locked = (tier == "상급" and st.session_state.tier != "상급") or (tier == "중급" and st.session_state.tier == "초급")
            with cols[i]:
                st.write(f"**{name}**")
                st.write(f"💰 {price} P")
                if is_locked:
                    st.button("🔒 잠김", key=f"lock_{name}", disabled=True)
                elif name in st.session_state.inventory:
                    if st.button("장착", key=f"eq_{name}"):
                        st.session_state.equipped = name.split()[-1]
                else:
                    if st.button("구매", key=f"buy_{name}"):
                        if st.session_state.points >= price:
                            st.session_state.points -= price
                            st.session_state.inventory.append(name); st.rerun()

st.sidebar.divider()
if st.sidebar.button("🔄 시스템 초기화"):
    for k in list(st.session_state.keys()): del st.session_state[k]
    st.rerun()
