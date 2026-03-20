import streamlit as st
import pandas as pd
import yfinance as yf
import time
import numpy as np
import random

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="원광대 실시간 AI 투자 시스템", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stMetric { background-color: #f8fafc; padding: 12px; border-radius: 10px; border: 1px solid #e2e8f0; }
    .news-box { background-color: #fffbeb; padding: 10px; border-left: 5px solid #f59e0b; margin-bottom: 8px; border-radius: 5px; font-size: 0.85rem; }
    </style>
    """, unsafe_allow_html=True)

# 2. 주식 종목 및 티커 매핑 (실제 시장 데이터 연결)
stock_map = {
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "NVIDIA": "NVDA",
    "애플": "AAPL", "테슬라": "TSLA", "구글": "GOOGL", "마이크로소프트": "MSFT",
    "현대차": "005380.KS", "넥슨": "3659.T", "텐센트": "0700.HK"
}

news_pool = [
    "🔥 [속보] NVIDIA, 차세대 AI 칩셋 주문 폭주로 사상 최고가 경신",
    "📉 [마켓] 금리 인상 우려로 반도체 및 기술주 전반적 조정 국면",
    "🚀 [단독] 테슬라, 신형 저가형 모델 생산 라인 가동 시작",
    "📢 [공시] 삼성전자, 3나노 파운드리 대형 고객사 추가 확보",
    "💡 [전문가] 원광대 전자공학부, 지능형 반도체 정밀 제어 시스템 상용화 성공",
    "🎮 [산업] 넥슨, 신작 흥행으로 글로벌 매출 목표 상향 조정"
]

# 3. 실시간 주가 로직 (API 연동 및 환율 적용)
@st.cache_data(ttl=60)
def fetch_real_prices():
    prices = {}
    for name, ticker in stock_map.items():
        try:
            data = yf.Ticker(ticker)
            # 최근 종가 가져오기
            price = data.history(period="1d")['Close'].iloc[-1]
            # 해외주식(USD, JPY, HKD) 대략적 환율 적용
            if ".KS" not in ticker:
                if ".T" in ticker: price *= 9.0   # JPY -> KRW
                elif ".HK" in ticker: price *= 170.0 # HKD -> KRW
                else: price *= 1400.0 # USD -> KRW
            # 실시간 변동 느낌을 위한 미세 노이즈(±0.1%)
            noise = (np.random.rand() - 0.5) * 0.002
            prices[name] = int(price * (1 + noise))
        except:
            prices[name] = 100000 # 에러 시 기본값
    return prices

# 4. 세션 상태 초기화
if 'user_name' not in st.session_state: st.session_state.user_name = ""
if 'difficulty' not in st.session_state: st.session_state.difficulty = ""
if 'balance' not in st.session_state: st.session_state.balance = 0.0
if 'portfolio' not in st.session_state: st.session_state.portfolio = {s: 0 for s in stock_map}
if 'bot_data' not in st.session_state:
    st.session_state.bot_data = [
        {"닉네임": "나스닥귀신", "자산": 150000000.0},
        {"닉네임": "불개미엔지니어", "자산": 75000000.0}
    ]

# 5. 로그인 및 난이도 화면
if not st.session_state.user_name:
    st.title("👨‍💻 원광대 실시간 AI 투자 제어 시스템")
    with st.container(border=True):
        name = st.text_input("닉네임 입력")
        diff = st.selectbox("시뮬레이션 난이도", ["초급 (5,000만)", "중급 (1,000만)", "상급 (100만)"])
        if st.button("시스템 접속"):
            if name:
                st.session_state.user_name = name
                st.session_state.difficulty = diff.split()[0]
                st.session_state.balance = 50000000.0 if "초급" in diff else 10000000.0 if "중급" in diff else 1000000.0
                st.rerun()
    st.stop()

# 6. 메인 시스템 가동
current_prices = fetch_real_prices()
total_stock_val = sum(st.session_state.portfolio[s] * current_prices[s] for s in stock_map)
total_assets = st.session_state.balance + total_stock_val

st.title(f"📈 {st.session_state.user_name}님의 {st.session_state.difficulty} 투자 대시보드")
st.caption(f"기준 시간: {time.strftime('%Y-%m-%d %H:%M:%S')} | 실제 시장 데이터 기반")

c1, c2, c3 = st.columns(3)
c1.metric("💵 보유 현금", f"{st.session_state.balance:,.0f} 원")
c2.metric("📊 주식 평가액", f"{total_stock_val:,.0f} 원")
c3.metric("🏆 총 자산", f"{total_assets:,.0f} 원")

st.divider()

# 7. 거래소 및 뉴스/랭킹 레이아웃
main_col, side_col = st.columns([2, 1])

with main_col:
    st.subheader("🛒 실시간 거래소")
    qty = st.number_input("거래 수량 설정 (주)", min_value=1, max_value=10000, value=1)
    
    stocks = list(current_prices.items())
    for i in range(0, len(stocks), 2):
        row = st.columns(2)
        for j in range(2):
            if i + j < len(stocks):
                name, price = stocks[i + j]
                with row[j].container(border=True):
                    st.write(f"### {name}")
                    st.metric("현재가", f"{price:,}원", help="야후 파이낸스 실시간 주가")
                    st.write(f"보유: **{st.session_state.portfolio[name]}** 주")
                    
                    b_btn, s_btn = st.columns(2)
                    cost = price * qty
                    if b_btn.button(f"{qty}주 매수", key=f"b_{name}"):
                        if st.session_state.balance >= cost:
                            st.session_state.balance -= cost
                            st.session_state.portfolio[name] += qty
                            st.toast(f"{name} 매수 성공!"); time.sleep(0.1); st.rerun()
                        else: st.error("잔액 부족!")
                    
                    if s_btn.button(f"{qty}주 매도", key=f"s_{name}"):
                        if st.session_state.portfolio[name] >= qty:
                            st.session_state.balance += cost
                            st.session_state.portfolio[name] -= qty
                            st.toast(f"{name} 매도 성공!"); time.sleep(0.1); st.rerun()
                        else: st.error("수량 부족!")

with side_col:
    st.subheader("📰 실시간 뉴스 피드")
    for news in random.sample(news_pool, 3):
        st.markdown(f'<div class="news-box">{news}</div>', unsafe_allow_html=True)
    
    st.subheader("⭐ 실시간 랭킹")
    all_players = st.session_state.bot_data + [{"닉네임": f"{st.session_state.user_name} ⭐", "자산": total_assets}]
    sorted_p = sorted(all_players, key=lambda x: x["자산"], reverse=True)
    
    rank_df = []
    for i, p in enumerate(sorted_p):
        rank_df.append({"순위": i+1, "닉네임": p["닉네임"], "총자산": f"{p['자산']:,.0f}원"})
    st.table(pd.DataFrame(rank_df))

    if st.button("🔄 시스템 초기화"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

st.divider()
st.latex(r"Asset_{total} = Balance + \sum_{i=1}^{n} (Price_i \times Qty_i)")
