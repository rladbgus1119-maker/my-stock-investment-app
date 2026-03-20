import streamlit as st
import pandas as pd
import time

# 1. 페이지 레이아웃 설정
st.set_page_config(page_title="AI 투자 시뮬레이터", layout="wide")

# 2. 스타일 커스터마이징
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stMetric { background-color: #f1f3f8; padding: 15px; border-radius: 10px; border: 1px solid #d1d5db; }
    </style>
    """, unsafe_allow_html=True)

# 3. 세션 상태 초기화
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""
if 'difficulty' not in st.session_state:
    st.session_state.difficulty = ""
if 'balance' not in st.session_state:
    st.session_state.balance = 0 
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {"삼성전자": 0, "애플": 0, "테슬라": 0}
if 'prices' not in st.session_state:
    st.session_state.prices = {"삼성전자": 75000, "애플": 275000, "테슬라": 210000}

# 4. 로그인 및 난이도 선택 화면
if not st.session_state.user_name:
    st.title("🎮 투자 시뮬레이션 시스템 가동")
    st.subheader("사용자 정보와 시뮬레이션 난이도를 선택해 주세요.")
    
    with st.container(border=True):
        input_name = st.text_input("닉네임 입력", placeholder="예: 투자왕")
        
        # 난이도 선택 박스
        difficulty = st.selectbox(
            "시뮬레이션 난이도 선택",
            ["초급 (자산 5,000만 원)", "중급 (자산 1,000만 원)", "상급 (자산 100만 원)"]
        )
        
        st.info("💡 난이도가 높을수록 적은 시드머니로 시작하여 리더보드 공략이 어려워집니다.")
        
        if st.button("시스템 접속 및 자산 지급"):
            if input_name:
                # 난이도에 따른 시드머니 할당 로직
                if "초급" in difficulty:
                    seed_money = 50000000
                    diff_label = "초급"
                elif "중급" in difficulty:
                    seed_money = 10000000
                    diff_label = "중급"
                else:
                    seed_money = 1000000
                    diff_label = "상급"
                
                st.session_state.user_name = input_name
                st.session_state.difficulty = diff_label
                st.session_state.balance = seed_money
                
                st.success(f"{input_name}님, {diff_label} 난이도로 설정되었습니다. 자산 {seed_money:,}원이 지급되었습니다!")
                st.balloons()
                time.sleep(1.5)
                st.rerun()
            else:
                st.warning("이름을 입력해야 접속이 가능합니다.")
    st.stop()

# --- 5. 메인 대시보드 (로그인 후) ---

st.title(f"📈 {st.session_state.user_name}님의 {st.session_state.difficulty} 투자 대시보드")

# 자산 계산
total_stock_val = sum(st.session_state.portfolio[s] * st.session_state.prices[s] for s in st.session_state.prices)
total_assets = st.session_state.balance + total_stock_val

col1, col2, col3 = st.columns(3)
col1.metric("💵 보유 현금", f"{st.session_state.balance:,} 원")
col2.metric("📊 주식 평가액", f"{total_stock_val:,} 원")
col3.metric("🏆 총 자산", f"{total_assets:,} 원", help="보유 현금과 주식 평가액의 합계입니다.")

st.divider()

# 6. 거래소 및 정보 레이아웃
c_left, c_right = st.columns([2, 1])

with c_left:
    st.subheader("🛒 실시간 거래소")
    for stock, price in st.session_state.prices.items():
        with st.container(border=True):
            col_n, col_p, col_b, col_s = st.columns([2, 2, 1, 1])
            col_n.write(f"### {stock}")
            col_p.write(f"**현재가:** {price:,} 원 \n\n **보유량:** {st.session_state.portfolio[stock]}주")
            
            if col_b.button(f"매수", key=f"buy_{stock}"):
                if st.session_state.balance >= price:
                    st.session_state.balance -= price
                    st.session_state.portfolio[stock] += 1
                    st.toast(f"{stock} 매수 완료!")
                    time.sleep(0.3)
                    st.rerun()
                else:
                    st.error("잔액이 부족합니다!")
            
            if col_s.button(f"매도", key=f"sell_{stock}"):
                if st.session_state.portfolio[stock] > 0:
                    st.session_state.balance += price
                    st.session_state.portfolio[stock] -= 1
                    st.toast(f"{stock} 매도 완료!")
                    time.sleep(0.3)
                    st.rerun()

with c_right:
    st.subheader("⭐ 실시간 랭킹")
    # 난이도 정보를 포함한 리더보드 데이터
    rank_data = pd.DataFrame({
        "순위": [1, 2, 3],
        "닉네임": ["퀀트마스터", "반도체왕", f"{st.session_state.user_name} ⭐"],
        "난이도": ["상급", "중급", st.session_state.difficulty],
        "총자산": ["1.5억", "1,240만", f"{total_assets//10000:,}만"]
    })
    st.table(rank_data)
    
    if st.button("🔄 난이도/이름 재설정"):
        st.session_state.user_name = ""
        st.session_state.balance = 0
        st.rerun()

# 하단 수식
st.latex(f"Total\\_Asset = Seed({st.session_state.difficulty}) + \\Delta Profit")
