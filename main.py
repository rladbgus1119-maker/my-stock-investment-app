import streamlit as st
import pandas as pd
import yfinance as yf
import time
import numpy as np
import random
from datetime import datetime, timedelta

# 1. 페이지 설정 및 다이내믹 테마 시스템
st.set_page_config(page_title="AI 투자 5분 시즌 챌린지", layout="wide")

st.sidebar.title("🎮 시즌 관제 센터")
theme_choice = st.sidebar.radio("배경 테마 선택", ["라이트 모드", "다크 모드"])

if theme_choice == "다크 모드":
    bg, txt, card, border = "#0e1117", "#ffffff", "#1d2026", "#3d414a"
else:
    bg, txt, card, border = "#ffffff", "#000000", "#f8fafc", "#e2e8f0"

# [가독성 강화 CSS] 다크 모드에서도 모든 글자가 또렷하게 보이도록 설정
st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg} !important; color: {txt} !important; }}
    h1, h2, h3, h4, p, span, div, label, .stMarkdown {{ color: {txt} !important; }}
    [data-testid="stWidgetLabel"] p {{ color: {txt} !important; font-weight: bold; }}
    .stMetric {{ background-color: {card} !important; padding: 15px; border-radius: 12px; border: 1px solid {border} !important; }}
    .rank-card {{ background-color: {card} !important; border-radius: 10px; padding: 12px; border: 1px solid {border} !important; margin-bottom: 8px; }}
    .quiz-container {{ background-color: {card} !important; padding: 20px; border-radius: 12px; border-left: 6px solid #ef4444 !important; margin-bottom: 15px; }}
    .term-box {{ background-color: {card} !important; padding: 15px; border-radius: 10px; border: 1px solid {border} !important; margin-bottom: 10px; }}
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 세트 (순수 주식 콘텐츠)
stock_map = {
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "NVIDIA": "NVDA",
    "애플": "AAPL", "테슬라": "TSLA", "마이크로소프트": "MSFT", "아마존": "AMZN", "현대차": "005380.KS"
}

terms_pool = [
    {"t": "코스피", "d": "한국 대표 주식 시장 지수"}, {"t": "코스닥", "d": "벤처/IT 기업 위주 시장"}, 
    {"t": "나스닥", "d": "미국 기술주 중심 시장"}, {"t": "블루칩", "d": "우량주"}, 
    {"t": "서킷브레이커", "d": "급락 시 매매 일시 중단"}, {"t": "배당금", "d": "주주에게 주는 이익금"}, 
    {"t": "시가총액", "d": "기업의 전체 몸값"}, {"t": "예수금", "d": "계좌 내 현금"}, 
    {"t": "매수", "d": "주식 사기"}, {"t": "매도", "d": "주식 팔기"}, 
    {"t": "손절매", "d": "손실 감수하고 매도"}, {"t": "익절", "d": "수익 확정 매도"}, 
    {"t": "공매도", "d": "빌려서 팔기"}, {"t": "상한가", "d": "최대 상승폭"}, 
    {"t": "하한가", "d": "최대 하락폭"}, {"t": "PER", "d": "주가수익비율"}, 
    {"t": "PBR", "d": "주가순자산비율"}, {"t": "물타기", "d": "단가 낮추기"}, 
    {"t": "우량주", "d": "재무 튼튼 대기업"}, {"t": "예탁금", "d": "고객이 맡긴 돈"}
]

quiz_pool = [
    {"q": "주식 시장에서 '상승장'을 의미하는 동물은?", "a": "황소(Bull)", "o": ["황소(Bull)", "곰(Bear)", "사자(Lion)"]},
    {"q": "기업의 순이익 중 일부를 주주들에게 나누어 주는 보너스는?", "a": "배당금", "o": ["배당금", "이자", "상여금"]},
    {"q": "주가가 급락할 때 시장 충격을 완화하기 위해 거래를 중단시키는 제도는?", "a": "서킷브레이커", "o": ["사이드카", "서킷브레이커", "데드캣바운스"]},
    {"q": "상장 주식수 x 주가는?", "a": "시가총액", "o": ["매출액", "시가총액", "순이익"]},
    {"q": "우량주를 뜻하는 용어는?", "a": "블루칩", "o": ["레드칩", "블루칩", "그린칩"]}
]

shop_items = {
    "👑 황금 왕관": {"price": 100, "emoji": "👑"},
    "💼 비즈니스 수트": {"price": 60, "emoji": "💼"},
    "🏎️ 슈퍼카": {"price": 150, "emoji": "🏎️"}
}

# 3. 실시간 가격 엔진
@st.cache_data(ttl=20)
def fetch_prices():
    prices = {}
    for name, ticker in stock_map.items():
        try:
            data = yf.Ticker(ticker); p = data.history(period="1d")['Close'].iloc[-1]
            if ".KS" not in ticker: p *= 1415 # 환율
            prices[name] = int(p * (1 + (np.random.rand()-0.5)*0.005))
        except: prices[name] = 100000
    return prices

# 4. 세션 상태 초기화 (5분 타이머 추가)
if 'user_name' not in st.session_state:
    st.session_state.update({
        'user_name': "", 'difficulty': "", 'balance': 0.0, 'points': 0,
        'portfolio': {s: 0 for s in stock_map}, 'trade_count': 0, 'tech_focus': 0,
        'avatar': "🐣 분석 대기 중", 'attendance': False, 'inventory': [], 'equipped': "",
        'quiz_cleared': [False] * len(quiz_pool), 'term_idx': 0, 'bots': [],
        'season_end_time': None, # 접속 시점에 설정
        'is_season_ended': False
    })

def init_bots(diff):
    names = ["퀀트마스터", "익산불개미", "여의도황소", "나스닥귀신", "버핏지망생", "단타의신", "월스트리트", "AI알고리즘", "풀매수전사"]
    base = {"초급": 50000000, "중급": 10000000, "상급": 1000000}[diff]
    return [{"닉네임": n, "자산": base * (1 + (random.random()-0.5)*0.2), "성향": "🛡️ 든든한 가디언", "난이도": diff} for n in names]

# 5. 로그인 로직
if not st.session_state.user_name:
    st.title("🏆 AI 투자 5분 시즌제 승급 챌린지")
    with st.container(border=True):
        name = st.text_input("닉네임 입력")
        diff_choice = st.selectbox("참여 등급", ["초급 (5,000만)", "중급 (1,000만)", "상급 (100만)"])
        if st.button("시스템 접속"):
            if name:
                st.session_state.user_name = name; dl = diff_choice.split()[0]
                st.session_state.difficulty = dl; st.session_state.balance = 50000000.0 if "초급" in diff_choice else 10000000.0 if "중급" in diff_choice else 1000000.0
                st.session_state.bots = init_bots(dl)
                # 💡 [핵심] 접속 시점부터 5분 타이머 시작
                st.session_state.season_end_time = datetime.now() + timedelta(minutes=5)
                st.rerun()
    st.stop()

# 6. 시즌 타이머 계산 로직
time_now = datetime.now()
time_left = st.session_state.season_end_time - time_now
seconds_left = time_left.total_seconds()

if seconds_left <= 0:
    st.session_state.is_season_ended = True
    seconds_left = 0

# 사이드바에 타이머 표시
st.sidebar.markdown(f"### ⏳ 시즌 종료까지")
if not st.session_state.is_season_ended:
    st.sidebar.subheader(f"{int(seconds_left // 60)}분 {int(seconds_left % 60)}초")
else:
    st.sidebar.error("🏁 시즌 종료 (순위 고정)")

# 7. 실시간 데이터 계산 및 행동 분석
prices = fetch_prices()
current_val = sum(st.session_state.portfolio[s] * prices[s] for s in stock_map)
total_assets = st.session_state.balance + current_val

# 시즌 진행 중일 때만 봇 자산 변동
if not st.session_state.is_season_ended:
    for bot in st.session_state.bots: bot['자산'] *= (1 + (random.random()-0.5)*0.003)

# 8. 메인 대시보드
st.title(f"{st.session_state.equipped} {st.session_state.user_name} ({st.session_state.difficulty})")
col_h1, col_h2, col_h3 = st.columns([1.5, 1.5, 1])
col_h1.metric("💵 현금 잔고", f"{st.session_state.balance:,.0f}원")
col_h2.metric("🏆 현재 자산", f"{total_assets:,.0f}원")
with col_h3:
    if not st.session_state.attendance:
        if st.button("📅 출석 체크"):
            st.session_state.balance += 50000; st.session_state.points += 10; st.session_state.attendance = True; st.rerun()
    else: st.success("✅ 출석 완료")

st.divider()

# 9. 기능 통합 탭
tab_market, tab_quiz, tab_academy, tab_shop = st.tabs(["🛒 거래소 & 랭킹", "❓ 주식 퀴즈", "📚 투자 사전", "🛍️ 상점/꾸미기"])

with tab_market:
    m_col, r_col = st.columns([1.8, 1.2])
    with m_col:
        st.subheader("🛒 실시간 마켓")
        if st.session_state.is_season_ended:
            st.warning("시즌이 종료되어 거래를 할 수 없습니다. 승급 여부를 확인하세요!")
        
        qty = st.number_input("거래 수량 설정", min_value=1, value=1, disabled=st.session_state.is_season_ended)
        st_items = list(prices.items())
        for i in range(0, len(st_items), 2):
            cols = st.columns(2)
            for j in range(2):
                if i+j < len(st_items):
                    n, p = st_items[i+j]
                    with cols[j].container(border=True):
                        st.write(f"### {n}"); st.write(f"가격: {p:,}원 | 보유: {st.session_state.portfolio[n]}주")
                        b_col, s_col = st.columns(2)
                        # 시즌 종료 시 버튼 비활성화
                        if b_col.button(f"매수", key=f"b_{n}", disabled=st.session_state.is_season_ended):
                            if st.session_state.balance >= p * qty:
                                st.session_state.balance -= p * qty; st.session_state.portfolio[n] += qty
                                st.session_state.trade_count += 1; st.rerun()
                        if s_col.button(f"매도", key=f"s_{n}", disabled=st.session_state.is_season_ended):
                            if st.session_state.portfolio[n] >= qty:
                                st.session_state.balance += p * qty; st.session_state.portfolio[n] -= qty
                                st.session_state.trade_count += 1; st.rerun()
    with r_col:
        st.subheader(f"🏆 {st.session_state.difficulty} 시즌 랭킹")
        user_rank_info = {"닉네임": f"{st.session_state.user_name} ⭐", "자산": total_assets}
        all_p = sorted(st.session_state.bots + [user_rank_info], key=lambda x: x["자산"], reverse=True)
        
        user_final_rank = 10
        for idx, p in enumerate(all_p):
            if "⭐" in p["닉네임"]: user_final_rank = idx + 1
            medal = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else f"{idx+1}위"
            st.markdown(f'<div class="rank-card">{medal} {p["닉네임"]} <br> 자산: {p["자산"]:,.0f}원</div>', unsafe_allow_html=True)
        
        # 💡 [핵심] 시즌 종료 후 승급 로직
        if st.session_state.is_season_ended:
            st.divider()
            if user_final_rank <= 3:
                st.success(f"🎊 시즌 종료! 최종 {user_final_rank}위로 승급 대상입니다.")
                if st.session_state.difficulty == "초급":
                    if st.button("🚀 중급 스테이지로 승급"):
                        st.session_state.update({'difficulty': "중급", 'balance': 10000000.0, 'portfolio': {s: 0 for s in stock_map}, 'is_season_ended': False, 'season_end_time': datetime.now() + timedelta(minutes=5), 'bots': init_bots("중급")})
                        st.rerun()
                elif st.session_state.difficulty == "중급":
                    if st.button("🔥 상급 스테이지로 승급"):
                        st.session_state.update({'difficulty': "상급", 'balance': 1000000.0, 'portfolio': {s: 0 for s in stock_map}, 'is_season_ended': False, 'season_end_time': datetime.now() + timedelta(minutes=5), 'bots': init_bots("상급")})
                        st.rerun()
                else: st.balloons(); st.write("👑 당신은 최고의 자산가입니다!")
            else:
                st.error(f"😢 최종 {user_final_rank}위로 아쉽게 승급에 실패했습니다.")
                if st.button("🔄 시즌 재도전 (초기화)"):
                    st.session_state.update({'is_season_ended': False, 'season_end_time': datetime.now() + timedelta(minutes=5), 'balance': 50000000.0 if st.session_state.difficulty == "초급" else 10000000.0 if st.session_state.difficulty == "중급" else 1000000.0, 'portfolio': {s: 0 for s in stock_map}})
                    st.rerun()

with tab_quiz:
    st.header("🧠 주식 상식 퀴즈 (중복 보상 불가)")
    for i, item in enumerate(quiz_pool):
        if st.session_state.quiz_cleared[i]:
            st.success(f"✅ Q{i+1} 완료! (보상 지급됨)")
        else:
            with st.container():
                st.markdown(f'<div class="quiz-container"><b>Q{i+1}. {item["q"]}</b></div>', unsafe_allow_html=True)
                ans = st.radio("정답 선택", item['o'], key=f"q_{i}", index=None)
                if st.button(f"정답 확인 (Q{i+1})", key=f"btn_{i}"):
                    if ans == item['a']:
                        st.session_state.quiz_cleared[i] = True; st.session_state.balance += 10000; st.session_state.points += 10; st.rerun()
                    else: st.error("오답!")

with tab_academy:
    st.header("📚 주식 용어 사전 (5개씩 순환)")
    start = st.session_state.term_idx
    for t in terms_pool[start:start+5]:
        st.markdown(f'<div class="term-box"><b>{t["t"]}</b>: {t["d"]}</div>', unsafe_allow_html=True)
    if st.button("🔄 다음 용어 보기"):
        st.session_state.term_idx = (st.session_state.term_idx + 5) % len(terms_pool); st.rerun()

with tab_shop:
    if st.button("🔄 시스템 리셋"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
