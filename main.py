import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import numpy as np
import random
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. 시스템 설정
st.set_page_config(page_title="AI 실시간 퀀트 터미널 v34", layout="wide")

# 1초마다 자동 새로고침하여 자산과 순위를 실시간으로 요동치게 만듭니다.
st_autorefresh(interval=1000, key="live_engine")

# --- 2. 전역 데이터 및 종목 확장 ---
STOCK_MAP = {
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "현대차": "005380.KS",
    "삼성SDI": "006400.KS", "NVIDIA": "NVDA", "애플": "AAPL", 
    "테슬라": "TSLA", "마이크로소프트": "MSFT", "아마존": "AMZN", 
    "구글": "GOOGL", "메타": "META", "넷플릭스": "NFLX"
}

TIER_CFG = {
    "초급": {"seed": 100000000, "pt_mul": 1.0, "next": "중급"},
    "중급": {"seed": 50000000, "pt_mul": 2.5, "next": "고급"},
    "고급": {"seed": 10000000, "pt_mul": 5.0, "next": "마스터"}
}

SHOP_ITEMS = {
    "초급": {"🎈 풍선": 50, "👓 연습용 안경": 150},
    "중급": {"💼 서류가방": 1000, "📱 최신 폰": 2500},
    "고급": {"👑 황금 왕관": 10000, "🏎️ 슈퍼카": 50000}
}

QUIZ_POOL = [
    {"q": "상승장을 상징하는 동물은?", "a": "황소", "o": ["황소", "곰", "독수리"]},
    {"q": "하락장을 상징하는 동물은?", "a": "곰", "o": ["황소", "곰", "사자"]},
    {"q": "기업 이익을 주주에게 나눠주는 돈은?", "a": "배당", "o": ["배당", "이자", "상여"]}
]

EXCHANGE_RATE = 1420.0 # 실시간 느낌을 위한 고정 환율

# --- 3. 세션 상태 초기화 (에러 완치) ---
if 'user_name' not in st.session_state:
    st.session_state.update({
        'user_name': "", 'tier': "초급", 'balance': 0.0, 'points': 0,
        'portfolio': {s: 0 for s in STOCK_MAP}, 'messages': [],
        'inventory': [], 'equipped': "🥚", 'daily_check': False,
        'quiz_cleared': [False] * len(QUIZ_POOL), 'term_idx': 0,
        'bots': [], 'season_end_time': None, 'is_ended': False
    })

# --- 4. CSS: 토스 스타일 화이트 UI ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff; color: #000000; }}
    .metric-card {{ background: #f2f4f6; padding: 20px; border-radius: 16px; border: none; color: #191f28; }}
    .rank-card {{ background: #ffffff; padding: 15px; border-radius: 12px; border-bottom: 1px solid #f2f4f6; color: #191f28; font-weight: bold; }}
    .timer-box {{ background: #ff4d4f; color: white !important; padding: 15px; border-radius: 12px; text-align: center; font-weight: bold; font-size: 1.2rem; }}
    .profit {{ color: #ff4d4f; }} .loss {{ color: #3182f6; }}
    </style>
""", unsafe_allow_html=True)

# --- 5. 실시간 데이터 엔진 ---
@st.cache_data(ttl=10) # 10초마다 실제 시세 업데이트
def fetch_live_market(name):
    ticker = STOCK_MAP[name]
    try:
        df = yf.download(ticker, period="5d", interval="15m", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        raw_price = df['Close'].iloc[-1]
        # 실시간 변동성을 보여주기 위한 노이즈 추가
        raw_price *= (1 + (np.random.rand()-0.5)*0.002)
        
        krw = int(raw_price) if ".KS" in ticker else int(raw_price * EXCHANGE_RATE)
        usd = raw_price if ".KS" not in ticker else raw_price / EXCHANGE_RATE
        return krw, usd, df
    except: return 100000, 70, None

def init_bots(league):
    base = TIER_CFG[league]['seed']
    return [{"닉네임": n, "자산": base * (1 + (random.random()-0.5)*0.1)} for n in ["퀀트마스터", "익산불개미", "여의도황소", "나스닥귀신", "버핏지망생"]]

# --- 6. 토스 스타일 인터랙티브 차트 ---
def draw_toss_chart(df, name, ticker):
    chart_df = df.copy()
    # 가격 축 통일 (원화 기준)
    price_col = 'Close'
    y_vals = chart_df[price_col] * (EXCHANGE_RATE if ".KS" not in ticker else 1)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=chart_df.index, y=y_vals,
        mode='lines', line=dict(color='#3182f6', width=3),
        hovertemplate="<b>%{y:,.0f}원</b><extra></extra>",
        name=name
    ))
    
    # 최고/최저가 주석
    mx_val, mn_val = y_vals.max(), y_vals.min()
    fig.add_annotation(x=y_vals.idxmax(), y=mx_val, text=f"▲ {mx_val:,.0f}", showarrow=False, font=dict(color="#ff4d4f", size=12), yshift=10)
    fig.add_annotation(x=y_vals.idxmin(), y=mn_val, text=f"▼ {mn_val:,.0f}", showarrow=False, font=dict(color="#3182f6", size=12), yshift=-10)

    fig.update_layout(
        paper_bgcolor='white', plot_bgcolor='white', hovermode="x unified",
        xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#f2f4f6', tickformat=",.0f"),
        height=400, margin=dict(l=10, r=10, t=10, b=10)
    )
    return fig

# --- 7. 메인 로직 ---
if not st.session_state.user_name:
    st.title("🏆 AI 투자 서바이벌 시즌")
    with st.container(border=True):
        u_name = st.text_input("닉네임")
        u_tier = st.selectbox("리그 선택", ["초급", "중급", "고급"])
        if st.button("시즌 참가", use_container_width=True):
            if u_name:
                st.session_state.update({
                    'user_name': u_name, 'tier': u_tier, 'balance': TIER_CFG[u_tier]['seed'],
                    'bots': init_bots(u_tier), 'is_ended': False,
                    'season_end_time': datetime.now() + timedelta(minutes=5)
                })
                st.rerun()
    st.stop()

# [실시간 엔진 핵심] 모든 종목의 현재 가격을 먼저 가져옵니다.
live_prices_krw = {}; live_charts = {}
current_total_stock_val = 0
for s in STOCK_MAP:
    krw, _, df = fetch_live_market(s)
    live_prices_krw[s] = krw; live_charts[s] = df
    # 내가 보유한 수량만큼 실시간 가치 합산
    current_total_stock_val += st.session_state.portfolio.get(s, 0) * krw

# 💡 실시간 총 자산 = 현재 남은 현금 + (보유 주식 수 * 실시간 시세)
total_assets = st.session_state.balance + current_total_stock_val

# 타이머 계산
time_diff = st.session_state.season_end_time - datetime.now()
sec_left = max(0, time_diff.total_seconds())
if sec_left <= 0: st.session_state.is_ended = True

# 봇 자산도 실시간으로 요동치게 하여 랭킹에 활력을 줌
if not st.session_state.is_ended:
    for b in st.session_state.bots: b['자산'] *= (1 + (random.random()-0.5)*0.004)

# --- 화면 출력 ---
st.title(f"{st.session_state.equipped} {st.session_state.user_name}님의 라이브 대시보드")

col_metrics = st.columns(3)
with col_metrics[0]:
    st.markdown(f'<div class="metric-card">💰 실시간 총 자산<br><h2>{total_assets:,.0f}원</h2></div>', unsafe_allow_html=True)
with col_metrics[1]:
    st.markdown(f'<div class="metric-card">💵 가용 현금(잔고)<br><h2>{st.session_state.balance:,.0f}원</h2></div>', unsafe_allow_html=True)
with col_metrics[2]:
    if not st.session_state.is_ended:
        st.markdown(f'<div class="timer-box">⏳ 시즌 종료까지<br>{int(sec_left//60)}분 {int(sec_left%60)}초</div>', unsafe_allow_html=True)
    else: st.markdown('<div class="timer-box">🏁 시즌 종료</div>', unsafe_allow_html=True)

st.divider()

t_market, t_rank, t_info = st.tabs(["🛒 실시간 거래소", "🏆 리더보드", "📚 투자 가이드"])

with t_market:
    m_col, p_col = st.columns([1.8, 1.2])
    with m_col:
        target = st.selectbox("종목 선택", list(STOCK_MAP.keys()))
        df = live_charts[target]
        if df is not None:
            st.plotly_chart(draw_toss_chart(df, target, STOCK_MAP[target]), use_container_width=True)
        
        st.write(f"### {target} 현재가: **{live_prices_krw[target]:,.0f}원**")
        qty = st.number_input("거래 수량", min_value=1, value=1)
        b, s = st.columns(2)
        if b.button("매수", use_container_width=True, disabled=st.session_state.is_ended):
            if st.session_state.balance >= live_prices_krw[target] * qty:
                st.session_state.balance -= live_prices_krw[target] * qty
                st.session_state.portfolio[target] += qty
                st.rerun() # 자산 즉시 반영을 위한 리런
        if s.button("매도", use_container_width=True, disabled=st.session_state.is_ended):
            if st.session_state.portfolio[target] >= qty:
                st.session_state.balance += live_prices_krw[target] * qty
                st.session_state.portfolio[target] -= qty
                st.rerun()

    with p_col:
        st.subheader("내 포트폴리오")
        for s, q in st.session_state.portfolio.items():
            if q > 0:
                val = q * live_prices_krw[s]
                st.write(f"**{s}** {q}주 | 평가액: {val:,.0f}원")

with t_rank:
    st.subheader(f"🏆 {st.session_state.tier} 리그 실시간 랭킹")
    my_rank_data = {"닉네임": f"{st.session_state.user_name} ⭐", "자산": total_assets}
    all_ranks = sorted(st.session_state.bots + [my_rank_data], key=lambda x: x['자산'], reverse=True)
    
    for idx, p in enumerate(all_ranks):
        medal = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else f"{idx+1}위"
        st.markdown(f'<div class="rank-card">{medal} {p["닉네임"]} | 자산: {p["자산"]:,.0f}원</div>', unsafe_allow_html=True)

st.sidebar.divider()
st.sidebar.write(f"💎 보유 포인트: {st.session_state.points}P")
if st.sidebar.button("🔄 시스템 초기화"):
    for k in list(st.session_state.keys()): del st.session_state[k]
    st.rerun()

# 수학적 자산 모델 표기
st.latex(r"Asset_{total} = Cash_{balance} + \sum_{i=1}^{n} (Quantity_i \times MarketPrice_i)")
