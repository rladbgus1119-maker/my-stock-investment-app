import streamlit as st
import pandas as pd
import numpy as np
import time

# 1. 페이지 레이아웃 설정
st.set_page_config(page_title="AI 투자 시뮬레이터", layout="wide", initial_sidebar_state="collapsed")

# 2. 스타일 커스터마이징 (Streamlit 툴바 숨기기 및 한국어 폰트 최적화)
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stMetric { background-color: #f0f2f6; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 3. 세션 상태 초기화 (데이터 유지)
if 'balance' not in st.session_state:
    st.session_state.balance = 10000000  # 기본 자산 1,000만원
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {"삼성전자": 0, "애플": 0, "테슬라": 0}
if 'prices' not in st.session_state:
    st.session_state.prices = {"삼성전자": 75000, "애플": 275000, "테슬라": 210000}

# 4. 사이드바: 난이도 설정
st.sidebar.title("🎮 시스템 설정")
difficulty = st.sidebar.selectbox("시뮬레이션 난이도", ["초보자", "중급자", "전문가"])
weights = {"초보자": 0.5, "중급자": 0.8, "전문가": 1.2}

# 5. 메인 대시보드
st.title("📈 AI 실시간 투자 챌린지")
st.caption("전자공학도를 위한 고정밀 투자 시뮬레이션 시스템")

# 자산 현황 섹션
col1, col2, col3 = st.columns(3)
total_stock_val = sum(st.session_state.portfolio[s] * st.session_state.prices[s] for s in st.session_state.prices)
total_assets = st.session_state.balance + total_stock_val

col1.metric("💵 보유 현금", f"{st.session_state.balance:,} 원")
col2.metric("📊 주식 평가액", f"{total_stock_val:,} 원")
col3.metric("🏆 총 자산", f"{total_assets:,} 원", delta=f"{weights[difficulty]}x 가중치 적용")

st.divider()

# 6. 마켓 뉴스 및 실시간 거래 (설계도 반영)
c_left, c_right = st.columns([2, 1])

with c_left:
    st.subheader("🛒 실시간 거래소")
    for stock, price in st.session_state.prices.items():
        with st.container(border=True):
            col_n, col_p, col_b, col_s = st.columns([2, 2, 1, 1])
            col_n.write(f"### {stock}")
            col_p.write(f"**현재가:** {price:,} 원")
            
            if col_b.button(f"매수", key=f"buy_{stock}"):
                if st.session_state.balance >= price:
                    st.session_state.balance -= price
                    st.session_state.portfolio[stock] += 1
                    st.toast(f"{stock} 1주를 매수했습니다!", icon="✅")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("잔액이 부족합니다!")
            
            if col_s.button(f"매도", key=f"sell_{stock}"):
                if st.session_state.portfolio[stock] > 0:
                    st.session_state.balance += price
                    st.session_state.portfolio[stock] -= 1
                    st.toast(f"{stock} 1주를 매도했습니다!", icon="💰")
                    time.sleep(0.5)
                    st.rerun()

with c_right:
    st.subheader("📰 뉴스 피드")
    news_list = [
        "📢 반도체 수율 99% 달성 전망",
        "📢 나스닥 기술주 중심 강세",
        "📢 신규 자율주행 알고리즘 공개"
    ]
    for news in news_list:
        st.info(news)
    
    st.subheader("⭐ 리더보드")
    rank_data = pd.DataFrame({
        "순위": [1, 2, 3],
        "닉네임": ["퀀트마스터", "원광대엔지니어", "나 ⭐"],
        "총자산": ["1,520만", "1,240만", f"{total_assets//10000:,}만"]
    })
    st.table(rank_data)

st.caption("본 시스템의 자산 가치 산출 공식: $A = B + \sum (P_i \times Q_i)$")