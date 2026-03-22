import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import random
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. 시스템 설정 (1초 주기 틱)
st.set_page_config(page_title="AI 실시간 퀀트 v41", layout="wide")
st_autorefresh(interval=1000, key="live_market_tick")

# --- 2. 전역 데이터 풀 ---
STOCK_MAP = {
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "현대차": "005380.KS",
    "NVIDIA": "NVDA", "애플": "AAPL", "테슬라": "TSLA", "마이크로소프트": "MSFT",
    "아마존": "AMZN", "구글": "GOOGL", "메타": "META", "넷플릭스": "NFLX", "삼성SDI": "006400.KS"
}

TIER_CFG = {
    "초급": {"seed": 100000000, "pt_mul": 1.0, "limit": 500000, "next": "중급"},
    "중급": {"seed": 50000000, "pt_mul": 2.5, "limit": 200000, "next": "고급"},
    "고급": {"seed": 10000000, "pt_mul": 5.0, "limit": 50000, "next": "마스터"}
}

SHOP_ITEMS = {
    "초급": {"🎈 풍선": 50, "👓 연습용 안경": 150},
    "중급": {"💼 서류가방": 1000, "📱 최신 폰": 2500},
    "고급": {"👑 황금 왕관": 10000, "🏎️ 슈퍼카": 50000}
}

EXCHANGE_RATE = 1425.0

# --- 3. 세션 상태 초기화 ---
if 'user_name' not in st.session_state:
    st.session_state.update({
        'user_name': "", 'tier': "초급", 'balance': 0.0, 'points': 0,
        'portfolio': {s: {'qty': 0, 'avg': 0} for s in STOCK_MAP}, 
        'messages': [], 'inventory': [], 'equipped': "🥚",
        'daily_check': False, 'quiz_cleared': [False] * 3,
        'trade_count': 0, 'term_idx': 0, 'bots': [], 'season_end': None, 
        'is_ended': False, 'selected_period': "1일"
    })

# --- 4. CSS: 토스 스타일 화이트 UI ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff; color: #191f28; }}
    .metric-card {{ background: #f2f4f6; padding: 20px; border-radius: 16px; border: none; }}
    .rank-card {{ background: #ffffff; padding: 12px; border-bottom: 1px solid #f2f4f6; font-weight: bold; cursor: pointer; }}
    .profit {{ color: #ff4d4f; font-weight: bold; }} .loss {{ color: #3182f6; font-weight: bold; }}
    .vol-text {{ color: #adb5bd; font-size: 0.8rem; }}
    </style>
""", unsafe_allow_html=True)

# --- 5. 실시간 데이터 엔진 (거래량 포함) ---
@st.cache_data(ttl=5)
def fetch_real_live_data(name, period="1d"):
    interval_map = {"1일": "5m", "1주": "30m", "3달": "1d", "1년": "1d", "5년": "1wk", "전체": "1mo"}
    yf_period_map = {"1일": "1d", "1주": "5d", "3달": "3mo", "1년": "1y", "5년": "5y", "전체": "10y"}
    try:
        data = yf.download(STOCK_MAP[name], period=yf_period_map[period], interval=interval_map[period], progress=False)
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
        
        curr_p = data['Close'].iloc[-1]
        change_pct = ((curr_p - data['Open'].iloc[0]) / data['Open'].iloc[0]) * 100
        vol = data['Volume'].iloc[-1]
        
        krw = int(curr_p) if ".KS" in STOCK_MAP[name] else int(curr_p * EXCHANGE_RATE)
        return {"price": krw, "change": change_pct, "vol": vol, "df": data}
    except: return None

# --- 6. 토스 스타일 거래량 통합 차트 ---
def draw_toss_vol_chart(df, name, ticker, period):
    y_vals = df['Close'] * (EXCHANGE_RATE if ".KS" not in ticker else 1)
    v_vals = df['Volume']
    
    # 💡 보조 축을 사용해 하단에 거래량 막대 배치
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # 가격 라인
    fig.add_trace(go.Scatter(x=df.index, y=y_vals, mode='lines', line=dict(color='#3182f6', width=3),
                             hovertemplate="<b>%{y:,.0f}원</b><extra></extra>"), secondary_y=True)
    
    # 거래량 막대 (하단에 낮게 배치)
    fig.add_trace(go.Bar(x=df.index, y=v_vals, marker_color='#e5e8eb', opacity=0.5, 
                         hovertemplate="거래량: %{y:,.0f}<extra></extra>"), secondary_y=False)

    mx, mn = y_vals.max(), y_vals.min()
    fig.add_annotation(x=y_vals.idxmax(), y=mx, text=f"▲ {mx:,.0f}", showarrow=False, font=dict(color="#ff4d4f"), yshift=10, secondary_y=True)
    fig.add_annotation(x=y_vals.idxmin(), y=mn, text=f"▼ {mn:,.0f}", showarrow=False, font=dict(color="#3182f6"), yshift=-10, secondary_y=True)

    fig.update_layout(paper_bgcolor='white', plot_bgcolor='white', hovermode="x unified", showlegend=False,
                      xaxis=dict(showgrid=False, showticklabels=False if period=="1일" else True),
                      yaxis=dict(showgrid=False, showticklabels=False, range=[0, v_vals.max() * 5]), # 거래량을 하단으로 밀어냄
                      yaxis2=dict(showgrid=True, gridcolor='#f2f4f6', side='right', tickformat=",.0f"),
                      height=400, margin=dict(l=10, r=10, t=10, b=10))
    return fig

# --- 7. 로그인 화면 ---
if not st.session_state.user_name:
    st.title("🏆 AI 투자 서바이벌: 라이브 마켓")
    u_name = st.text_input("닉네임")
    u_tier = st.selectbox("리그 선택", ["초급", "중급", "고급"])
    if st.button("참가하기", use_container_width=True):
        if u_name:
            st.session_state.update({'user_name': u_name, 'tier': u_tier, 'balance': TIER_CFG[u_tier]['seed'],
                                    'bots': [{"닉네임": n, "자산": TIER_CFG[u_tier]['seed'] * (1+random.random()*0.1)} for n in ["A봇", "B봇", "C봇"]],
                                    'season_end': datetime.now() + timedelta(minutes=10)})
            st.rerun()
    st.stop()

# --- 8. 데이터 수집 및 랭킹 계산 ---
market_data = {}
for s in STOCK_MAP:
    market_data[s] = fetch_real_live_data(s, period="1일")

total_stock_val = sum(st.session_state.portfolio[s]['qty'] * market_data[s]['price'] for s in STOCK_MAP if market_data[s])
total_assets = st.session_state.balance + total_stock_val

# 랭킹 리스트 생성
sorted_gainers = sorted([s for s in STOCK_MAP if market_data[s]], key=lambda x: market_data[x]['change'], reverse=True)
sorted_losers = sorted([s for s in STOCK_MAP if market_data[s]], key=lambda x: market_data[x]['change'])
sorted_popular = sorted([s for s in STOCK_MAP if market_data[s]], key=lambda x: market_data[x]['vol'], reverse=True)

# --- 9. 메인 네비게이션 ---
st.sidebar.title(f"🚀 {st.session_state.tier} 리그")
page = st.sidebar.radio("🧭 메뉴", ["🏠 대시보드", "🛒 거래소 & 실시간 테마", "📚 아카데미"])

if page == "🏠 대시보드":
    st.title(f"📊 {st.session_state.user_name}님의 투자 비중")
    c1, c2 = st.columns([1, 1.2])
    with c1:
        st.markdown(f'<div class="metric-card">💰 실시간 총 자산<br><h3>{total_assets:,.0f}원</h3></div>', unsafe_allow_html=True)
        st.write("")
        st.markdown(f'<div class="metric-card">💵 가용 현금 비중<br><h3>{st.session_state.balance / total_assets * 100:.1f}%</h3></div>', unsafe_allow_html=True)
    with c2:
        # 비중 차트 (간략화)
        labels = [s for s in STOCK_MAP if st.session_state.portfolio[s]['qty'] > 0] + ["현금"]
        values = [st.session_state.portfolio[s]['qty'] * market_data[s]['price'] for s in STOCK_MAP if st.session_state.portfolio[s]['qty'] > 0] + [st.session_state.balance]
        fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4, marker=dict(colors=['#3182f6', '#f2f4f6']))])
        fig_pie.update_layout(showlegend=False, height=300, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_pie, use_container_width=True)

elif page == "🛒 거래소 & 실시간 테마":
    m_col, r_col = st.columns([1.8, 1.2])
    with m_col:
        target = st.selectbox("종목 선택", list(STOCK_MAP.keys()))
        period = st.radio("기간", ["1일", "1주", "3달", "1년", "5년", "전체"], horizontal=True, label_visibility="collapsed")
        
        # 💡 선택된 종목의 차트 로드 (거래량 포함)
        target_info = fetch_real_live_data(target, period=period)
        if target_info:
            st.plotly_chart(draw_toss_vol_chart(target_info['df'], target, STOCK_MAP[target], period), use_container_width=True)
            
            p_now = target_info['price']; chg = target_info['change']; vol = target_info['vol']
            st.write(f"### 현재가: **{p_now:,.0f}원** (<span class='{'profit' if chg > 0 else 'loss'}'>{chg:+.2f}%</span>)", unsafe_allow_html=True)
            st.markdown(f"<span class='vol-text'>거래량: {vol:,.0f}</span>", unsafe_allow_html=True)
            
            qty = st.number_input("수량", min_value=1, value=1)
            if st.button("매수", use_container_width=True):
                if st.session_state.balance >= p_now * qty:
                    hold = st.session_state.portfolio[target]
                    new_qty = hold['qty'] + qty
                    hold['avg'] = ((hold['avg'] * hold['qty']) + (p_now * qty)) / new_qty
                    st.session_state.balance -= p_now * qty
                    hold['qty'] = new_qty; st.rerun()

    with r_col:
        # 💡 [핵심 추가] 실시간 테마 랭킹
        st.subheader("🔥 실시간 랭킹")
        rank_tab = st.tabs(["🚀 급상승", "📉 급하락", "⭐ 인기(거래량)"])
        
        with rank_tab[0]: # 급상승
            for s in sorted_gainers[:5]:
                st.markdown(f'<div class="rank-card">{s} <span class="profit" style="float:right;">{market_data[s]["change"]:+.2f}%</span></div>', unsafe_allow_html=True)
        with rank_tab[1]: # 급하락
            for s in sorted_losers[:5]:
                st.markdown(f'<div class="rank-card">{s} <span class="loss" style="float:right;">{market_data[s]["change"]:+.2f}%</span></div>', unsafe_allow_html=True)
        with rank_tab[2]: # 인기
            for s in sorted_popular[:5]:
                st.markdown(f'<div class="rank-card">{s} <span class="vol-text" style="float:right;">{market_data[s]["vol"]:,.0f} vol</span></div>', unsafe_allow_html=True)

st.sidebar.divider()
if st.sidebar.button("🔄 초기화"):
    for k in list(st.session_state.keys()): del st.session_state[k]
    st.rerun()

st.latex(r"ROI = \frac{Price_{current} - Price_{average}}{Price_{average}} \times 100\%")
