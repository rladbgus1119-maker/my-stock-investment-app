import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import numpy as np
import random
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. 시스템 설정 및 실시간 틱 (1초 주기)
st.set_page_config(page_title="AI 퀀트 유니버스: 최종 통합본", layout="wide")
st_autorefresh(interval=1000, key="global_engine")

# --- 2. 전역 데이터 풀 (누락된 모든 콘텐츠 복구) ---
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

TERMS_POOL = [
    {"t": "코스피(KOSPI)", "d": "한국 거래소의 종합주가지수."},
    {"t": "블루칩", "d": "안정성이 높은 대형 우량주."},
    {"t": "배당금", "d": "기업 이익을 주주에게 나눠주는 현금."},
    {"t": "시가총액", "d": "기업의 전체 가치(주가 × 주식수)."},
    {"t": "PER", "d": "이익 대비 주가 수준."},
    {"t": "공매도", "d": "주가 하락을 예상하고 빌려서 파는 전략."},
    {"t": "서킷브레이커", "d": "급락 시 매매를 일시 중단하는 제도."},
    {"t": "익절/손절", "d": "이익 또는 손해를 확정 짓는 매도."},
    {"t": "예수금", "d": "거래를 위해 넣어둔 현금."},
    {"t": "보통주/우선주", "d": "의결권 여부에 따른 주식 분류."}
]

QUIZ_POOL = [
    {"q": "상승장을 상징하는 동물은?", "a": "황소", "o": ["황소", "곰", "독수리"]},
    {"q": "기업 이익을 주주에게 나눠주는 돈은?", "a": "배당", "o": ["배당", "이자", "상여"]},
    {"q": "하락장을 상징하는 동물은?", "a": "곰", "o": ["황소", "곰", "사자"]}
]

EXCHANGE_RATE = 1420.0

# --- 3. 세션 상태 초기화 (AttributeError 완전 방어) ---
if 'user_name' not in st.session_state:
    st.session_state.update({
        'user_name': "", 'tier': "초급", 'balance': 0.0, 'points': 0,
        'portfolio': {s: {'qty': 0, 'avg': 0} for s in STOCK_MAP}, 
        'trade_log': [], 'messages': [], 'inventory': [], 'equipped': "🥚",
        'daily_check': False, 'quiz_cleared': [False] * len(QUIZ_POOL),
        'trade_count': 0, 'tech_focus': 0, 'avatar_type': "🌱 투자 꿈나무",
        'term_idx': 0, 'bots': [], 'season_end': None, 'is_ended': False
    })

# --- 4. CSS: 토스 스타일 화이트 UI ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff; color: #191f28; }}
    .metric-card {{ background: #f2f4f6; padding: 20px; border-radius: 16px; border: none; color: #191f28; }}
    .rank-card {{ background: #ffffff; padding: 12px; border-radius: 10px; border-bottom: 1px solid #f2f4f6; color: #191f28; font-weight: bold; }}
    .timer-box {{ background: #ff4d4f; color: white !important; padding: 15px; border-radius: 12px; text-align: center; font-weight: bold; font-size: 1.2rem; }}
    .term-box {{ background: #f2f4f6; padding: 15px; border-radius: 12px; margin-bottom: 10px; color: #191f28; }}
    .profit {{ color: #ff4d4f; }} .loss {{ color: #3182f6; }}
    </style>
""", unsafe_allow_html=True)

# --- 5. 데이터 엔진 ---
@st.cache_data(ttl=20)
def fetch_live_data(name):
    try:
        df = yf.download(STOCK_MAP[name], period="5d", interval="30m", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        raw_price = df['Close'].iloc[-1]
        # 실시간 변동성 부여
        raw_price *= (1 + (np.random.rand()-0.5)*0.002)
        krw = int(raw_price) if ".KS" in STOCK_MAP[name] else int(raw_price * EXCHANGE_RATE)
        return krw, df
    except: return 100000, None

def init_bots(tier):
    base = TIER_CFG[tier]['seed']
    names = ["퀀트마스터", "익산불개미", "여의도황소", "나스닥귀신", "버핏지망생"]
    return [{"닉네임": n, "자산": base * (1 + (random.random()-0.5)*0.1)} for n in names]

# --- 6. 토스 스타일 차트 ---
def draw_toss_chart(df, name, ticker):
    y_vals = df['Close'] * (EXCHANGE_RATE if ".KS" not in ticker else 1)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=y_vals, mode='lines', line=dict(color='#3182f6', width=3), 
                             hovertemplate="<b>%{y:,.0f}원</b><extra></extra>"))
    mx, mn = y_vals.max(), y_vals.min()
    fig.add_annotation(x=y_vals.idxmax(), y=mx, text=f"▲ {mx:,.0f}", showarrow=False, font=dict(color="#ff4d4f"), yshift=10)
    fig.add_annotation(x=y_vals.idxmin(), y=mn, text=f"▼ {mn:,.0f}", showarrow=False, font=dict(color="#3182f6"), yshift=-10)
    fig.update_layout(paper_bgcolor='white', plot_bgcolor='white', hovermode="x unified",
                      xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#f2f4f6'),
                      height=400, margin=dict(l=10, r=10, t=10, b=10))
    return fig

# --- 7. 로그인 화면 ---
if not st.session_state.user_name:
    st.title("🏆 AI 투자 RPG: 5분 서바이벌")
    with st.container(border=True):
        u_name = st.text_input("닉네임")
        u_tier = st.selectbox("리그(난이도) 선택", ["초급", "중급", "고급"])
        if st.button("시작하기", use_container_width=True):
            if u_name:
                st.session_state.update({'user_name': u_name, 'tier': u_tier, 'balance': TIER_CFG[u_tier]['seed'],
                                        'bots': init_bots(u_tier), 'season_end': datetime.now() + timedelta(minutes=5)})
                st.rerun()
    st.stop()

# --- 8. 실시간 데이터 & 자산 계산 ---
live_prices = {}; live_charts = {}
total_stock_val = 0
for s in STOCK_MAP:
    p, h = fetch_live_data(s)
    live_prices[s] = p; live_charts[s] = h
    total_stock_val += st.session_state.portfolio[s]['qty'] * p

total_assets = st.session_state.balance + total_stock_val

# 파산 방지 지원금
if total_assets < TIER_CFG[st.session_state.tier]['limit']:
    st.session_state.balance += TIER_CFG[st.session_state.tier]['safe_net']
    st.warning("💸 파산 위기 지원금이 입금되었습니다!")

# 타이머
time_diff = st.session_state.season_end - datetime.now()
sec_left = max(0, time_diff.total_seconds())
if sec_left <= 0: st.session_state.is_ended = True

# 봇 자산 변동 (랭킹 실시간성)
if not st.session_state.is_ended:
    for b in st.session_state.bots: b['자산'] *= (1 + (random.random()-0.5)*0.005)

# --- 9. 메인 네비게이션 ---
st.sidebar.title(f"🚀 {st.session_state.tier} 리그")
st.sidebar.subheader(f"{st.session_state.equipped} {st.session_state.user_name}님")
page = st.sidebar.radio("🧭 메뉴", ["🏠 대시보드", "🛒 거래소 & 랭킹", "📚 아카데미", "🛍️ 상점/커뮤니티"])

if page == "🏠 대시보드":
    st.title(f"👋 {st.session_state.user_name}님 환영합니다!")
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 실시간 총 자산", f"{total_assets:,.0f}원")
    c2.metric("💵 가용 현금", f"{st.session_state.balance:,.0f}원")
    c3.metric("💎 포인트", f"{st.session_state.points}P")
    
    st.divider()
    if not st.session_state.daily_check:
        if st.button("📅 출석체크 (+50P)"):
            st.session_state.points += 50; st.session_state.daily_check = True; st.rerun()

elif page == "🛒 거래소 & 랭킹":
    m_col, r_col = st.columns([1.8, 1.2])
    with m_col:
        target = st.selectbox("종목 분석", list(STOCK_MAP.keys()))
        df = live_charts[target]
        if df is not None:
            st.plotly_chart(draw_toss_chart(df, target, STOCK_MAP[target]), use_container_width=True)
        
        # 수익률 표시
        p_now = live_prices[target]; hold = st.session_state.portfolio[target]
        roi = ((p_now - hold['avg']) / hold['avg'] * 100) if hold['qty'] > 0 else 0
        st.write(f"### 현재가: **{p_now:,}원** | 수익률: <span class='{'profit' if roi > 0 else 'loss'}'>{roi:.2f}%</span>", unsafe_allow_html=True)
        
        qty = st.number_input("수량", min_value=1, value=1)
        b, s = st.columns(2)
        if b.button("매수", use_container_width=True, disabled=st.session_state.is_ended):
            if st.session_state.balance >= p_now * qty:
                new_qty = hold['qty'] + qty
                hold['avg'] = ((hold['avg'] * hold['qty']) + (p_now * qty)) / new_qty
                st.session_state.balance -= p_now * qty
                hold['qty'] = new_qty
                st.session_state.trade_count += 1; st.rerun()
        if s.button("매도", use_container_width=True, disabled=st.session_state.is_ended):
            if hold['qty'] >= qty:
                st.session_state.balance += p_now * qty
                hold['qty'] -= qty; st.rerun()

    with r_col:
        if not st.session_state.is_ended:
            st.markdown(f'<div class="timer-box">⏳ 종료까지: {int(sec_left//60)}분 {int(sec_left%60)}초</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="timer-box">🏁 시즌 종료</div>', unsafe_allow_html=True)
        
        st.subheader("🏆 실시간 랭킹")
        my_r = {"닉네임": f"{st.session_state.user_name} ⭐", "자산": total_assets}
        ranks = sorted(st.session_state.bots + [my_r], key=lambda x: x['자산'], reverse=True)
        my_pos = 0
        for idx, p in enumerate(ranks):
            if "⭐" in p['닉네임']: my_pos = idx + 1
            st.markdown(f'<div class="rank-card">{"🥇" if idx==0 else "🥈" if idx==1 else "🥉" if idx==2 else f"{idx+1}위"} {p["닉네임"]} | {p["자산"]:,.0f}원</div>', unsafe_allow_html=True)
        
        if st.session_state.is_ended and my_pos <= 3:
            nt = TIER_CFG[st.session_state.tier]['next']
            if nt != "마스터" and st.button(f"🚀 {nt} 리그로 승급하기"):
                st.session_state.update({'tier': nt, 'balance': TIER_CFG[nt]['seed'], 'is_ended': False, 'season_end': datetime.now() + timedelta(minutes=5)}); st.rerun()

elif page == "📚 아카데미":
    t1, t2 = st.tabs(["📖 용어 사전", "❓ 퀴즈"])
    with t1:
        start = st.session_state.term_idx
        for t in TERMS_POOL[start:start+5]:
            st.markdown(f'<div class="term-box"><b>{t["t"]}</b>: {t["d"]}</div>', unsafe_allow_html=True)
        if st.button("🔄 다음 용어 보기"):
            st.session_state.term_idx = (st.session_state.term_idx + 5) % len(TERMS_POOL); st.rerun()
    with t2:
        for i, q in enumerate(QUIZ_POOL):
            if not st.session_state.quiz_cleared[i]:
                st.write(f"**Q{i+1}. {q['q']}**")
                ans = st.radio("정답 선택", q['o'], key=f"q_{i}")
                if st.button(f"제출", key=f"b_{i}"):
                    if ans == q['a']:
                        st.session_state.points += 100; st.session_state.quiz_cleared[i] = True; st.rerun()
            else: st.success(f"Q{i+1} 완료 ✅")

elif page == "🛍️ 상점/커뮤니티":
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🛍️ 상점")
        for tier, items in SHOP_ITEMS.items():
            st.write(f"[{tier}]")
            for name, price in items.items():
                locked = (tier == "고급" and st.session_state.tier != "고급") or (tier == "중급" and st.session_state.tier == "초급")
                if st.button(f"{name} ({price}P)", disabled=locked, key=f"s_{name}"):
                    if st.session_state.points >= price:
                        st.session_state.points -= price; st.session_state.inventory.append(name); st.rerun()
    with c2:
        st.subheader("💬 광장")
        st.markdown('<div class="chat-box">', unsafe_allow_html=True)
        for m in st.session_state.messages[-10:]: st.write(f"**{m['user']}**: {m['text']}")
        st.markdown('</div>', unsafe_allow_html=True)
        with st.form("chat", clear_on_submit=True):
            m = st.text_input("메시지"); 
            if st.form_submit_button("전송"): st.session_state.messages.append({"user": st.session_state.user_name, "text": m}); st.rerun()

st.sidebar.divider()
if st.sidebar.button("🔄 초기화"):
    for k in list(st.session_state.keys()): del st.session_state[k]
    st.rerun()
