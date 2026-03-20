import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import random
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. 페이지 설정 및 다이내믹 테마
st.set_page_config(page_title="AI 실시간 투자 터미널 v17", layout="wide")

# 1초마다 자동 새로고침 (실시간 타이머 및 차트 업데이트)
st_autorefresh(interval=1000, key="datarefresh")

st.sidebar.title("🎨 UI 환경 설정")
theme_choice = st.sidebar.radio("배경 테마 선택", ["라이트 모드", "다크 모드"])

if theme_choice == "다크 모드":
    bg, txt, card, border = "#0e1117", "#ffffff", "#1d2026", "#3d414a"
    plotly_template = "plotly_dark"
else:
    bg, txt, card, border = "#ffffff", "#000000", "#f8fafc", "#e2e8f0"
    plotly_template = "plotly_white"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg} !important; color: {txt} !important; }}
    h1, h2, h3, h4, p, span, div, label, .stMarkdown, .stTable {{ color: {txt} !important; }}
    [data-testid="stWidgetLabel"] p {{ color: {txt} !important; font-weight: bold; }}
    .stMetric {{ background-color: {card} !important; padding: 15px; border-radius: 12px; border: 1px solid {border} !important; }}
    .rank-card {{ background-color: {card} !important; border-radius: 10px; padding: 12px; border: 1px solid {border} !important; margin-bottom: 8px; }}
    .quiz-container {{ background-color: {card} !important; padding: 20px; border-radius: 12px; border-left: 6px solid #ef4444 !important; margin-bottom: 15px; }}
    .timer-box {{ background-color: #ef4444; color: white !important; padding: 15px; border-radius: 12px; text-align: center; font-size: 1.4rem; font-weight: bold; margin-bottom: 15px; }}
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 세트
stock_map = {
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "NVIDIA": "NVDA",
    "애플": "AAPL", "테슬라": "TSLA", "마이크로소프트": "MSFT", "아마존": "AMZN", "현대차": "005380.KS"
}

avatar_base = {"🛡️ 든든한 가디언": "🐢", "🚀 불타는 로켓": "🚀", "⚖️ 냉철한 분석가": "💻", "🌱 투자 꿈나무": "🌱", "🐣 분석 대기 중": "🥚"}

# 3. 실시간 주가 및 차트 엔진 (진짜 데이터 기반)
@st.cache_data(ttl=30)
def fetch_realtime_chart(target_name):
    ticker = stock_map[target_name]
    try:
        # 최근 5일간의 30분 단위 데이터를 가져옴 (가장 안정적)
        data = yf.download(ticker, period="5d", interval="30m", progress=False)
        if data.empty:
            return 100000, pd.DataFrame()
        
        # 한국인 입맛에 맞는 실시간 가격 (종가 기준)
        current_price = data['Close'].iloc[-1]
        if ".KS" not in ticker: current_price *= 1415 # 실시간 환율 적용
        
        # 이동평균선 계산 (MA5, MA20)
        data['MA5'] = data['Close'].rolling(window=5).mean()
        data['MA20'] = data['Close'].rolling(window=20).mean()
        
        return int(current_price), data
    except:
        return 100000, pd.DataFrame()

# 4. 세션 상태 초기화
if 'user_name' not in st.session_state:
    st.session_state.update({
        'user_name': "", 'difficulty': "", 'balance': 0.0, 'points': 0,
        'portfolio': {s: 0 for s in stock_map}, 'trade_log': [],
        'trade_count': 0, 'tech_focus': 0, 'avatar': "🐣 분석 대기 중",
        'attendance': False, 'quiz_cleared': [False]*5, 'bots': [], 
        'season_end_time': None, 'is_season_ended': False, 'equipped': ""
    })

def init_bots(diff):
    names = ["퀀트장인", "익산불개미", "여의도황소", "나스닥귀신", "단타의신", "원광대우등생", "AI알고리즘", "풀매수전사"]
    base = {"초급": 50000000, "중급": 10000000, "상급": 1000000}[diff]
    return [{"닉네임": n, "자산": base * (1 + (random.random()-0.5)*0.2), "성향": "🛡️ 든든한 가디언", "난이도": diff} for n in names]

# 5. 로그인 화면
if not st.session_state.user_name:
    st.title("🏆 AI 투자 5분 스피드 시즌전")
    with st.container(border=True):
        name = st.text_input("닉네임 입력")
        diff_choice = st.selectbox("참여 등급", ["초급 (5,000만)", "중급 (1,000만)", "상급 (100만)"])
        if st.button("시작"):
            if name:
                st.session_state.user_name = name; dl = diff_choice.split()[0]
                st.session_state.difficulty = dl; st.session_state.balance = 50000000.0 if "초급" in diff_choice else 10000000.0 if "중급" in diff_choice else 1000000.0
                st.session_state.bots = init_bots(dl)
                st.session_state.season_end_time = datetime.now() + timedelta(minutes=5)
                st.rerun()
    st.stop()

# 6. 실시간 자산 및 타이머 계산
time_left = st.session_state.season_end_time - datetime.now()
seconds_left = max(0, time_left.total_seconds())
if seconds_left <= 0: st.session_state.is_season_ended = True

live_prices = {}; stock_histories = {}
total_stock_value = 0
for n in stock_map.keys():
    price, history = fetch_realtime_chart(n)
    live_prices[n] = price; stock_histories[n] = history
    total_stock_value += st.session_state.portfolio[n] * price

total_assets = st.session_state.balance + total_stock_value

# 7. 대시보드
full_avatar = f"{avatar_base.get(st.session_state.avatar, '🥚')} {st.session_state.equipped}"
st.title(f"{full_avatar} {st.session_state.user_name}님 환영합니다!")

col_h1, col_h2, col_h3 = st.columns([1.5, 1.5, 1])
col_h1.metric("💵 가용 현금", f"{st.session_state.balance:,.0f}원")
col_h2.metric("🏆 실시간 총 자산", f"{total_assets:,.0f}원")
with col_h3:
    if not st.session_state.attendance:
        if st.button("📅 출석 체크"):
            st.session_state.balance += 50000; st.session_state.points += 10; st.session_state.attendance = True; st.rerun()
    else: st.success("✅ 오늘 출석 완료")

st.divider()

# 8. 메인 기능 탭
tab_market, tab_portfolio, tab_quiz = st.tabs(["🛒 거래소 & 랭킹", "📂 자산 분석", "❓ 주식 퀴즈"])

with tab_market:
    m_col, r_col = st.columns([2, 1])
    with m_col:
        target_stock = st.selectbox("종목 선택", list(stock_map.keys()))
        df = stock_histories[target_stock]
        
        # 📈 [진짜 차트 시스템]
        if not df.empty:
            fig = go.Figure()
            # 1. 캔들스틱 추가 (한국 스타일 색상 적용)
            fig.add_trace(go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                increasing_line_color='#ef4444', decreasing_line_color='#3b82f6',
                name='시세'
            ))
            # 2. 이동평균선 추가
            fig.add_trace(go.Scatter(x=df.index, y=df['MA5'], mode='lines', line=dict(color='#f59e0b', width=1.2), name='5일선'))
            fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], mode='lines', line=dict(color='#a855f7', width=1.2), name='20일선'))

            fig.update_layout(
                title=f"📊 {target_stock} 실시간 전문 차트",
                template=plotly_template,
                xaxis_rangeslider_visible=False,
                height=500,
                margin=dict(l=10, r=10, t=50, b=10)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("데이터를 불러오는 중입니다... (장외 시간일 경우 마지막 종가 기준)")

        # 매매 인터페이스
        qty = st.number_input("거래 수량", min_value=1, value=1, disabled=st.session_state.is_season_ended)
        p = live_prices[target_stock]
        b_c, s_c = st.columns(2)
        if b_c.button(f"매수 ({p:,}원)", disabled=st.session_state.is_season_ended):
            if st.session_state.balance >= p * qty:
                st.session_state.balance -= p * qty; st.session_state.portfolio[target_stock] += qty; st.rerun()
        if s_c.button(f"매도 ({p:,}원)", disabled=st.session_state.is_season_ended):
            if st.session_state.portfolio[target_stock] >= qty:
                st.session_state.balance += p * qty; st.session_state.portfolio[target_stock] -= qty; st.rerun()

    with r_col:
        if not st.session_state.is_season_ended:
            st.markdown(f'<div class="timer-box">⏳ 시즌 종료까지: {int(seconds_left // 60)}분 {int(seconds_left % 60)}초</div>', unsafe_allow_html=True)
        else:
            st.error("🏁 시즌 종료 (순위 확정)")

        st.subheader("🏆 시즌 랭킹")
        user_rank_info = {"닉네임": f"{st.session_state.user_name} ⭐", "자산": total_assets}
        all_p = sorted(st.session_state.bots + [user_rank_info], key=lambda x: x["자산"], reverse=True)
        for idx, p in enumerate(all_p):
            st.markdown(f'<div class="rank-card">{"🥇" if idx==0 else "🥈" if idx==1 else "🥉" if idx==2 else f"{idx+1}위"} {p["닉네임"]} <br> {p["자산"]:,.0f}원</div>', unsafe_allow_html=True)
