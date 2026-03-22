import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import numpy as np
import random
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. 페이지 설정 및 실시간 틱 시스템
st.set_page_config(page_title="AI 실시간 투자 터미널 v26", layout="wide")

# 1초마다 앱을 자동 새로고침하여 타이머와 차트를 끊김 없이 갱신 (1000ms = 1초)
st_autorefresh(interval=1000, key="datarefresh")

# 사이드바 테마 및 환경 설정
st.sidebar.title("🎨 UI 환경 설정")
theme_choice = st.sidebar.radio("배경 테마 선택", ["라이트 모드", "다크 모드"])

if theme_choice == "다크 모드":
    bg, txt, card, border, plotly_template = "#0e1117", "#ffffff", "#1d2026", "#3d414a", "plotly_dark"
else:
    bg, txt, card, border, plotly_template = "#ffffff", "#000000", "#f8fafc", "#e2e8f0", "plotly_white"

# 가독성 강화 CSS (다크모드 완벽 대응)
st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg} !important; color: {txt} !important; }}
    h1, h2, h3, h4, p, span, div, label, .stMarkdown, .stTable {{ color: {txt} !important; }}
    .stMetric {{ background-color: {card} !important; padding: 15px; border-radius: 12px; border: 1px solid {border} !important; }}
    .rank-card {{ background-color: {card} !important; border-radius: 10px; padding: 12px; border: 1px solid {border} !important; margin-bottom: 8px; }}
    .timer-box {{ background-color: #ef4444; color: white !important; padding: 15px; border-radius: 12px; text-align: center; font-size: 1.4rem; font-weight: bold; margin-bottom: 15px; }}
    .term-box {{ background-color: {card} !important; padding: 15px; border-radius: 10px; border: 1px solid {border} !important; margin-bottom: 10px; }}
    .profit {{ color: #ef4444 !important; font-weight: bold; }}
    .loss {{ color: #3b82f6 !important; font-weight: bold; }}
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 세트 (주식 및 용어 사전)
stock_map = {
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "NVIDIA": "NVDA",
    "애플": "AAPL", "테슬라": "TSLA", "마이크로소프트": "MSFT", "아마존": "AMZN", "현대차": "005380.KS"
}

terms_pool = [
    {"t": "코스피(KOSPI)", "d": "한국 거래소에 상장된 종합주가지수."},
    {"t": "블루칩(Blue Chip)", "d": "수익성, 성장성, 안정성이 높은 대형 우량주."},
    {"t": "서킷브레이커", "d": "주가 급락 시 시장 안정을 위해 매매를 일시 중단하는 제도."},
    {"t": "배당금", "d": "기업의 이익 중 일부를 주주에게 나누어 주는 현금."},
    {"t": "시가총액", "d": "상장 주식수 × 현재 주가. 기업의 전체 몸값."},
    {"t": "PER(주가수익비율)", "d": "주가가 1주당 수익의 몇 배인지 나타내는 지표."},
    {"t": "PBR(주가순자산비율)", "d": "주가가 1주당 자산의 몇 배인지 나타내는 지표."},
    {"t": "예수금", "d": "주식을 사기 위해 계좌에 넣어둔 현금."},
    {"t": "익절", "d": "수익이 난 상태에서 주식을 팔아 이익을 확정하는 것."},
    {"t": "손절매", "d": "더 큰 손실을 막기 위해 현재 손해를 감수하고 파는 것."},
    {"t": "공매도", "d": "주가 하락을 예상하고 주식을 빌려서 파는 투자 기법."},
    {"t": "유상증자", "d": "기업이 자금을 조달하기 위해 새로 주식을 발행해 파는 것."},
    {"t": "보통주", "d": "주주총회에서 의결권을 가지는 일반적인 주식."},
    {"t": "우선주", "d": "의결권은 없지만 배당을 더 많이 받는 주식."},
    {"t": "공모주", "d": "기업이 상장할 때 일반인에게 청약을 받는 주식."}
]

# 3. 실시간 주가 및 차트 엔진 (연속형 차트 로직 추가)
@st.cache_data(ttl=20)
def fetch_robust_data(target_name):
    ticker = stock_map[target_name]
    try:
        df = yf.download(ticker, period="5d", interval="30m", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        if df.empty: return 100000, pd.DataFrame()
        
        current_p = df['Close'].iloc[-1]
        if ".KS" not in ticker: current_p *= 1410 # 실시간 환율 적용
        return int(current_p), df
    except:
        return 100000, pd.DataFrame()

# 4. 세션 상태 초기화
if 'user_name' not in st.session_state:
    st.session_state.update({
        'user_name': "", 'balance': 0.0,
        'portfolio': {s: {'qty': 0, 'avg_price': 0} for s in stock_map},
        'trade_log': [], 'bots': [], 'season_end_time': None, 'is_ended': False,
        'quiz_cleared': [False] * 3, 'term_idx': 0
    })

def init_bots(diff):
    names = ["퀀트마스터", "익산불개미", "여의도황소", "나스닥귀신", "버핏지망생", "단타의신", "월스트리트", "AI알고리즘", "풀매수전사"]
    base = {"초급": 50000000, "중급": 10000000, "상급": 1000000}[diff]
    return [{"닉네임": n, "자산": base * (1 + (random.random()-0.5)*0.2)} for n in names]

# 5. 로그인 화면
if not st.session_state.user_name:
    st.title("🏆 AI 투자 5분 시즌제 챌린지")
    with st.container(border=True):
        name = st.text_input("닉네임 입력")
        diff_choice = st.selectbox("참여 등급", ["초급 (5,000만)", "중급 (1,000만)", "상급 (100만)"])
        if st.button("시작"):
            if name:
                st.session_state.update({
                    'user_name': name, 'balance': 50000000.0 if "초급" in diff_choice else 10000000.0 if "중급" in diff_choice else 1000000.0,
                    'bots': init_bots(diff_choice.split()[0]),
                    'season_end_time': datetime.now() + timedelta(minutes=5)
                })
                st.rerun()
    st.stop()

# 6. 실시간 자산 및 타이머
time_left = st.session_state.season_end_time - datetime.now()
sec_left = max(0, time_left.total_seconds())
if sec_left <= 0: st.session_state.is_ended = True

live_prices = {}; live_charts = {}
total_stock_value = 0
for n in stock_map.keys():
    p, h = fetch_robust_data(n)
    live_prices[n] = p; live_charts[n] = h
    total_stock_value += st.session_state.portfolio[n]['qty'] * p

total_assets = st.session_state.balance + total_stock_value

# 7. 대시보드 출력
st.title(f"📈 {st.session_state.user_name}님 환영합니다!")
c1, c2 = st.columns(2)
c1.metric("💵 가용 현금", f"{st.session_state.balance:,.0f}원")
c2.metric("🏆 실시간 총 자산", f"{total_assets:,.0f}원")

st.divider()

# 8. 메인 탭
tab_market, tab_portfolio, tab_academy = st.tabs(["🛒 거래소 & 랭킹", "📂 자산 분석", "📚 주식 사전"])

with tab_market:
    m_col, r_col = st.columns([1.8, 1.2])
    with m_col:
        target = st.selectbox("종목 선택", list(stock_map.keys()))
        df = live_charts[target]
        
        # 📈 [버그 해결] 연속형 그래프 로직
        if not df.empty:
            # 캔들스틱 차트 생성
            fig = go.Figure(data=[go.Candlestick(
                x=df.index.strftime('%m/%d %H:%M'), # X축을 문자열로 변환하여 시간 공백 제거
                open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                increasing_line_color='#ef4444', decreasing_line_color='#3b82f6'
            )])
            
            # 그래프 레이아웃 설정
            fig.update_layout(
                title=f"📊 {target} 연속 시세 차트",
                template=plotly_template,
                xaxis_rangeslider_visible=False,
                xaxis_type='category', # 💡 [핵심] 카테고리 타입으로 설정하여 끊김 없이 연결
                height=450,
                margin=dict(l=10, r=10, t=40, b=10)
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # 수익률 및 매매 UI
        p_now = live_prices[target]; hold = st.session_state.portfolio[target]
        profit_pct = ((p_now - hold['avg_price']) / hold['avg_price'] * 100) if hold['qty'] > 0 else 0
        
        st.write(f"### 현재가: {p_now:,}원")
        if hold['qty'] > 0:
            color = "profit" if profit_pct > 0 else "loss"
            st.markdown(f"보유: **{hold['qty']}주** | 평단: **{hold['avg_price']:,.0f}원** | 수익률: <span class='{color}'>{profit_pct:.2f}%</span>", unsafe_allow_html=True)

        qty = st.number_input("수량 설정", min_value=1, value=1, disabled=st.session_state.is_ended)
        b_c, s_c = st.columns(2)
        if b_c.button(f"매수", key=f"buy_{target}", disabled=st.session_state.is_ended):
            if st.session_state.balance >= p_now * qty:
                new_qty = hold['qty'] + qty
                new_avg = ((hold['avg_price'] * hold['qty']) + (p_now * qty)) / new_qty
                st.session_state.balance -= p_now * qty
                st.session_state.portfolio[target] = {'qty': new_qty, 'avg_price': int(new_avg)}
                st.rerun()
        if s_c.button(f"매도", key=f"sell_{target}", disabled=st.session_state.is_ended):
            if hold['qty'] >= qty:
                st.session_state.balance += p_now * qty
                st.session_state.portfolio[target]['qty'] -= qty
                st.rerun()

    with r_col:
        if not st.session_state.is_ended:
            st.markdown(f'<div class="timer-box">⏳ 종료까지: {int(sec_left//60)}분 {int(sec_left%60)}초</div>', unsafe_allow_html=True)
        else: st.error("🏁 시즌 종료")
        st.subheader("🏆 시즌 랭킹")
        user_rank_data = {"닉네임": f"{st.session_state.user_name} ⭐", "자산": total_assets}
        all_p = sorted(st.session_state.bots + [user_rank_data], key=lambda x: x["자산"], reverse=True)
        for idx, p in enumerate(all_p):
            medal = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else f"{idx+1}위"
            st.markdown(f'<div class="rank-card">{medal} {p["닉네임"]} <br> {p["자산"]:,.0f}원</div>', unsafe_allow_html=True)

with tab_portfolio:
    if total_stock_value > 0:
        labels = [s for s in stock_map.keys() if st.session_state.portfolio[s]['qty'] > 0]
        values = [st.session_state.portfolio[s]['qty'] * live_prices[s] for s in labels]
        st.plotly_chart(go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)]))
    else: st.info("보유 주식이 없습니다.")

# 💡 [핵심 추가] 주식 용어 사전 탭
with tab_academy:
    st.header("📚 주식 용어 사전 (5개씩 순환)")
    st.write("버튼을 누르면 새로운 지식이 업데이트됩니다.")
    start = st.session_state.term_idx
    current_terms = terms_pool[start:start+5]
    for t in current_terms:
        st.markdown(f'<div class="term-box"><b>{t["t"]}</b>: {t["d"]}</div>', unsafe_allow_html=True)
    if st.button("🔄 다음 용어 보기"):
        st.session_state.term_idx = (st.session_state.term_idx + 5) % len(terms_pool)
        st.rerun()

st.divider()
if st.button("🔄 시스템 초기화"):
    for k in list(st.session_state.keys()): del st.session_state[k]
    st.rerun()
