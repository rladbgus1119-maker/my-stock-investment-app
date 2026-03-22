import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import numpy as np
import random
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. 시스템 설정 및 실시간 마켓 엔진 (1초 주기)
st.set_page_config(page_title="AI 실시간 퀀트: 아카데미 에디션", layout="wide")
st_autorefresh(interval=1000, key="live_market_tick")

# --- 2. 전역 데이터 풀 (용어 사전 및 퀴즈 대폭 확충) ---
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
    {"t": "코스피(KOSPI)", "d": "한국 거래소의 종합주가지수. 한국 경제의 온도계라고 불립니다."},
    {"t": "블루칩(Blue Chip)", "d": "오랜 기간 안정적인 이익을 내고 배당을 주는 대형 우량주."},
    {"t": "시가총액", "d": "기업의 전체 가치. (현재 주가 × 발행 주식 총수)"},
    {"t": "PER(주가수익비율)", "d": "주가가 1주당 순이익의 몇 배인지 나타내는 지표. 낮을수록 저평가."},
    {"t": "PBR(주가순자산비율)", "d": "주가가 순자산에 비해 1배보다 낮으면 청산가치보다 낮다는 뜻."},
    {"t": "공매도", "d": "주가 하락을 예상하고 주식을 빌려서 파는 전략. 떨어져야 돈을 법니다."},
    {"t": "서킷브레이커", "d": "주가가 너무 급격히 변할 때 시장을 진정시키기 위해 매매를 일시 중단함."},
    {"t": "예수금", "d": "주식을 사기 위해 증권 계좌에 입금해 놓은 현금."},
    {"t": "익절/손절", "d": "수익을 확정 짓는 것을 익절, 손해를 감수하고 파는 것을 손절이라고 함."},
    {"t": "배당락", "d": "배당을 받을 권리가 사라지는 날. 보통 주가가 배당만큼 하락함."}
]

QUIZ_POOL = [
    {"q": "주식 시장에서 '상승장'을 상징하며, 뿔을 위로 치켜드는 동물은?", "a": "황소(Bull)", "o": ["황소(Bull)", "곰(Bear)", "독수리(Eagle)"]},
    {"q": "기업이 벌어들인 이익의 일부를 주주들에게 현금으로 나누어 주는 것은?", "a": "배당금", "o": ["배당금", "이자", "상여금"]},
    {"q": "상장 주식수와 현재 주가를 곱한 것으로, 기업의 전체 몸값을 뜻하는 말은?", "a": "시가총액", "o": ["시가총액", "매출액", "자본금"]}
]

EXCHANGE_RATE = 1425.0

# --- 3. 세션 상태 초기화 (AttributeError 완전 방어) ---
if 'user_name' not in st.session_state:
    st.session_state.update({
        'user_name': "", 'tier': "초급", 'balance': 0.0, 'points': 0,
        'portfolio': {s: {'qty': 0, 'avg': 0} for s in STOCK_MAP}, 
        'trade_log': [], 'messages': [], 'inventory': [], 'equipped': "🥚",
        'daily_check': False, 'quiz_cleared': [False] * len(QUIZ_POOL), # 💡 퀴즈 초기화
        'trade_count': 0, 'term_idx': 0, 'bots': [], 'season_end': None, 
        'is_ended': False, 'selected_period': "1일"
    })

# --- 4. CSS: 토스 스타일 화이트 UI ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff; color: #191f28; }}
    .metric-card {{ background: #f2f4f6; padding: 20px; border-radius: 16px; border: none; color: #191f28; }}
    .rank-card {{ background: #ffffff; padding: 12px; border-bottom: 1px solid #f2f4f6; font-weight: bold; color: #191f28; }}
    .term-box {{ background: #f2f4f6; padding: 18px; border-radius: 14px; margin-bottom: 12px; border-left: 6px solid #3182f6; }}
    .quiz-card {{ background: #ffffff; padding: 20px; border-radius: 16px; border: 1px solid #e5e8eb; margin-bottom: 15px; }}
    .profit {{ color: #ff4d4f; font-weight: bold; }} .loss {{ color: #3182f6; font-weight: bold; }}
    </style>
""", unsafe_allow_html=True)

# --- 5. 실시간 데이터 엔진 ---
@st.cache_data(ttl=5)
def fetch_real_data(name, period="1d"):
    interval_map = {"1일": "5m", "1주": "30m", "3달": "1d", "1년": "1d", "5년": "1wk", "전체": "1mo"}
    yf_period_map = {"1일": "1d", "1주": "5d", "3달": "3mo", "1년": "1y", "5년": "5y", "전체": "10y"}
    ticker = STOCK_MAP[name]
    try:
        data = yf.download(ticker, period=yf_period_map[period], interval=interval_map[period], progress=False)
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
        curr = int(data['Close'].iloc[-1]) if ".KS" in ticker else int(data['Close'].iloc[-1] * EXCHANGE_RATE)
        return curr, data
    except: return 100000, None

# --- 6. 토스 스타일 차트 ---
def draw_toss_chart(df, name, ticker, period):
    y_vals = df['Close'] * (EXCHANGE_RATE if ".KS" not in ticker else 1)
    fig = go.Figure()
    hover_fmt = "%m-%d %H:%M" if period in ["1일", "1주"] else "%Y-%m-%d"
    fig.add_trace(go.Scatter(x=df.index, y=y_vals, mode='lines', line=dict(color='#3182f6', width=3),
                             hovertemplate="<b>%{x|" + hover_fmt + "}</b><br>가격: %{y:,.0f}원<extra></extra>"))
    mx, mn = y_vals.max(), y_vals.min()
    fig.add_annotation(x=y_vals.idxmax(), y=mx, text=f"▲ {mx:,.0f}", showarrow=False, font=dict(color="#ff4d4f"))
    fig.add_annotation(x=y_vals.idxmin(), y=mn, text=f"▼ {mn:,.0f}", showarrow=False, font=dict(color="#3182f6"))
    fig.update_layout(paper_bgcolor='white', plot_bgcolor='white', hovermode="x unified",
                      xaxis=dict(showgrid=False, showticklabels=False if period=="1일" else True),
                      yaxis=dict(showgrid=True, gridcolor='#f2f4f6', side='right', tickformat=",.0f"),
                      height=400, margin=dict(l=10, r=10, t=10, b=10))
    return fig

# --- 7. 로그인 화면 ---
if not st.session_state.user_name:
    st.title("🏆 AI 투자 서바이벌: 토스 라이브")
    with st.container(border=True):
        u_name = st.text_input("닉네임")
        u_tier = st.selectbox("리그 선택 (초급: 1억 / 중급: 5천만 / 고급: 1천만)", ["초급", "중급", "고급"])
        if st.button("참가하기", use_container_width=True):
            if u_name:
                st.session_state.update({'user_name': u_name, 'tier': u_tier, 'balance': TIER_CFG[u_tier]['seed'],
                                        'bots': [{"닉네임": n, "자산": TIER_CFG[u_tier]['seed'] * (1 + (random.random()-0.5)*0.1)} for n in ["퀀트마", "익산불개", "여의도소", "나스닥신", "버핏지망"]],
                                        'season_end': datetime.now() + timedelta(minutes=5)})
                st.rerun()
    st.stop()

# --- 8. 실시간 자산 동기화 로직 ---
live_prices = {}; total_stock_val = 0
for s in STOCK_MAP:
    p, _ = fetch_real_data(s, period="1일")
    live_prices[s] = p
    total_stock_val += st.session_state.portfolio[s]['qty'] * p

# 💡 실시간 총 자산 = 현금 + 보유주식의 실제 실시간 가치
total_assets = st.session_state.balance + total_stock_val

# 타이머
time_diff = st.session_state.season_end - datetime.now()
sec_left = max(0, time_diff.total_seconds())
if sec_left <= 0: st.session_state.is_ended = True

# --- 9. 메인 화면 네비게이션 ---
st.sidebar.title(f"🚀 {st.session_state.tier} 리그")
st.sidebar.subheader(f"{st.session_state.equipped} {st.session_state.user_name}님")
page = st.sidebar.radio("🧭 메뉴 이동", ["🏠 대시보드", "🛒 거래소 & 랭킹", "📚 아카데미(지식)"])

if page == "🏠 대시보드":
    st.title(f"👋 {st.session_state.user_name}님, 오늘의 투자 현황")
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 실시간 총 자산", f"{total_assets:,.0f}원")
    c2.metric("💵 가용 현금", f"{st.session_state.balance:,.0f}원")
    c3.metric("💎 포인트", f"{st.session_state.points}P")
    
    st.divider()
    if total_assets < TIER_CFG[st.session_state.tier]['limit']:
        st.warning("💸 파산 위기! 긴급 자금 100만 원을 지원받으세요.")
        if st.button("지원금 받기"):
            st.session_state.balance += 1000000; st.rerun()

elif page == "🛒 거래소 & 랭킹":
    m_col, r_col = st.columns([1.8, 1.2])
    with m_col:
        target = st.selectbox("종목 선택", list(STOCK_MAP.keys()))
        period = st.radio("기간", ["1일", "1주", "3달", "1년", "5년", "전체"], horizontal=True, label_visibility="collapsed")
        _, df_chart = fetch_real_data(target, period=period)
        if df_chart is not None:
            st.plotly_chart(draw_toss_chart(df_chart, target, STOCK_MAP[target], period), use_container_width=True)
        
        p_now = live_prices[target]; hold = st.session_state.portfolio[target]
        st.write(f"### 현재가: **{p_now:,.0f}원**")
        qty = st.number_input("거래 수량", min_value=1, value=1)
        b, s = st.columns(2)
        if b.button("매수", use_container_width=True, disabled=st.session_state.is_ended):
            if st.session_state.balance >= p_now * qty:
                new_qty = hold['qty'] + qty
                hold['avg'] = ((hold['avg'] * hold['qty']) + (p_now * qty)) / new_qty
                st.session_state.balance -= p_now * qty
                hold['qty'] = new_qty; st.rerun()
        if s.button("매도", use_container_width=True, disabled=st.session_state.is_ended):
            if hold['qty'] >= qty:
                st.session_state.balance += p_now * qty
                hold['qty'] -= qty; st.rerun()

    with r_col:
        st.markdown(f'<div style="background:#ff4d4f;color:white;padding:15px;border-radius:12px;text-align:center;font-weight:bold;">⏳ 시즌 종료까지: {int(sec_left//60)}분 {int(sec_left%60)}초</div>', unsafe_allow_html=True)
        st.subheader("🏆 실시간 리더보드")
        my_r = {"닉네임": f"{st.session_state.user_name} ⭐", "자산": total_assets}
        for b in st.session_state.bots: b['자산'] *= (1 + (random.random()-0.5)*0.003)
        ranks = sorted(st.session_state.bots + [my_r], key=lambda x: x['자산'], reverse=True)
        for idx, p in enumerate(ranks):
            st.markdown(f'<div class="rank-card">{"🥇" if idx==0 else "🥈" if idx==1 else "🥉" if idx==2 else f"{idx+1}위"} {p["닉네임"]} | {p["자산"]:,.0f}원</div>', unsafe_allow_html=True)

# --- 💡 [핵심] 아카데미 메뉴 콘텐츠 강화 ---
elif page == "📚 아카데미(지식)":
    st.title("📚 투자 지식 아카데미")
    t1, t2 = st.tabs(["📖 핵심 용어 사전", "❓ 포인트 퀴즈"])
    
    with t1:
        st.subheader("💡 꼭 알아야 할 주식 용어 (5개씩 순환)")
        start = st.session_state.term_idx
        current_terms = TERMS_POOL[start:start+5]
        for t in current_terms:
            st.markdown(f'<div class="term-box"><b>{t["t"]}</b><br>{t["d"]}</div>', unsafe_allow_html=True)
        if st.button("🔄 다음 용어 보기"):
            st.session_state.term_idx = (st.session_state.term_idx + 5) % len(TERMS_POOL); st.rerun()

    with t2:
        st.subheader("💎 퀴즈 풀고 시드머니 벌기")
        st.info("퀴즈를 맞힐 때마다 100포인트가 지급됩니다!")
        for i, q in enumerate(QUIZ_POOL):
            if not st.session_state.quiz_cleared[i]:
                with st.container(border=True):
                    st.markdown(f"**Q{i+1}. {q['q']}**")
                    ans = st.radio("정답을 골라주세요", q['o'], key=f"ans_{i}")
                    if st.button(f"Q{i+1} 정답 확인", key=f"btn_{i}"):
                        if ans == q['a']:
                            st.session_state.points += 100
                            st.session_state.quiz_cleared[i] = True
                            st.success("🎉 정답입니다! 100포인트 획득!")
                            st.rerun()
                        else: st.error("다시 생각해보세요!")
            else:
                st.success(f"✅ Q{i+1} 문제를 이미 해결했습니다!")

st.sidebar.divider()
if st.sidebar.button("🔄 로그아웃/초기화"):
    for k in list(st.session_state.keys()): del st.session_state[k]
    st.rerun()
