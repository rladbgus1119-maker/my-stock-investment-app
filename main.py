import streamlit as st
import pandas as pd
import numpy as np
import time

# 페이지 설정
st.set_page_config(page_title="실시간 주식 투자 시뮬레이션", layout="wide")

# 가상 주식 데이터 정의 (제공된 이미지 기반)
# 2020년 1월부터 12월까지의 월별 매출 데이터
data_ref = {
    'Month': list(range(1, 13)),
    '국내 매출': [2300, 3500, 4000, 3200, 3000, 4500, 7000, 7800, 6000, 5800, 5900, 8700],
    '해외 매출': [1900, 3200, 2600, 400, 1900, 2000, 3600, 6000, 4500, 4200, 5200, 6000]
}
df_ref = pd.DataFrame(data_ref)

# 다양한 종목 정의 (가상)
# Month 컬럼을 인덱스로 설정
stock_options = {
    "삼성전자": df_ref.set_index('Month'),
    "현대차": (df_ref.set_index('Month') * 0.8 + np.random.randint(-500, 500, size=(12, 2))).clip(lower=0), # clip(lower=0)으로 음수 방지
    "SK하이닉스": (df_ref.set_index('Month') * 1.2 + np.random.randint(-1000, 1000, size=(12, 2))).clip(lower=0),
    "카카오": (df_ref.set_index('Month') * 0.5 + np.random.randint(-300, 300, size=(12, 2))).clip(lower=0),
    "네이버": (df_ref.set_index('Month') * 0.6 + np.random.randint(-400, 400, size=(12, 2))).clip(lower=0)
}

# 사이드바 설정
with st.sidebar:
    st.header("설정")
    
    # 난이도 선택 및 시드머니 설정
    difficulty = st.selectbox("난이도 선택", ["초급", "중급", "고급"])
    seed_money_dict = {"초급": 100000000, "중급": 50000000, "고급": 10000000}
    seed_money = seed_money_dict[difficulty]
    
    # 세션 상태 초기화 (투자금)
    if 'balance' not in st.session_state:
        st.session_state.balance = seed_money
    if 'stocks_owned' not in st.session_state:
        st.session_state.stocks_owned = 0
    if 'last_difficulty' not in st.session_state:
        st.session_state.last_difficulty = difficulty

    # 난이도 변경 시 잔고 초기화
    if difficulty != st.session_state.last_difficulty:
        st.session_state.balance = seed_money
        st.session_state.stocks_owned = 0
        st.session_state.last_difficulty = difficulty
        st.warning("난이도가 변경되어 투자금이 초기화되었습니다.")

    st.subheader(f"현재 잔고: {st.session_state.balance:,}원")
    st.subheader(f"보유 주식 수: {st.session_state.stocks_owned:,}주")
    st.write(f"시드머니: {seed_money:,}원")

    # 종목 선택
    selected_stock = st.selectbox("종목 선택", list(stock_options.keys()))

# 메인 화면
st.title(f"{selected_stock} 실시간 차트 시뮬레이션")
st.write("2020년 월별 데이터 (가상 주가로 간주)")

# 차트 배경색을 하얗게 설정하기 위한 CSS
st.markdown(
    """
    <style>
    [data-testid="stLineChart"] {
        background-color: white;
        padding: 10px;
        border-radius: 5px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 차트 업데이트를 위한 st.empty()
chart_placeholder = st.empty()
price_placeholder = st.empty()

# 투자 버튼
col1, col2 = st.columns(2)
with col1:
    buy_button = st.button("매수", key="buy")
with col2:
    sell_button = st.button("매도", key="sell")

# 시뮬레이션 루프
df_sim = stock_options[selected_stock].copy()
current_price = 0

# 초기 차트 설정
initial_df = df_sim.iloc[:1]
chart_placeholder.line_chart(initial_df)
current_price = initial_df['국내 매출'].iloc[-1]
price_placeholder.markdown(f"**현재 주가: {current_price:,}원**")
time.sleep(1)

for i in range(2, 13):
    next_row = df_sim.iloc[i-1:i]
    chart_placeholder.add_rows(next_row)
    
    # 현재 가격 (국내 매출을 주가로 가정)
    current_price = next_row['국내 매출'].iloc[-1]
    price_placeholder.markdown(f"**현재 주가: {current_price:,}원**")
    
    # 매수 로직
    if buy_button:
        num_to_buy = st.session_state.balance // current_price
        if num_to_buy > 0:
            st.session_state.balance -= num_to_buy * current_price
            st.session_state.stocks_owned += num_to_buy
            st.success(f"{num_to_buy:,}주 매수 완료!")
            # 매수 후 페이지 새로고침하여 잔고 업데이트
            st.rerun()
        else:
            st.error("잔고가 부족합니다.")
    
    # 매도 로직
    if sell_button:
        if st.session_state.stocks_owned > 0:
            st.session_state.balance += st.session_state.stocks_owned * current_price
            st.success(f"{st.session_state.stocks_owned:,}주 매도 완료! 잔고: {st.session_state.balance:,}원")
            st.session_state.stocks_owned = 0
            # 매도 후 페이지 새로고침하여 잔고 업데이트
            st.rerun()
        else:
            st.error("보유 주식이 없습니다.")

    time.sleep(1) # 1초 대기

# 평가액 표시
total_eval = st.session_state.balance + (st.session_state.stocks_owned * current_price)
st.metric("총 평가액", f"{total_eval:,}원", help="잔고 + (보유 주식 수 * 현재 주가)")
