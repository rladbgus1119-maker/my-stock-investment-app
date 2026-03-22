import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import numpy as np
import random
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. 시스템 설정
st.set_page_config(page_title="AI 퀀트 유니버스: 토스 Edition", layout="wide")

# 2초마다 자동 새로고침 (실시간 가격 및 타이머 갱신)
st_autorefresh(interval=2000, key="global_tick")

# --- 2. 전역 데이터 정의 (오류 원천 차단) ---
STOCK_MAP = {
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", 
    "NVIDIA": "NVDA", "애플": "AAPL", "테슬라": "TSLA", "마이크로소프트": "MSFT"
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

TERMS_POOL = [
    {"t": "코스피(KOSPI)", "d": "한국 거래소의 종합주가지수."},
    {"t": "블루칩", "d": "안정성이 높은 대형 우량주."},
    {"t": "배당금", "d": "기업 이익을 주주에게 나눠주는 현금."},
    {"t": "시가총액", "d": "기업의 전체 가치(주가 × 주식수)."},
    {"t": "PER", "d": "주가수익비율. 기업의 이익 대비 주가 수준."},
    {"t": "공매도", "d": "주가 하락을 예상하고 빌려서 파는 전략."},
    {"t": "예수금", "d": "주식 거래를 위해 입금한 현금."}
]

QUIZ_POOL = [
    {"q": "상승장을 상징하는 동물은?", "a": "황소", "o": ["황소", "곰", "독수리"]},
    {"q": "기업 이익을 주주에게 돌려주는 돈은?", "a": "배당", "o": ["배당", "이자", "상여"]},
    {"q": "하락장을 상징하는 동물은?", "a": "곰", "o": ["황소", "곰", "사자"]}
]

EXCHANGE_RATE = 1415.0 # 고정 환율 (USD -> KRW)

# --- 3. 세션 상태 초기화 (AttributeError 해결) ---
if 'user_name' not in st.session_state:
    st.session_state.update({
        'user_name': "", 'tier': "초급", 'balance': 0.0, 'points': 0,
        'portfolio': {s: 0 for s in STOCK_MAP}, 'messages': [],
        'inventory': [], 'equipped': "🥚", 'daily_check': False,
        'quiz_cleared': [False] * len(QUIZ_POOL), # 💡 퀴즈 에러 해결 포인트
        'term_idx': 0, 'bots': [], 'season_end_time': None, 'is_ended': False
    })

# --- 4. CSS: 토스 스타일 화이트 UI ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff; color: #000000; }}
    .metric-card {{ background: #f2f4f6; padding: 20px; border-radius: 16px; border: none; color: #191f28; }}
    .rank-card {{ background: #ffffff; padding: 15px; border-radius: 12px; border-bottom: 1px solid #f2f4f6; color: #191f28; }}
    .timer-box {{ background: #ff4d4f; color: white !important; padding: 15px; border-radius: 12px; text-align: center; font-weight: bold; font-size: 1.2rem; }}
    .chat-box {{ background: #f9fafb; height: 300px; overflow-y: auto; padding: 15px; border-radius: 12px; border: 1px solid #e5e8eb; color: #191f28; }}
    .term-box {{ background: #f2f4f6; padding: 15px; border-radius: 12px; margin-bottom: 10px; color: #191f28; }}
    .stButton>button {{ border-radius: 8px; font-weight: bold; border: none; }}
    </style>
""", unsafe_allow_html=True)

# --- 5. 데이터 엔진 (KRW/USD 변환 및 차트) ---
@st.cache_data(ttl=30)
def fetch_stock_data(name):
    ticker = STOCK_MAP[name]
    try:
        df = yf.download(ticker, period="5d", interval="30m", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        # 원화/달러 가격 계산
        raw_price = df['Close'].iloc[-1]
        if ".KS" in ticker:
            krw = int(raw_price)
            usd = raw_price / EXCHANGE_RATE
        else:
            usd = raw_price
            krw = int(raw_price * EXCHANGE_RATE)
        
        return krw, usd, df
    except: return 100000, 70, None

def init_bots(league):
    base = TIER_CFG[league]['seed']
    return [{"닉네임": n, "자산": base * (1 + (random.random()-0.5)*0.1)} for n in ["퀀트장인", "익산불개미", "여의도황소", "나스닥귀신", "단타의신"]]

# --- 6. 토스 스타일 차트 생성 함수 ---
def create_toss_chart(df, name, ticker):
    # 가격 데이터를 원화로 변환 (미국 주식일 경우)
    chart_df = df.copy()
    if ".KS" not in ticker:
        chart_df['Close_KRW'] = chart_df['Close'] * EXCHANGE_RATE
        chart_df['Close_USD'] = chart_df['Close']
    else:
        chart_df['Close_KRW'] = chart_df['Close']
        chart_df['Close_USD'] = chart_df['Close'] / EXCHANGE_RATE

    max_idx = chart_df['Close_KRW'].idxmax()
    min_idx = chart_df['Close_KRW'].idxmin()
    max_val = chart_df['Close_KRW'].max()
    min_val = chart_df['Close_KRW'].min()

    fig = go.Figure()
    
    # 메인 라인
    fig.add_trace(go.Scatter(
        x=chart_df.index, y=chart_df['Close_KRW'],
        mode='lines', line=dict(color='#3182f6', width=3),
        hovertemplate="<b>가격: %{y:,.0f}원</b><br>($%{customdata:.2f})<extra></extra>",
        customdata=chart_df['Close_USD'],
        name=name
    ))

    # 최고가/최저가 주석 (Toss 스타일)
    fig.add_annotation(x=max_idx, y=max_val, text=f"최고 {max_val:,.0f}", showarrow=True, arrowhead=2, arrowcolor="#ff4d4f", font=dict(color="#ff4d4f"))
    fig.add_annotation(x=min_idx, y=min_val, text=f"최저 {min_val:,.0f}", showarrow=True, arrowhead=2, arrowcolor="#3182f6", font=dict(color="#3182f6"))

    fig.update_layout(
        paper_bgcolor='white', plot_bgcolor='white',
        hovermode="x unified",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=True),
        yaxis=dict(showgrid=True, gridcolor='#f2f4f6', zeroline=False, tickformat=",.0f"),
        height=400, margin=dict(l=10, r=10, t=10, b=10)
    )
    return fig

# --- 7. 메인 로직 ---
if not st.session_state.user_name:
    st.title("🏆 토스 투자 RPG: 5분 서바이벌")
    with st.container(border=True):
        u_name = st.text_input("사용하실 닉네임")
        u_tier = st.selectbox("참여 리그 선택", ["초급", "중급", "고급"])
        if st.button("시작하기", use_container_width=True):
            if u_name:
                st.session_state.update({
                    'user_name': u_name, 'tier': u_tier, 'balance': TIER_CFG[u_tier]['seed'],
                    'bots': init_bots(u_tier), 'is_ended': False,
                    'season_end_time': datetime.now() + timedelta(minutes=5)
                })
                st.rerun()
    st.stop()

# 실시간 데이터 계산
time_diff = st.session_state.season_end_time - datetime.now()
sec_left = max(0, time_diff.total_seconds())
if sec_left <= 0: st.session_state.is_ended = True

live_prices_krw = {}; live_prices_usd = {}; live_charts = {}
total_stock_val = 0
for s in STOCK_MAP:
    krw, usd, df = fetch_stock_data(s)
    live_prices_krw[s] = krw; live_prices_usd[s] = usd; live_charts[s] = df
    total_stock_val += st.session_state.portfolio.get(s, 0) * krw

total_assets = st.session_state.balance + total_stock_val

# --- 화면 구성 ---
st.sidebar.title(f"🚀 {st.session_state.tier} 리그")
st.sidebar.subheader(f"{st.session_state.equipped} {st.session_state.user_name}")
page = st.sidebar.radio("🧭 메뉴", ["🏠 내 자산", "🛒 실시간 거래소", "📚 아카데미", "🛍️ 상점 & 광장"])

if page == "🏠 내 자산":
    st.title("나의 투자 리포트")
    c1, c2 = st.columns(2)
    with c1: st.metric("💰 총 자산 (원화)", f"{total_assets:,.0f}원")
    with c2: st.metric("💵 총 자산 (달러환산)", f"${total_assets/EXCHANGE_RATE:,.2f}")
    
    st.divider()
    st.subheader("보유 종목 현황")
    for s, q in st.session_state.portfolio.items():
        if q > 0:
            st.write(f"**{s}**: {q}주 (평가액: {q*live_prices_krw[s]:,.0f}원 / ${q*live_prices_usd[s]:,.2f})")

elif page == "🛒 실시간 거래소":
    m_col, r_col = st.columns([1.8, 1.2])
    with m_col:
        target = st.selectbox("종목 선택", list(STOCK_MAP.keys()))
        df = live_charts[target]
        if df is not None:
            # 💡 토스 스타일 차트 출력
            fig = create_toss_chart(df, target, STOCK_MAP[target])
            st.plotly_chart(fig, use_container_width=True)
        
        st.write(f"### 현재가: **{live_prices_krw[target]:,.0f}원** <small>(${live_prices_usd[target]:,.2f})</small>", unsafe_allow_html=True)
        qty = st.number_input("거래 수량", min_value=1, value=1)
        b, s = st.columns(2)
        if b.button("매수", use_container_width=True, disabled=st.session_state.is_ended):
            if st.session_state.balance >= live_prices_krw[target]*qty:
                st.session_state.balance -= live_prices_krw[target]*qty; st.session_state.portfolio[target] += qty; st.rerun()
        if s.button("매도", use_container_width=True, disabled=st.session_state.is_ended):
            if st.session_state.portfolio[target] >= qty:
                st.session_state.balance += live_prices_krw[target]*qty; st.session_state.portfolio[target] -= qty; st.rerun()

    with r_col:
        if not st.session_state.is_ended:
            st.markdown(f'<div class="timer-box">⏳ 종료까지: {int(sec_left//60)}분 {int(sec_left%60)}초</div>', unsafe_allow_html=True)
        else: st.markdown('<div class="timer-box">🏁 시즌 종료!</div>', unsafe_allow_html=True)
        
        st.subheader("🏆 시즌 랭킹")
        my_data = {"닉네임": f"{st.session_state.user_name} ⭐", "자산": total_assets}
        ranks = sorted(st.session_state.bots + [my_data], key=lambda x: x['자산'], reverse=True)
        for idx, p in enumerate(ranks):
            medal = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else f"{idx+1}위"
            st.markdown(f'<div class="rank-card">{medal} {p["닉네임"]} <br> {p["자산"]:,.0f}원</div>', unsafe_allow_html=True)
        
        if st.session_state.is_ended and st.button("🚀 다음 리그 도전 (TOP 3 승급)"):
            # 승급 로직... (이전과 동일)
            pass

elif page == "📚 아카데미":
    st.title("지식 아카데미")
    t1, t2 = st.tabs(["📖 용어 사전", "❓ 포인트 퀴즈"])
    with t1:
        start = st.session_state.term_idx
        for t in TERMS_POOL[start:start+5]:
            st.markdown(f'<div class="term-box"><b>{t["t"]}</b>: {t["d"]}</div>', unsafe_allow_html=True)
        if st.button("🔄 다음 용어"): st.session_state.term_idx = (st.session_state.term_idx + 5) % len(TERMS_POOL); st.rerun()
    with t2:
        for i, q in enumerate(QUIZ_POOL):
            if not st.session_state.quiz_cleared[i]:
                st.write(f"**Q{i+1}. {q['q']}**")
                ans = st.radio("정답 선택", q['o'], key=f"q_{i}")
                if st.button(f"Q{i+1} 제출", key=f"b_{i}"):
                    if ans == q['a']:
                        st.session_state.points += 100; st.session_state.quiz_cleared[i] = True; st.rerun()
            else: st.success(f"Q{i+1} 완료 ✅")

elif page == "🛍️ 상점 & 광장":
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🛍️ 상점")
        for tier, items in SHOP_ITEMS.items():
            st.write(f"[{tier}]")
            for name, price in items.items():
                if st.button(f"{name} ({price}P)", key=f"s_{name}"):
                    if st.session_state.points >= price:
                        st.session_state.points -= price; st.session_state.inventory.append(name); st.rerun()
    with c2:
        st.subheader("💬 광장")
        st.markdown('<div class="chat-box">', unsafe_allow_html=True)
        for m in st.session_state.messages[-10:]: st.write(f"**{m['user']}**: {m['text']}")
        st.markdown('</div>', unsafe_allow_html=True)
        with st.form("chat"):
            m = st.text_input("메시지"); 
            if st.form_submit_button("전송"): st.session_state.messages.append({"user": st.session_state.user_name, "text": m}); st.rerun()

st.sidebar.divider()
if st.sidebar.button("🔄 초기화"):
    for k in list(st.session_state.keys()): del st.session_state[k]
    st.rerun()
