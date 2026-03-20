import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import numpy as np
import random
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. 페이지 설정 및 실시간 틱(Tick) 시스템
st.set_page_config(page_title="AI 실시간 투자 터미널 v23", layout="wide")

# 2초마다 화면을 자동으로 새로고침하여 타이머와 수익률을 갱신함
st_autorefresh(interval=2000, key="datarefresh")

# 사이드바 테마 설정
st.sidebar.title("🎨 UI 환경 설정")
theme_choice = st.sidebar.radio("배경 테마 선택", ["라이트 모드", "다크 모드"])

if theme_choice == "다크 모드":
    bg, txt, card, border, plotly_template = "#0e1117", "#ffffff", "#1d2026", "#3d414a", "plotly_dark"
else:
    bg, txt, card, border, plotly_template = "#ffffff", "#000000", "#f8fafc", "#e2e8f0", "plotly_white"

# 가독성 강화 CSS
st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg} !important; color: {txt} !important; }}
    h1, h2, h3, h4, p, span, div, label, .stMarkdown, .stTable {{ color: {txt} !important; }}
    [data-testid="stWidgetLabel"] p {{ color: {txt} !important; font-weight: bold; }}
    .stMetric {{ background-color: {card} !important; padding: 15px; border-radius: 12px; border: 1px solid {border} !important; }}
    .rank-card {{ background-color: {card} !important; border-radius: 10px; padding: 12px; border: 1px solid {border} !important; margin-bottom: 8px; }}
    .timer-box {{ background-color: #ef4444; color: white !important; padding: 15px; border-radius: 12px; text-align: center; font-size: 1.4rem; font-weight: bold; margin-bottom: 15px; }}
    .profit {{ color: #ef4444 !important; font-weight: bold; }} /* 한국식 상승: 빨강 */
    .loss {{ color: #3b82f6 !important; font-weight: bold; }}   /* 한국식 하락: 파랑 */
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 세트 (순수 주식 콘텐츠)
stock_map = {
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "NVIDIA": "NVDA",
    "애플": "AAPL", "테슬라": "TSLA", "아마존": "AMZN", "현대차": "005380.KS"
}

quiz_pool = [
    {"q": "주식 시장에서 '상승장'을 의미하는 동물은?", "a": "황소(Bull)", "o": ["황소(Bull)", "곰(Bear)", "사자(Lion)"]},
    {"q": "상장 주식수 x 주가는?", "a": "시가총액", "o": ["매출액", "시가총액", "순이익"]}
]

# 3. 실시간 주가 및 그래프 엔진 (v23.0 강력한 구조 보강)
@st.cache_data(ttl=20)
def fetch_robust_data(target_name):
    ticker = stock_map[target_name]
    try:
        # 최근 1개월, 60분 단위 데이터를 가져옴
        df = yf.download(ticker, period="1mo", interval="60m", progress=False)
        
        # 💡 [핵심 해결책] yfinance v0.2.x의 다중 인덱스 컬럼을 단일 컬럼으로 강제 변환
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        if df.empty: return 100000, pd.DataFrame()
        
        current_p = df['Close'].iloc[-1]
        if ".KS" not in ticker: current_p *= 1410 # 실시간 환율 보정
        
        return int(current_p), df
    except:
        return 100000, pd.DataFrame()

# 4. 세션 상태 초기화 (수익률 계산 로직 포함)
if 'user_name' not in st.session_state:
    st.session_state.update({
        'user_name': "", 'balance': 0.0,
        # 포트폴리오 구조: {종목명: {'qty': 수량, 'avg_price': 평단가}}
        'portfolio': {s: {'qty': 0, 'avg_price': 0} for s in stock_map},
        'trade_log': [], 'bots': [], 'season_end_time': None, 'is_ended': False,
        'quiz_cleared': [False] * len(quiz_pool), 'term_idx': 0
    })

def init_bots(diff):
    names = ["퀀트장인", "익산불개미", "여의도황소", "나스닥귀신", "버핏지망생", "단타의신", "개미왕", "AI알고리즘", "풀매수전사"]
    base = {"초급": 50000000, "중급": 10000000, "상급": 1000000}[diff]
    bots = []
    for n in names:
        bot_log = [{"시간": "시즌 중", "종목": random.choice(list(stock_map.keys())), "종류": "매수", "수량": 1}]
        bots.append({"닉네임": n, "자산": base * (1 + (random.random()-0.5)*0.2), "log": bot_log, "strategy": "AI 알고리즘 투자"})
    return bots

# 5. 로그인 화면 ('시작' 버튼 반영)
if not st.session_state.user_name:
    st.title("🏆 AI 투자 5분 스피드 시즌전")
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

# 6. 실시간 자산 및 타이머 계산
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
if not st.session_state.is_ended:
    for bot in st.session_state.bots: bot['자산'] *= (1 + (random.random()-0.5)*0.003)

# 7. 대시보드 출력 (환영 메시지)
st.title(f"📈 {st.session_state.user_name}님 환영합니다!")
c1, c2 = st.columns(2)
c1.metric("💵 가용 현금", f"{st.session_state.balance:,.0f}원")
c2.metric("🏆 실시간 총 자산", f"{total_assets:,.0f}원")

st.divider()

# 8. 메인 탭
tab_market, tab_portfolio, tab_quiz = st.tabs(["🛒 거래소 & 랭킹", "📂 자산 상세 분석", "❓ 주식 퀴즈"])

with tab_market:
    m_col, r_col = st.columns([1.8, 1.2])
    with m_col:
        target = st.selectbox("종목 선택", list(stock_map.keys()))
        df = live_charts[target]
        
        # 📈 [그래프 강제 출력 로직]
        if not df.empty:
            fig = go.Figure(data=[go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                increasing_line_color='#ef4444', decreasing_line_color='#3b82f6'
            )])
            fig.update_layout(template=plotly_template, xaxis_rangeslider_visible=False, height=450, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ 실시간 주가 데이터를 분석 중입니다...")

        # 실시간 수익률 및 매매 UI
        p_now = live_prices[target]
        hold = st.session_state.portfolio[target]
        
        # 💡 [수익률 계산 로직]
        profit_pct = 0
        if hold['qty'] > 0:
            profit_pct = ((p_now - hold['avg_price']) / hold['avg_price']) * 100
        
        st.write(f"### 현재가: {p_now:,}원")
        if hold['qty'] > 0:
            color = "profit" if profit_pct > 0 else "loss"
            st.markdown(f"보유: **{hold['qty']}주** | 평단: **{hold['avg_price']:,.0f}원** | 수익률: <span class='{color}'>{profit_pct:.2f}%</span>", unsafe_allow_html=True)

        qty = st.number_input("거래 수량", min_value=1, value=1, disabled=st.session_state.is_ended)
        b_c, s_c = st.columns(2)
        
        if b_c.button(f"{target} 매수", key=f"buy_{target}", disabled=st.session_state.is_ended):
            if st.session_state.balance >= p_now * qty:
                # 💡 [가중평균단가 계산]
                new_qty = hold['qty'] + qty
                new_avg = ((hold['avg_price'] * hold['qty']) + (p_now * qty)) / new_qty
                st.session_state.balance -= p_now * qty
                st.session_state.portfolio[target] = {'qty': new_qty, 'avg_price': int(new_avg)}
                st.session_state.trade_log.append({"시간": datetime.now().strftime("%H:%M"), "종목": target, "종류": "매수", "수량": qty, "가격": p_now})
                st.rerun()
        
        if s_c.button(f"{target} 매도", key=f"sell_{target}", disabled=st.session_state.is_ended):
            if hold['qty'] >= qty:
                st.session_state.balance += p_now * qty
                st.session_state.portfolio[target]['qty'] -= qty
                st.session_state.trade_log.append({"시간": datetime.now().strftime("%H:%M"), "종목": target, "종류": "매도", "수량": qty, "가격": p_now})
                st.rerun()

    with r_col:
        if not st.session_state.is_ended:
            st.markdown(f'<div class="timer-box">⏳ 종료까지: {int(sec_left//60)}분 {int(sec_left%60)}초</div>', unsafe_allow_html=True)
        else:
            st.error("🏁 시즌 종료 (TOP 3 분석 가능)")

        st.subheader("🏆 시즌 랭킹")
        user_rank_data = {"닉네임": f"{st.session_state.user_name} ⭐", "자산": total_assets, "log": st.session_state.trade_log, "strategy": "사용자 맞춤형 투자"}
        all_p = sorted(st.session_state.bots + [user_rank_data], key=lambda x: x["자산"], reverse=True)
        
        for idx, p in enumerate(all_p):
            medal = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else f"{idx+1}위"
            if st.session_state.is_ended and idx < 3:
                with st.expander(f"{medal} {p['닉네임']} (분석하기)"):
                    st.write(f"💰 최종 자산: {p['자산']:,.0f}원")
                    st.write(f"📝 주요 전략: {p.get('strategy', '비공개')}")
                    if p['log']: st.table(pd.DataFrame(p['log']).tail(3))
            else:
                st.markdown(f'<div class="rank-card">{medal} {p["닉네임"]} <br> {p["자산"]:,.0f}원</div>', unsafe_allow_html=True)

with tab_portfolio:
    if total_stock_value > 0:
        labels = [s for s in stock_map.keys() if st.session_state.portfolio[s]['qty'] > 0]
        values = [st.session_state.portfolio[s]['qty'] * live_prices[s] for s in labels]
        st.plotly_chart(go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)]))
    else: st.info("보유 중인 주식이 없습니다.")

with tab_quiz:
    for i, item in enumerate(quiz_pool):
        if st.session_state.quiz_cleared[i]: st.success(f"✅ Q{i+1} 완료")
        else:
            st.markdown(f'<div class="quiz-container"><b>Q{i+1}. {item["q"]}</b></div>', unsafe_allow_html=True)
            ans = st.radio("정답 선택", item['o'], key=f"q_{i}", index=None)
            if st.button("제출", key=f"btn_{i}"):
                if ans == item['a']:
                    st.session_state.quiz_cleared[i] = True; st.session_state.balance += 10000; st.rerun()

st.divider()
st.latex(r"Profit\_Yield = \frac{Current\_Price - Avg\_Price}{Avg\_Price} \times 100 \%")
if st.button("🔄 시스템 초기화"):
    for k in list(st.session_state.keys()): del st.session_state[k]
    st.rerun()
