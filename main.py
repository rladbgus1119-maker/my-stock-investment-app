import streamlit as st
import pandas as pd
import yfinance as yf
import time
import numpy as np
import random

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="원광대 AI 투자 & 아카데미 시스템", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stMetric { background-color: #f8fafc; padding: 12px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
    .news-box { background-color: #fffbeb; padding: 12px; border-left: 5px solid #f59e0b; margin-bottom: 10px; border-radius: 5px; font-size: 0.85rem; }
    .mission-card { background-color: #f0fdf4; padding: 15px; border-radius: 10px; border: 1px solid #bbf7d0; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 세트 설계 (주식, 퀴즈, 용어)
stock_map = {
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "NVIDIA": "NVDA",
    "애플": "AAPL", "테슬라": "TSLA", "구글": "GOOGL", "마이크로소프트": "MSFT",
    "현대차": "005380.KS", "넥슨": "3659.T", "텐센트": "0700.HK"
}

avatar_info = {
    "🛡️ 든든한 가디언": "안전과 장기 투자를 선호하는 보수적 엔지니어",
    "🚀 불타는 로켓": "고수익 기술주에 올인하는 공격적 엔지니어",
    "⚖️ 냉철한 분석가": "데이터와 단기 흐름을 쫓는 전략적 엔지니어",
    "🌱 투자 꿈나무": "원광대 정신으로 미래 가치를 키우는 성장형 엔지니어"
}

quiz_pool = [
    {"q": "기업이 이익 중 일부를 주주에게 나누어 주는 것은?", "a": "배당금", "o": ["배당금", "이자", "상여금"]},
    {"q": "주식 수량에 현재가를 곱한 기업의 전체 가치는?", "a": "시가총액", "o": ["자본금", "시가총액", "매출액"]},
    {"q": "PER이 낮을수록 이익 대비 주가가 저평가된 것이다?", "a": "O", "o": ["O", "X"]}
]

# 3. 실시간 가격 엔진 (캐싱 적용)
@st.cache_data(ttl=60)
def get_market_data():
    prices = {}
    for name, ticker in stock_map.items():
        try:
            data = yf.Ticker(ticker)
            p = data.history(period="1d")['Close'].iloc[-1]
            if ".KS" not in ticker: # 해외 주식 환율 적용
                if ".T" in ticker: p *= 9.2   # JPY
                elif ".HK" in ticker: p *= 172.0 # HKD
                else: p *= 1410.0 # USD
            prices[name] = int(p * (1 + (np.random.rand()-0.5)*0.002))
        except: prices[name] = 100000
    return prices

# 4. 세션 상태 초기화 (메모리 설계)
if 'init' not in st.session_state:
    st.session_state.update({
        'init': True, 'user_name': "", 'difficulty': "", 'avatar': "", 'points': 0,
        'balance': 0.0, 'portfolio': {s: 0 for s in stock_map},
        'attendance': False, 'm_trade': False, 'quiz_done': [False]*len(quiz_pool),
        'bot_data': [
            {"닉네임": "안전봇", "난이도": "초급", "자산": 55000000.0, "성향": "🛡️ 든든한 가디언"},
            {"닉네임": "성장봇", "난이도": "초급", "자산": 52000000.0, "성향": "🌱 투자 꿈나무"},
            {"닉네임": "분석봇", "난이도": "중급", "자산": 15000000.0, "성향": "⚖️ 냉철한 분석가"},
            {"닉네임": "로켓봇", "난이도": "중급", "자산": 12000000.0, "성향": "🚀 불타는 로켓"},
            {"닉네임": "나스닥귀신", "난이도": "상급", "자산": 3000000.0, "성향": "🚀 불타는 로켓"},
            {"닉네임": "워런버핏봇", "난이도": "상급", "자산": 2500000.0, "성향": "🛡️ 든든한 가디언"}
        ]
    })

# --- 5. 온보딩: AI 성향 분석 및 난이도 설정 ---
if not st.session_state.user_name:
    st.title("👨‍🔬 AI 투자 성향 분석 & 시스템 가동")
    with st.container(border=True):
        name = st.text_input("닉네임 입력")
        diff = st.selectbox("챌린지 등급", ["초급 (5,000만)", "중급 (1,000만)", "상급 (100만)"])
        
        st.write("---")
        st.write("**🤖 AI 투자 성향 진단**")
        q1 = st.radio("위험 선호도", ["원금 보호가 최고다", "손실 감수하고 대박 노린다"])
        q2 = st.radio("투자 기간", ["오래 보유한다", "매일 확인하고 사고판다"])
        
        if st.button("성향 분석 및 접속"):
            if name:
                st.session_state.user_name = name
                st.session_state.difficulty = diff.split()[0]
                st.session_state.balance = 50000000.0 if "초급" in diff else 10000000.0 if "중급" in diff else 1000000.0
                
                # 분석 로직
                if "원금" in q1 and "오래" in q2: st.session_state.avatar = "🛡️ 든든한 가디언"
                elif "손실" in q1 and "매일" in q2: st.session_state.avatar = "🚀 불타는 로켓"
                elif "매일" in q2: st.session_state.avatar = "⚖️ 냉철한 분석가"
                else: st.session_state.avatar = "🌱 투자 꿈나무"
                
                st.success(f"분석 완료! 당신은 **{st.session_state.avatar}** 타입입니다."); time.sleep(1.5); st.rerun()
    st.stop()

# --- 6. 메인 제어 센터 ---
prices = get_market_data()
total_stock_val = sum(st.session_state.portfolio[s] * prices[s] for s in stock_map)
total_assets = st.session_state.balance + total_stock_val

st.title(f"{st.session_state.avatar.split()[0]} {st.session_state.user_name} 엔지니어")
st.caption(f"등급: {st.session_state.difficulty} | 성향: {st.session_state.avatar}")

col_h1, col_h2, col_h3, col_h4 = st.columns(4)
col_h1.metric("💵 보유 현금", f"{st.session_state.balance:,.0f}원")
col_h2.metric("🏆 총 자산", f"{total_assets:,.0f}원")
col_h3.metric("💎 포인트", f"{st.session_state.points}P")
with col_h4:
    if not st.session_state.attendance:
        if st.button("📅 오늘 출석 (5만 원)"):
            st.session_state.attendance = True; st.session_state.balance += 50000; st.session_state.points += 10
            st.toast("출석 완료!"); time.sleep(0.5); st.rerun()
    else: st.success("✅ 출석 완료")

st.divider()

# --- 7. 기능 통합 탭 ---
tab_trade, tab_mission, tab_academy = st.tabs(["🛒 거래소 & 랭킹", "🎯 미션 & 보상", "📚 투자 아카데미"])

# [탭 1: 거래소 & 등급별 랭킹]
with tab_trade:
    c_main, c_side = st.columns([2, 1])
    with c_main:
        st.subheader("🛒 실시간 마켓")
        t_qty = st.number_input("거래 수량 설정", min_value=1, value=1)
        stocks = list(prices.items())
        for i in range(0, len(stocks), 2):
            cols = st.columns(2)
            for j in range(2):
                if i+j < len(stocks):
                    n, p = stocks[i+j]
                    with cols[j].container(border=True):
                        st.write(f"### {n}"); st.write(f"가: {p:,}원 | 보: {st.session_state.portfolio[n]}주")
                        b, s = st.columns(2)
                        if b.button(f"매수", key=f"b_{n}"):
                            if st.session_state.balance >= p * t_qty:
                                st.session_state.balance -= p * t_qty; st.session_state.portfolio[n] += t_qty
                                st.session_state.m_trade = True; st.rerun()
                        if s.button(f"매도", key=f"s_{n}"):
                            if st.session_state.portfolio[n] >= t_qty:
                                st.session_state.balance += p * t_qty; st.session_state.portfolio[n] -= t_qty
                                st.rerun()
    with c_side:
        st.subheader(f"⭐ {st.session_state.difficulty} 등급 랭킹")
        relevant_bots = [b for b in st.session_state.bot_data if b["난이도"] == st.session_state.difficulty]
        user_rank = {"닉네임": f"{st.session_state.user_name} ⭐", "성향": st.session_state.avatar, "자산": total_assets}
        all_r = sorted(relevant_bots + [user_rank], key=lambda x: x["자산"], reverse=True)
        r_list = [{"순위": i+1, "엔지니어": f"{p['성향'].split()[0]} {p['닉네임']}", "자산": f"{p['자산']:,.0f}원"} for i, p in enumerate(all_r)]
        st.table(pd.DataFrame(r_list))

# [탭 2: 미션 & 보상]
with tab_mission:
    st.header("🎯 오늘의 엔지니어 미션")
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown(f'<div class="mission-card"><b>첫 매수 성공</b><br>보상: 10만 원 / 20P<br>{"✅ 달성" if st.session_state.m_trade else "⏳ 미달성"}</div>', unsafe_allow_html=True)
    with col_m2:
        m2_ok = total_assets >= (100000000 if st.session_state.difficulty == "초급" else 50000000)
        st.markdown(f'<div class="mission-card"><b>자산 목표 달성</b><br>보상: 50만 원 / 50P<br>{"✅ 달성" if m2_ok else "⏳ 진행 중"}</div>', unsafe_allow_html=True)
    
    st.header("🧠 지식 테스트 (보너스)")
    for i, q in enumerate(quiz_pool):
        if not st.session_state.quiz_done[i]:
            with st.expander(f"문제 {i+1}"):
                ans = st.radio("정답 선택", q['o'], key=f"quiz_{i}")
                if st.button("제출", key=f"btn_{i}"):
                    if ans == q['a']:
                        st.session_state.quiz_done[i] = True; st.session_state.balance += 10000; st.rerun()
        else: st.info(f"문제 {i+1} 완료 (보상 지급됨)")

# [탭 3: 아카데미]
with tab_academy:
    st.header("📚 주식 용어 사전")
    terms = {"PER": "주가수익비율. 낮을수록 저평가.", "PBR": "주가순자산비율. 1 미만이면 자산보다 저렴.", "시가총액": "기업의 총 몸무게."}
    for k, v in terms.items(): st.write(f"**{k}**: {v}")
    st.image("https://upload.wikimedia.org/wikipedia/commons/e/e4/Stock_market_index_chart.png", caption="시장 흐름 읽기")
    if st.button("🔄 데이터 전체 리셋"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

st.divider()
st.latex(r"Asset_{total} = Balance + \sum (Price_{real} \times Qty)")
