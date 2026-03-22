import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import random
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. 페이지 설정 및 실시간 엔진 (1초 주기)
st.set_page_config(page_title="AI 실시간 퀀트 v45", layout="wide")
st_autorefresh(interval=1000, key="global_engine_v45")

# --- 2. 전역 데이터 설정 ---
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

TERMS_POOL = [
    {"t": "코스피(KOSPI)", "d": "한국 거래소의 종합주가지수."},
    {"t": "블루칩", "d": "안정성이 높은 대형 우량주."},
    {"t": "시가총액", "d": "기업의 전체 가치 (주가 × 주식수)."},
    {"t": "PER/PBR", "d": "이익 및 자산 대비 주가 수준 지표."},
    {"t": "공매도", "d": "주가 하락을 예상하고 빌려서 파는 전략."},
    {"t": "서킷브레이커", "d": "급락 시 매매를 일시 중단하는 제도."}
]

QUIZ_POOL = [
    {"q": "상승장을 상징하는 동물은?", "a": "황소(Bull)", "o": ["황소(Bull)", "곰(Bear)", "사자(Lion)"]},
    {"q": "기업 이익을 주주에게 현금으로 나눠주는 돈은?", "a": "배당금", "o": ["배당금", "이자", "상여금"]},
    {"q": "하락장을 상징하는 동물은?", "a": "곰(Bear)", "o": ["황소", "곰", "독수리"]}
]

EXCHANGE_RATE = 1425.0

# --- 3. 세션 상태 초기화 ---
if 'user_name' not in st.session_state:
    st.session_state.update({
        'user_name': "", 'tier': "초급", 'balance': 0.0, 'points': 0,
        'portfolio': {s: {'qty': 0, 'avg': 0} for s in STOCK_MAP}, 
        'quiz_cleared': [False] * len(QUIZ_POOL), 'term_idx': 0,
        'bots': [], 'season_end': None, 'is_ended': False, 'selected_period': "1일",
        'trade_count': 0, 'messages': []
    })

# --- 4. CSS: 토스 스타일 화이트 UI ---
css_style = """
    <style>
    .stApp { background-color: #ffffff; color: #191f28; }
    .metric-card { background: #f2f4f6; padding: 20px; border-radius: 16px; border: none; color: #191f28; }
    .rank-card { background: #ffffff; padding: 12px; border-bottom: 1px solid #f2f4f6; font-weight: bold; color: #191f28; }
    .trend-card { background: #f9fafb; padding: 10px; border-radius: 12px; margin-bottom: 6px; font-size: 0.8rem; border: 1px solid #e5e8eb; }
    .news-card { background: #ffffff; padding: 15px; border-radius: 12px; border: 1px solid #f2f4f6; margin-bottom: 10px; transition: 0.3s; }
    .news-card:hover { background: #f9fafb; border-color: #3182f6; }
    .timer-box { background: #ff4d4f; color: white !important; padding: 15px; border-radius: 12px; text-align: center; font-weight: bold; }
    .profit { color: #ff4d4f; } .loss { color: #3182f6; }
    </style>
"""
st.markdown(css_style, unsafe_allow_html=True)

# --- 5. 데이터 엔진 ---
@st.cache_data(ttl=10)
def fetch_market_data(name, period="1일"):
    p_map = {"1일": "1d", "1주": "5d", "1달": "1mo", "3달": "3mo", "1년": "1y", "5년": "5y", "전체": "10y"}
    i_map = {"1일": "5m", "1주": "30m", "1달": "60m", "3달": "1d", "1년": "1d", "5년": "1wk", "전체": "1mo"}
    try:
        data = yf.download(STOCK_MAP[name], period=p_map[period], interval=i_map[period], progress=False)
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
        curr = data['Close'].iloc[-1]
        chg = ((curr - data['Open'].iloc[0]) / data['Open'].iloc[0]) * 100
        vol = data['Volume'].iloc[-1]
        krw = int(curr) if ".KS" in STOCK_MAP[name] else int(curr * EXCHANGE_RATE)
        return {"price": krw, "change": chg, "vol": vol, "df": data}
    except: return None

@st.cache_data(ttl=300)
def fetch_stock_news(name):
    try:
        ticker = yf.Ticker(STOCK_MAP[name])
        return ticker.news[:6]
    except: return []

# --- 6. 토스 스타일 차트 ---
def draw_toss_chart(df, ticker, period):
    y_vals = df['Close'] * (EXCHANGE_RATE if ".KS" not in ticker else 1)
    v_vals = df['Volume']
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=df.index, y=y_vals, mode='lines', line=dict(color='#3182f6', width=3), hovertemplate="%{y:,.0f}원"), secondary_y=True)
    fig.add_trace(go.Bar(x=df.index, y=v_vals, marker_color='#e5e8eb', opacity=0.4), secondary_y=False)
    mx, mn = y_vals.max(), y_vals.min()
    fig.add_annotation(x=y_vals.idxmax(), y=mx, text=f"▲ {mx:,.0f}", showarrow=False, font=dict(color="#ff4d4f"), yshift=10, secondary_y=True)
    fig.add_annotation(x=y_vals.idxmin(), y=mn, text=f"▼ {mn:,.0f}", showarrow=False, font=dict(color="#3182f6"), yshift=-10, secondary_y=True)
    fig.update_layout(paper_bgcolor='white', plot_bgcolor='white', hovermode="x unified", showlegend=False,
                      xaxis=dict(showgrid=False, showticklabels=False if period=="1일" else True),
                      yaxis=dict(showgrid=False, range=[0, v_vals.max()*6]),
                      yaxis2=dict(showgrid=True, gridcolor='#f2f4f6', side='right', tickformat=",.0f"),
                      height=400, margin=dict(l=10, r=10, t=10, b=10))
    return fig

# --- 7. 로그인 ---
if not st.session_state.user_name:
    st.title("🏆 AI 투자 서바이벌: 시즌 6")
    col_u, col_t = st.columns(2)
    u_name = col_u.text_input("닉네임")
    u_tier = col_t.selectbox("리그 선택", ["초급", "중급", "고급"])
    if st.button("참가하기", use_container_width=True):
        if u_name:
            st.session_state.update({'user_name': u_name, 'tier': u_tier, 'balance': TIER_CFG[u_tier]['seed'],
                                    'bots': [{"닉네임": n, "자산": TIER_CFG[u_tier]['seed']*(1+(random.random()-0.5)*0.1)} for n in ["A봇", "B봇", "C봇"]],
                                    'season_end': datetime.now() + timedelta(minutes=10)})
            st.rerun()
    st.stop()

# --- 8. 실시간 연산 ---
market_snap = {}
for s in STOCK_MAP: market_snap[s] = fetch_market_data(s, period="1일")

total_stock_val = sum(st.session_state.portfolio[s]['qty'] * market_snap[s]['price'] for s in STOCK_MAP if market_snap[s])
total_assets = st.session_state.balance + total_stock_val

# 트렌드
valid_s = [s for s in STOCK_MAP if market_snap[s]]
sorted_gainers = sorted(valid_s, key=lambda x: market_snap[x]['change'], reverse=True)
sorted_losers = sorted(valid_s, key=lambda x: market_snap[x]['change'])
sorted_popular = sorted(valid_s, key=lambda x: market_snap[x]['vol'], reverse=True)

sec_left = max(0, (st.session_state.season_end - datetime.now()).total_seconds())
if sec_left <= 0: st.session_state.is_ended = True

# --- 9. 메인 네비게이션 ---
st.sidebar.title(f"🚀 {st.session_state.tier}")
page = st.sidebar.radio("🧭 메뉴", ["🏠 대시보드", "🛒 거래소", "📚 아카데미"])

if page == "🏠 대시보드":
    st.title(f"👋 {st.session_state.user_name}님")
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 실시간 총 자산", f"{total_assets:,.0f}원")
    c2.metric("💵 가용 현금", f"{st.session_state.balance:,.0f}원")
    c3.metric("💎 포인트", f"{st.session_state.points}P")
    st.divider()
    st.subheader("📊 자산 비중")
    labels = [s for s in STOCK_MAP if st.session_state.portfolio[s]['qty'] > 0] + ["현금"]
    values = [st.session_state.portfolio[s]['qty'] * market_snap[s]['price'] for s in STOCK_MAP if st.session_state.portfolio[s]['qty'] > 0] + [st.session_state.balance]
    st.plotly_chart(go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4, marker=dict(colors=['#3182f6', '#f2f4f6']))]), use_container_width=True)

elif page == "🛒 거래소":
    l_col, m_col, r_col = st.columns([1, 2.5, 1.2])
    
    with l_col: # 종목 선택 및 트렌드
        st.subheader("🛒 종목")
        target = st.selectbox("종목 선택", list(STOCK_MAP.keys()), label_visibility="collapsed")
        st.write("---")
        st.write("🔥 **실시간 트렌드**")
        t_tab = st.tabs(["🚀 상승", "📉 하락", "⭐ 인기"])
        with t_tab[0]:
            for s in sorted_gainers[:4]: st.markdown(f'<div class="trend-card">{s} <span class="profit" style="float:right;">{market_snap[s]["change"]:+.2f}%</span></div>', unsafe_allow_html=True)
        with t_tab[1]:
            for s in sorted_losers[:4]: st.markdown(f'<div class="trend-card">{s} <span class="loss" style="float:right;">{market_snap[s]["change"]:+.2f}%</span></div>', unsafe_allow_html=True)
        with t_tab[2]:
            for s in sorted_popular[:4]: st.markdown(f'<div class="trend-card">{s} <span style="float:right;color:#adb5bd;">{market_snap[s]["vol"]/10000:,.0f}만</span></div>', unsafe_allow_html=True)

    with m_col: # 차트 및 뉴스
        t_data = fetch_market_data(target, period=st.session_state.selected_period)
        if t_data:
            st.plotly_chart(draw_toss_chart(t_data['df'], STOCK_MAP[target], st.session_state.selected_period), use_container_width=True)
            st.session_state.selected_period = st.radio("기간 선택", ["1일", "1주", "1달", "3달", "1년", "5년", "전체"], horizontal=True, label_visibility="collapsed")
            
            p_now = t_data['price']
            st.write(f"### 현재가: **{p_now:,.0f}원**")
            qty = st.number_input("수량", min_value=1, value=1)
            b, s = st.columns(2)
            if b.button("매수", use_container_width=True, disabled=st.session_state.is_ended):
                if st.session_state.balance >= p_now * qty:
                    st.session_state.balance -= p_now * qty
                    st.session_state.portfolio[target]['qty'] += qty; st.rerun()
            if s.button("매도", use_container_width=True, disabled=st.session_state.is_ended):
                if st.session_state.portfolio[target]['qty'] >= qty:
                    st.session_state.balance += p_now * qty
                    st.session_state.portfolio[target]['qty'] -= qty; st.rerun()

            st.write("---")
            st.subheader(f"📰 {target} 실시간 뉴스")
            news = fetch_stock_news(target)
            for n in news:
                # 💡 [KeyError 해결 핵심] .get()을 사용하여 데이터가 없어도 에러 방지
                link = n.get('link', '#') 
                title = n.get('title', '제목 없음')
                pub = n.get('publisher', '정보 없음')
                st.markdown(f"""
                    <div class="news-card">
                        <a href="{link}" target="_blank" style="text-decoration:none; color:#191f28;">
                            <div style="font-size:0.9rem; font-weight:bold;">{title}</div>
                            <div style="font-size:0.75rem; color:#8b95a1; margin-top:5px;">{pub}</div>
                        </a>
                    </div>
                """, unsafe_allow_html=True)

    with r_col: # 랭킹
        st.markdown(f'<div class="timer-box">⏳ {int(sec_left//60)}분 {int(sec_left%60)}초 후 종료</div>', unsafe_allow_html=True)
        st.subheader("🏆 리그 랭킹")
        my_r = {"닉네임": f"{st.session_state.user_name} ⭐", "자산": total_assets}
        for b in st.session_state.bots: b['자산'] *= (1+(random.random()-0.5)*0.005)
        ranks = sorted(st.session_state.bots + [my_r], key=lambda x: x['자산'], reverse=True)
        for idx, p in enumerate(ranks):
            st.markdown(f'<div class="rank-card">{"🥇" if idx==0 else "🥈" if idx==1 else "🥉" if idx==2 else f"{idx+1}위"} {p["닉네임"]} <br> {p["자산"]:,.0f}원</div>', unsafe_allow_html=True)

elif page == "📚 아카데미":
    st.title("📚 주식 성장 아카데미")
    t1, t2 = st.tabs(["📖 용어 사전", "❓ 포인트 퀴즈"])
    with t1:
        st.subheader("💡 투자 필수 용어")
        start = st.session_state.term_idx
        for t in TERMS_POOL[start:start+5]:
            st.markdown(f'<div style="background:#f2f4f6;padding:15px;border-radius:12px;margin-bottom:10px;"><b>{t["t"]}</b>: {t["d"]}</div>', unsafe_allow_html=True)
        if st.button("🔄 다음 용어"):
            st.session_state.term_idx = (st.session_state.term_idx + 5) % len(TERMS_POOL); st.rerun()
    with t2:
        st.subheader("💎 포인트 퀴즈")
        for i, q in enumerate(QUIZ_POOL):
            if not st.session_state.quiz_cleared[i]:
                with st.container(border=True):
                    st.write(f"**Q{i+1}. {q['q']}**")
                    ans = st.radio("정답 선택", q['o'], key=f"ans_{i}")
                    if st.button(f"Q{i+1} 확인", key=f"btn_{i}"):
                        if ans == q['a']:
                            st.session_state.points += 100; st.session_state.quiz_cleared[i] = True; st.rerun()
            else: st.success(f"✅ Q{i+1} 완료")

st.sidebar.divider()
if st.sidebar.button("🔄 초기화"):
    for k in list(st.session_state.keys()): del st.session_state[k]
    st.rerun()
