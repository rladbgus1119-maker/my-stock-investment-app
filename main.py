import streamlit as st
import pandas as pd
import time

# 1. 페이지 설정
st.set_page_config(page_title="AI 투자 시뮬레이터", layout="wide")

# 2. 세션 상태에 이름 저장 변수 만들기
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""

# 3. 이름 입력 화면 (이름이 없을 때만 표시)
if not st.session_state.user_name:
    st.title("👋 환영합니다!")
    st.subheader("투자 시뮬레이션 시작 전, 당신의 이름을 알려주세요.")
    
    name = st.text_input("닉네임을 입력하세요 (예: 원광대 에이스)", key="name_input")
    
    if st.button("입장하기"):
        if name:
            st.session_state.user_name = name
            st.success(f"{name}님, 환영합니다! 시스템을 가동합니다.")
            time.sleep(1)
            st.rerun()
        else:
            st.warning("이름을 입력해야 입장할 수 있습니다.")
    st.stop() # 이름을 입력하기 전까지 아래 코드는 실행되지 않음

# --- 여기서부터는 기존 투자 앱 코드 ---

# 4. 상단 인사말 및 자산 현황
st.title(f"📈 {st.session_state.user_name}님의 실시간 투자 대시보드")
st.write(f"현재 접속자: **{st.session_state.user_name}** 엔지니어")

# (이후 기존 자산 계산 및 거래 로직 그대로 유지...)
if 'balance' not in st.session_state:
    st.session_state.balance = 10000000
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {"삼성전자": 0, "애플": 0, "테슬라": 0}
if 'prices' not in st.session_state:
    st.session_state.prices = {"삼성전자": 75000, "애플": 275000, "테슬라": 210000}

# 대시보드 레이아웃
c1, c2, c3 = st.columns(3)
total_stock_val = sum(st.session_state.portfolio[s] * st.session_state.prices[s] for s in st.session_state.prices)
c1.metric("💵 보유 현금", f"{st.session_state.balance:,} 원")
c2.metric("📊 주식 평가액", f"{total_stock_val:,} 원")
c3.metric("🏆 총 자산", f"{st.session_state.balance + total_stock_val:,} 원")

st.balloons() # 입장 축하 풍선!
