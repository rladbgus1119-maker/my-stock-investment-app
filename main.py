import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import numpy as np
import random
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. 페이지 설정 및 다이내믹 테마 시스템
st.set_page_config(page_title="AI 실시간 투자 터미널 v15", layout="wide")

# [핵심] 1초마다 자동 새로고침 (실시간 타이머 및 자산 반영용)
st_autorefresh(interval=1000, key="datarefresh")

# 사이드바 설정
st.sidebar.title("🎨 UI 환경 설정")
theme_choice = st.sidebar.radio("배경 테마 선택", ["라이트 모드", "다크 모드"])

if theme_choice == "다크 모드":
    bg, txt, card, border = "#0e1117", "#ffffff", "#1d2026", "#3d414a"
    plotly_template = "plotly_dark"
else:
    bg, txt, card, border = "#ffffff", "#000000", "#f8fafc", "#e2e8f0"
    plotly_template = "plotly_white"

# [가독성 강화 CSS] 다크모드에서도 모든 글자가 또렷하게 보이도록 설정
st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg} !important; color: {txt} !important; }}
    h1, h2, h3, h4, p, span, div, label, .stMarkdown, .stTable {{ color: {txt} !important; }}
    [data-testid="stWidgetLabel"] p {{ color: {txt} !important; font-weight: bold; }}
    .stMetric {{ background-color: {card} !important; padding: 15px; border-radius: 12px; border: 1px solid {border} !important; }}
    .rank-card {{ background-color: {card} !important; border-radius: 10px; padding: 12px; border: 1px solid {border} !important; margin-bottom: 8px; }}
    .quiz-container {{ background-color: {card} !important; padding: 20px; border-radius: 12px; border-left: 6px solid #ef4444 !important; margin-bottom: 15px; }}
    .timer-box {{ background-color: #ef4444; color: white !important; padding: 15px; border-radius: 12px; text-align: center; font-size: 1.4rem; font-weight: bold; margin-bottom: 15px; }}
    .term-box {{ background-color: {card} !important; padding: 15px; border-radius: 10px; border: 1px solid {border} !important; margin-bottom: 10px; }}
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 세트 (순수 주식 콘텐츠)
stock_map = {
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "NVIDIA": "NVDA",
    "애플": "AAPL", "테슬라": "TSLA", "마이크로소프트": "MSFT", "아마존": "AMZN", "현대차": "005380.KS"
}

avatar_base = {"🛡️ 든든한 가디언": "🐢", "🚀 불타는 로켓": "🚀", "⚖️ 냉철한 분석가": "💻", "🌱 투자 꿈나무": "🌱", "🐣 분석 대기 중": "🥚"}

terms_pool = [
    {"t": "코스피", "d": "한국 대표 주식 시장 지수"}, {"t": "블루칩", "d": "우량주"}, 
    {"t": "서킷브레이커", "d": "급락 시 매매 일시 중단"}, {"t": "배당금", "d": "주주에게 주는 이익금"}, 
    {"t": "시가총액", "d": "기업의 전체 몸값"}, {"t": "익절", "d": "수익 확정 매도"}, 
    {"t": "손절매", "d": "손실 감수 매도"}, {"t": "공매도", "d": "빌려서 팔기"}
]

quiz_pool = [
    {"q": "상승장을 의미하는 동물은?", "a": "황소(Bull)", "o": ["황소(Bull)", "곰(Bear)", "사자(Lion)"]},
    {"q": "기업 이익 일부를 주주에게 나누어 주는 보너스는?", "a": "배당금", "o": ["배당금", "이자", "상여금"]},
    {"q": "상장 주식수 x 주가는?", "a": "시가총액", "o": ["매출액", "시가총액", "순이익"]}
]

# 3. 실시간 가격 엔진
@st.cache_data(ttl=30)
def fetch_realtime_data(target_name):
    ticker = stock_map[target_name]
    try:
        data = yf.download(ticker, period="5d", interval="15m", progress=False)
        current_price = data['Close'].iloc[-1]
        if ".KS" not in ticker: current_price *= 1415 # 환율 적용
        noise_price = int(current_price * (1 + (np.random.rand()-0.5)*0.005))
        return noise_price, data
    except: return 100000, pd.DataFrame()

# 4. 세션 상태 초기화
if 'user_name' not in st.session_state:
    st.session_state.update({
        'user_name': "", 'difficulty': "", 'balance': 0.0, 'points': 0,
        'portfolio': {s: 0 for s in stock_map}, 'trade_log': [],
        'trade_count': 0, 'tech_focus': 0, 'avatar': "🐣 분석 대기 중",
        'attendance': False, 'quiz_cleared': [False] * len(quiz_pool),
        'term_idx': 0, 'bots': [], 'season_end_time': None, 'is_season_ended': False,
        'equipped': ""
    })

def init_bots(diff):
    names = ["퀀트마스터", "익산불개미", "여의도황소", "나스닥귀신", "버핏지망생", "단타의신", "월스트리트", "AI알고리즘", "풀매수전사"]
    base = {"초급": 50000000, "중급": 10000000, "상급": 1000000}[diff]
    return [{"닉네임": n, "자산": base * (1 + (random.random()-0.5)*0.2), "성향": "🛡️ 든든한 가디언", "난이도": diff} for n in names]

# --- 5. 로그인 화면 (버튼 문구 '시작') ---
if not st.session_state.user_name:
    st.title("🏆 AI 투자 5분 스피드 시즌전")
    with st.container(border=True):
        name = st.text_input("닉네임 입력")
        diff_choice = st.selectbox("참여 등급", ["초급 (5,000만)", "중급 (1,000만)", "상급 (100만)"])
        if st.button("시작"): # '시작' 버튼 반영
            if name:
                st.session_state.user_name = name; dl = diff_choice.split()[0]
                st.session_state.difficulty = dl; st.session_state.balance = 50000000.0 if "초급" in diff_choice else 10000000.0 if "중급" in diff_choice else 1000000.0
                st.session_state.bots = init_bots(dl)
                st.session_state.season_end_time = datetime.now() + timedelta(minutes=5)
                st.rerun()
    st.stop()

# 6. 타이머 실시간 계산
time_left = st.session_state.season_end_time - datetime.now()
seconds_left = max(0, time_left.total_seconds())
if seconds_left <= 0: st.session_state.is_season_ended = True

# 7. 실시간 데이터 및 자산 합산
live_prices = {}; stock_histories = {}
total_stock_value = 0
for n in stock_map.keys():
    price, history = fetch_realtime_data(n)
    live_prices[n] = price; stock_histories[n] = history
    total_stock_value += st.session_state.portfolio[n] * price

total_assets = st.session_state.balance + total_stock_value

# 봇 자산 실시간 변동
if not st.session_state.is_season_ended:
    for bot in st.session_state.bots: bot['자산'] *= (1 + (random.random()-0.5)*0.003)

# --- 8. 대시보드 출력 (닉네임님 환영합니다! 버전) ---
full_avatar = f"{avatar_base.get(st.session_state.avatar, '🥚')} {st.session_state.equipped}"
st.title(f"{full_avatar} {st.session_state.user_name}님 환영합니다!") # 요청하신 타이틀 반영
st.caption(f"현재 등급: {st.session_state.difficulty} | AI 분석 성향: {st.session_state.avatar}")

col_h1, col_h2, col_h3 = st.columns([1.5, 1.5, 1])
col_h1.metric("💵 가용 현금", f"{st.session_state.balance:,.0f}원")
col_h2.metric("🏆 실시간 총 자산", f"{total_assets:,.0f}원") # 실시간 동기화
with col_h3:
    if not st.session_state.attendance:
        if st.button("📅 출석 체크"):
            st.session_state.balance += 50000; st.session_state.points += 10; st.session_state.attendance = True; st.rerun()
    else: st.success("✅ 오늘 출석 완료")

st.divider()

# 9. 기능 탭
tab_market, tab_portfolio, tab_quiz, tab_history = st.tabs(["🛒 거래소 & 실시간 랭킹", "📂 자산 상세 분석", "❓ 주식 퀴즈", "📜 거래 로그"])

with tab_market:
    m_col, r_col = st.columns([2, 1])
    with m_col:
        target_stock = st.selectbox("종목 분석", list(stock_map.keys()))
        df = stock_histories[target_stock]
        if not df.empty:
            fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='시세')])
            fig.update_layout(template=plotly_template, xaxis_rangeslider_visible=False, height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        qty = st.number_input("수량", min_value=1, value=1, disabled=st.session_state.is_season_ended)
        p = live_prices[target_stock]
        b_c, s_c = st.columns(2)
        if b_c.button(f"매수 ({p:,}원)", key=f"buy_{target_stock}", disabled=st.session_state.is_season_ended):
            if st.session_state.balance >= p * qty:
                st.session_state.balance -= p * qty; st.session_state.portfolio[target_stock] += qty
                st.session_state.trade_log.append({"시간": datetime.now().strftime("%H:%M:%S"), "종목": target_stock, "종류": "매수", "수량": qty, "가격": p}); st.rerun()
        if s_c.button(f"매도 ({p:,}원)", key=f"sell_{target_stock}", disabled=st.session_state.is_season_ended):
            if st.session_state.portfolio[target_stock] >= qty:
                st.session_state.balance += p * qty; st.session_state.portfolio[target_stock] -= qty
                st.session_state.trade_log.append({"시간": datetime.now().strftime("%H:%M:%S"), "종목": target_stock, "종류": "매도", "수량": qty, "가격": p}); st.rerun()

    with r_col:
        # 실시간 1초 주기 타이머
        if not st.session_state.is_season_ended:
            st.markdown(f'<div class="timer-box">⏳ 시즌 종료까지: {int(seconds_left // 60)}분 {int(seconds_left % 60)}초</div>', unsafe_allow_html=True)
        else:
            st.error("🏁 시즌 종료 (순위 확정)")

        st.subheader(f"🏆 {st.session_state.difficulty} 시즌 랭킹")
        user_rank_info = {"닉네임": f"{st.session_state.user_name} ⭐", "자산": total_assets}
        all_p = sorted(st.session_state.bots + [user_rank_info], key=lambda x: x["자산"], reverse=True)
        
        user_rank = 10
        for idx, p in enumerate(all_p):
            if "⭐" in p["닉네임"]: user_rank = idx + 1
            st.markdown(f'<div class="rank-card">{"🥇" if idx==0 else "🥈" if idx==1 else "🥉" if idx==2 else f"{idx+1}위"} {p["닉네임"]} <br> {p["자산"]:,.0f}원</div>', unsafe_allow_html=True)
        
        # 시즌 종료 후 승급 시스템
        if st.session_state.is_season_ended:
            st.divider()
            if user_rank <= 3:
                st.success(f"최종 {user_rank}위! 승급 가능")
                target = "중급" if st.session_state.difficulty == "초급" else "상급"
                if st.session_state.difficulty != "상급" and st.button(f"🚀 {target}으로 승급"):
                    st.session_state.update({'difficulty': target, 'balance': 10000000.0 if target=="중급" else 1000000.0, 'portfolio': {s: 0 for s in stock_map}, 'is_season_ended': False, 'season_end_time': datetime.now() + timedelta(minutes=5), 'bots': init_bots(target)})
                    st.rerun()
            else:
                if st.button("🔄 시즌 재도전"):
                    st.session_state.update({'is_season_ended': False, 'season_end_time': datetime.now() + timedelta(minutes=5)})
                    st.rerun()

# 포트폴리오 차트
with tab_portfolio:
    if total_stock_value > 0:
        labels = [s for s in stock_map.keys() if st.session_state.portfolio[s] > 0]
        values = [st.session_state.portfolio[s] * live_prices[s] for s in labels]
        fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])
        st.plotly_chart(fig_pie)
    else: st.info("보유 주식이 없습니다.")

# 퀴즈 (중복 보상 방지 및 순수 주식 문제)
with tab_quiz:
    for i, item in enumerate(quiz_pool):
        if st.session_state.quiz_cleared[i]: st.success(f"✅ Q{i+1} 완료! (보상 지급됨)")
        else:
            with st.container():
                st.markdown(f'<div class="quiz-container"><b>Q{i+1}. {item["q"]}</b></div>', unsafe_allow_html=True)
                ans = st.radio("정답 선택", item['o'], key=f"q_{i}", index=None)
                if st.button("제출", key=f"btn_{i}"):
                    if ans == item['a']:
                        st.session_state.quiz_cleared[i] = True; st.session_state.balance += 10000; st.session_state.points += 10; st.rerun()

# 용어 사전 (5개 순환)
with tab_history:
    st.header("📚 주식 용어 순환 사전")
    start = st.session_state.term_idx
    for t in terms_pool[start:start+5]:
        st.markdown(f'<div class="term-box"><b>{t["t"]}</b>: {t["d"]}</div>', unsafe_allow_html=True)
    if st.button("🔄 다음 용어 보기"): st.session_state.term_idx = (st.session_state.term_idx + 5) % len(terms_pool); st.rerun()

st.divider()
st.latex(r"Asset_{total} = Cash + \sum (Price_{real} \times Quantity)")
