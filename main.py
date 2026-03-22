import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import numpy as np
import random
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. 시스템 설정 및 실시간 마켓 엔진 (1초 주기)
st.set_page_config(page_title="초보자도 쉽게 할 수 있는 AI 투자 서비스", layout="wide")
st_autorefresh(interval=1000, key="live_market_tick")

# --- 2. 전역 설정 (실제 Ticker 매핑) ---
STOCK_MAP = {
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "현대차": "005380.KS",
    "NVIDIA": "NVDA", "애플": "AAPL", "테슬라": "TSLA", "마이크로소프트": "MSFT",
    "아마존": "AMZN", "구글": "GOOGL", "메타": "META", "넷플릭스": "NFLX", "삼성SDI": "006400.KS"
}

TIER_CFG = {
    "초급": {"seed": 100000000, "pt_mul": 1.0, "safe_net": 1000000, "limit": 500000, "next": "중급"},
    "중급": {"seed": 50000000, "pt_mul": 2.5, "safe_net": 500000, "limit": 200000, "next": "고급"},
    "고급": {"seed": 10000000, "pt_mul": 5.0, "safe_net": 100000, "limit": 50000, "next": "마스터"}
}

SHOP_ITEMS = {
    "초급": {"🎈 풍선": 50, "👓 연습용 안경": 150},
    "중급": {"💼 서류가방": 1000, "📱 최신 폰": 2500},
    "고급": {"👑 황금 왕관": 10000, "🏎️ 슈퍼카": 50000}
}

EXCHANGE_RATE = 1425.0 # 실제와 유사한 고정 환율 설정

# --- 3. 세션 상태 초기화 ---
if 'user_name' not in st.session_state:
    st.session_state.update({
        'user_name': "", 'tier': "초급", 'balance': 0.0, 'points': 0,
        'portfolio': {s: {'qty': 0, 'avg': 0} for s in STOCK_MAP}, 
        'trade_log': [], 'messages': [], 'inventory': [], 'equipped': "🥚",
        'daily_check': False, 'quiz_cleared': [False] * 3,
        'trade_count': 0, 'term_idx': 0, 'bots': [], 'season_end': None, 
        'is_ended': False, 'selected_period': "1일"
    })

# --- 4. CSS: 토스 스타일 미니멀리즘 ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff; color: #191f28; }}
    .metric-card {{ background: #f2f4f6; padding: 20px; border-radius: 16px; border: none; }}
    .rank-card {{ background: #ffffff; padding: 12px; border-bottom: 1px solid #f2f4f6; font-weight: bold; }}
    .timer-box {{ background: #ff4d4f; color: white !important; padding: 15px; border-radius: 12px; text-align: center; font-weight: bold; }}
    .profit {{ color: #ff4d4f; font-weight: bold; }} .loss {{ color: #3182f6; font-weight: bold; }}
    </style>
""", unsafe_allow_html=True)

# --- 5. [실시간 데이터 엔진] 실제 주가 동기화 ---
@st.cache_data(ttl=5) # 5초 캐싱으로 실제 데이터와 동일한 수준 유지
def fetch_real_market_data(name, period="1d"):
    interval_map = {"1일": "5m", "1주": "30m", "3달": "1d", "1년": "1d", "5년": "1wk", "전체": "1mo"}
    yf_period_map = {"1일": "1d", "1주": "5d", "3달": "3mo", "1년": "1y", "5년": "5y", "전체": "10y"}
    ticker = STOCK_MAP[name]
    try:
        data = yf.download(ticker, period=yf_period_map[period], interval=interval_map[period], progress=False)
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
        
        # 현재 실시간 가격 (종가 기준)
        current_p = data['Close'].iloc[-1]
        # 원화 변환 (국내 주식은 그대로, 해외 주식은 환율 적용)
        krw_price = int(current_p) if ".KS" in ticker else int(current_p * EXCHANGE_RATE)
        return krw_price, data
    except:
        return 100000, None

def init_bots(tier):
    base = TIER_CFG[tier]['seed']
    names = ["퀀트마스터", "익산불개미", "여의도황소", "나스닥귀신", "버핏지망생"]
    return [{"닉네임": n, "자산": base * (1 + (random.random()-0.5)*0.1)} for n in names]

# --- 6. 토스 스타일 기간별 차트 ---
def draw_toss_live_chart(df, name, ticker, period):
    y_vals = df['Close'] * (EXCHANGE_RATE if ".KS" not in ticker else 1)
    fig = go.Figure()
    
    hover_fmt = "%m-%d %H:%M" if period in ["1일", "1주"] else "%Y-%m-%d"
    
    fig.add_trace(go.Scatter(
        x=df.index, y=y_vals,
        mode='lines', line=dict(color='#3182f6', width=3),
        hovertemplate="<b>%{x|" + hover_fmt + "}</b><br>가격: %{y:,.0f}원<extra></extra>"
    ))
    
    # 토스 스타일의 최고/최저가 주석
    mx, mn = y_vals.max(), y_vals.min()
    fig.add_annotation(x=y_vals.idxmax(), y=mx, text=f"▲ {mx:,.0f}", showarrow=False, font=dict(color="#ff4d4f"))
    fig.add_annotation(x=y_vals.idxmin(), y=mn, text=f"▼ {mn:,.0f}", showarrow=False, font=dict(color="#3182f6"))

    fig.update_layout(
        paper_bgcolor='white', plot_bgcolor='white', hovermode="x unified",
        xaxis=dict(showgrid=False, showticklabels=False if period == "1일" else True,
                   type='date' if period != "1일" else 'category'),
        yaxis=dict(showgrid=True, gridcolor='#f2f4f6', side='right', tickformat=",.0f"),
        height=450, margin=dict(l=10, r=10, t=10, b=10)
    )
    return fig

# --- 7. 로그인 화면 ---
if not st.session_state.user_name:
    st.title("🏆 토스 라이브 투자 서바이벌")
    with st.container(border=True):
        u_name = st.text_input("닉네임")
        u_tier = st.selectbox("참여 리그 선택", ["초급", "중급", "고급"])
        if st.button("시작하기", use_container_width=True):
            if u_name:
                st.session_state.update({
                    'user_name': u_name, 'tier': u_tier, 'balance': TIER_CFG[u_tier]['seed'],
                    'bots': init_bots(u_tier), 'season_end': datetime.now() + timedelta(minutes=5)
                })
                st.rerun()
    st.stop()

# --- 8. 실시간 데이터 & 자산 요동 엔진 ---
live_prices = {}; live_charts = {}
current_stock_value = 0
for s in STOCK_MAP:
    # 실시간 현재가 (1일 기준 최신가)
    p, h = fetch_real_market_data(s, period="1일")
    live_prices[s] = p; live_charts[s] = h
    current_stock_value += st.session_state.portfolio[s]['qty'] * p

# 💡 실시간 총 자산 공식 적용
total_assets = st.session_state.balance + current_stock_value

# 타이머 및 시즌 상태
time_left = st.session_end = st.session_state.season_end - datetime.now()
sec_left = max(0, time_left.total_seconds())
if sec_left <= 0: st.session_state.is_ended = True

# --- 9. 메인 화면 ---
st.sidebar.title(f"🚀 {st.session_state.tier} 리그")
st.sidebar.subheader(f"{st.session_state.equipped} {st.session_state.user_name}님")
page = st.sidebar.radio("🧭 메뉴", ["🏠 대시보드", "🛒 거래소 & 랭킹", "📚 아카데미"])

if page == "🏠 대시보드":
    st.title("나의 실시간 투자 현황")
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 실시간 총 자산", f"{total_assets:,.0f}원")
    c2.metric("💵 가용 현금", f"{st.session_state.balance:,.0f}원")
    c3.metric("💎 포인트", f"{st.session_state.points}P")
    
    st.divider()
    st.subheader("📊 보유 종목 수익률")
    for s, data in st.session_state.portfolio.items():
        if data['qty'] > 0:
            cur_p = live_prices[s]
            roi = ((cur_p - data['avg']) / data['avg'] * 100)
            color = "profit" if roi > 0 else "loss"
            st.markdown(f"**{s}** {data['qty']}주 | 평단 {data['avg']:,.0f}원 | 수익률 <span class='{color}'>{roi:.2f}%</span>", unsafe_allow_html=True)

elif page == "🛒 거래소 & 랭킹":
    m_col, r_col = st.columns([1.8, 1.2])
    with m_col:
        target = st.selectbox("종목 분석", list(STOCK_MAP.keys()))
        period = st.radio("기간", ["1일", "1주", "3달", "1년", "5년", "전체"], horizontal=True, label_visibility="collapsed")
        
        # 선택된 기간 데이터 로드
        _, df_chart = fetch_real_market_data(target, period=period)
        if df_chart is not None:
            st.plotly_chart(draw_toss_live_chart(df_chart, target, STOCK_MAP[target], period), use_container_width=True)
        
        # 매매 UI
        p_now = live_prices[target]
        st.write(f"### 현재가: **{p_now:,.0f}원**")
        qty = st.number_input("거래 수량", min_value=1, value=1)
        b, s = st.columns(2)
        if b.button("매수", use_container_width=True, disabled=st.session_state.is_ended):
            if st.session_state.balance >= p_now * qty:
                # 평단가 업데이트
                hold = st.session_state.portfolio[target]
                new_qty = hold['qty'] + qty
                hold['avg'] = ((hold['avg'] * hold['qty']) + (p_now * qty)) / new_qty
                st.session_state.balance -= p_now * qty
                hold['qty'] = new_qty
                st.rerun()
        if s.button("매도", use_container_width=True, disabled=st.session_state.is_ended):
            if st.session_state.portfolio[target]['qty'] >= qty:
                st.session_state.balance += p_now * qty
                st.session_state.portfolio[target]['qty'] -= qty
                st.rerun()

    with r_col:
        if not st.session_state.is_ended:
            st.markdown(f'<div class="timer-box">⏳ 시즌 종료까지: {int(sec_left//60)}분 {int(sec_left%60)}초</div>', unsafe_allow_html=True)
        else: st.error("🏁 시즌 종료!")
        
        st.subheader("🏆 리더보드")
        my_data = {"닉네임": f"{st.session_state.user_name} ⭐", "자산": total_assets}
        # 봇들의 자산도 실제 주가 변동률에 따라 연동 (선택사항이나 여기선 랜덤 변동 유지)
        for b in st.session_state.bots: b['자산'] *= (1 + (random.random()-0.5)*0.003)
        ranks = sorted(st.session_state.bots + [my_data], key=lambda x: x['자산'], reverse=True)
        for idx, p in enumerate(ranks):
            medal = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else f"{idx+1}위"
            st.markdown(f'<div class="rank-card">{medal} {p["닉네임"]} | {p["자산"]:,.0f}원</div>', unsafe_allow_html=True)

st.sidebar.divider()
if st.sidebar.button("🔄 로그아웃/초기화"):
    for k in list(st.session_state.keys()): del st.session_state[k]
    st.rerun()
