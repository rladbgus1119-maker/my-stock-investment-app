import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import numpy as np
import random
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. 시스템 설정
st.set_page_config(page_title="AI 퀀트 유니버스 v31", layout="wide")

# 타이머와 실시간 랭킹을 위해 2초마다 자동 새로고침
st_autorefresh(interval=2000, key="global_tick")

# 2. 전역 데이터 정의 (오류 해결: shop_items를 최상단에 배치)
stock_map = {
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", 
    "NVIDIA": "NVDA", "애플": "AAPL", "테슬라": "TSLA", "마이크로소프트": "MSFT"
}

tier_cfg = {
    "초급": {"seed": 100000000, "pt_mul": 1.0, "limit": 500000, "next": "중급"},
    "중급": {"seed": 50000000, "pt_mul": 2.5, "limit": 200000, "next": "고급"},
    "고급": {"seed": 10000000, "pt_mul": 5.0, "limit": 50000, "next": "마스터"}
}

shop_items = {
    "초급": {"🎈 풍선": 50, "👓 연습용 안경": 150},
    "중급": {"💼 서류가방": 1000, "📱 최신 폰": 2500},
    "고급": {"👑 황금 왕관": 10000, "🏎️ 슈퍼카": 50000}
}

terms_pool = [
    {"t": "코스피(KOSPI)", "d": "한국 거래소에 상장된 종합주가지수."},
    {"t": "블루칩", "d": "수익성, 성장성, 안정성이 높은 우량주."},
    {"t": "배당금", "d": "기업의 이익 중 일부를 주주에게 나누어 주는 현금."},
    {"t": "시가총액", "d": "상장 주식수 × 현재 주가. 기업의 전체 몸값."},
    {"t": "PER", "d": "주가가 1주당 수익의 몇 배인지 나타내는 지표."},
    {"t": "PBR", "d": "주가가 1주당 자산의 몇 배인지 나타내는 지표."},
    {"t": "공매도", "d": "주가 하락을 예상하고 빌려서 파는 전략."},
    {"t": "예수금", "d": "주식을 사기 위해 계좌에 넣어둔 현금."},
    {"t": "익절", "d": "수익이 난 상태에서 이익을 확정하는 매도."},
    {"t": "손절매", "d": "더 큰 손실을 막기 위해 손해를 감수하는 매도."},
    {"t": "서킷브레이커", "d": "주가 급변 시 매매를 일시 중단하는 제도."},
    {"t": "보통주", "d": "의결권을 가지는 일반적인 주식."},
    {"t": "우선주", "d": "의결권은 없으나 배당 우선권을 갖는 주식."},
    {"t": "유상증자", "d": "신주를 발행해 자금을 조달하는 것."},
    {"t": "선물(Futures)", "d": "미래의 특정 시점에 상품을 사기로 약속하는 거래."}
]

quiz_pool = [
    {"q": "주식 시장에서 '상승장'을 상징하는 동물은?", "a": "황소", "o": ["황소", "곰", "사자"]},
    {"q": "기업의 이익을 주주에게 현금으로 돌려주는 것은?", "a": "배당", "o": ["배당", "이자", "상여"]},
    {"q": "주식 가격에 총 발행 주식 수를 곱한 기업의 가치는?", "a": "시가총액", "o": ["매출액", "시가총액", "자본금"]},
    {"q": "주가가 급락할 때 시장을 진정시키려 매매를 멈추는 제도는?", "a": "서킷브레이커", "o": ["사이드카", "서킷브레이커", "데드캣"]}
]

# 3. 세션 상태 초기화
if 'user_name' not in st.session_state:
    st.session_state.update({
        'user_name': "", 'tier': "초급", 'balance': 0.0, 'points': 0,
        'portfolio': {s: 0 for s in stock_map}, 'trade_log': [], 'messages': [],
        'inventory': [], 'equipped': "🥚", 'quiz_idx': 0, 'daily_check': False,
        'trade_count': 0, 'tech_focus': 0, 'term_idx': 0,
        'bots': [], 'season_end_time': None, 'is_ended': False
    })

# 4. 스타일링 (화이트 테마)
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #000000; }
    .metric-card { background: #f8fafc; padding: 15px; border-radius: 12px; border: 1px solid #e2e8f0; }
    .rank-card { background: #ffffff; padding: 10px; border-radius: 10px; border: 1px solid #e2e8f0; margin-bottom: 8px; border-left: 5px solid #3b82f6; }
    .timer-box { background: #ef4444; color: white !important; padding: 15px; border-radius: 12px; text-align: center; font-size: 1.3rem; font-weight: bold; margin-bottom: 10px; }
    .chat-box { background: #f1f5f9; height: 300px; overflow-y: auto; padding: 10px; border-radius: 10px; border: 1px solid #cbd5e1; }
    .term-box { background: #f8fafc; padding: 12px; border-radius: 10px; border: 1px solid #e2e8f0; margin-bottom: 8px; }
    </style>
""", unsafe_allow_html=True)

# 5. 핵심 엔진
@st.cache_data(ttl=30)
def fetch_stock_data(name):
    try:
        df = yf.download(stock_map[name], period="5d", interval="30m", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        curr = int(df['Close'].iloc[-1] * (1 if ".KS" in stock_map[name] else 1410))
        return curr, df
    except: return 100000, None

def init_season_bots(league):
    names = ["퀀트마스터", "익산불개미", "여의도황소", "나스닥귀신", "버핏지망생", "풀매수전사"]
    base = tier_cfg[league]['seed']
    return [{"닉네임": n, "자산": base * (1 + (random.random()-0.1)*0.1)} for n in names]

# 6. 로그인 화면 (난이도 선택)
if not st.session_state.user_name:
    st.title("🏆 AI 투자 RPG: 5분 서바이벌 시즌")
    with st.container(border=True):
        u_name = st.text_input("닉네임")
        u_tier = st.selectbox("리그(난이도) 선택", ["초급", "중급", "고급"])
        if st.button("시즌 시작", use_container_width=True):
            if u_name:
                st.session_state.update({
                    'user_name': u_name, 'tier': u_tier, 'balance': tier_cfg[u_tier]['seed'],
                    'bots': init_season_bots(u_tier),
                    'season_end_time': datetime.now() + timedelta(minutes=5),
                    'is_ended': False
                })
                st.rerun()
    st.stop()

# --- 실시간 계산 데이터 ---
time_diff = st.session_state.season_end_time - datetime.now()
seconds_left = max(0, time_diff.total_seconds())
if seconds_left <= 0: st.session_state.is_ended = True

current_prices = {}; total_stock_val = 0
for s in stock_map:
    p, _ = fetch_stock_data(s)
    current_prices[s] = p
    total_stock_val += st.session_state.portfolio.get(s, 0) * p
total_assets = st.session_state.balance + total_stock_val

# 봇 자산 실시간 변동 (랭킹 역동성 부여)
if not st.session_state.is_ended:
    for b in st.session_state.bots: b['자산'] *= (1 + (random.random()-0.5)*0.005)

# --- 메인 화면 ---
st.sidebar.title(f"🚀 {st.session_state.tier} 리그")
st.sidebar.subheader(f"{st.session_state.equipped} {st.session_state.user_name}")
page = st.sidebar.radio("🧭 메뉴", ["🏠 홈/대시보드", "🛒 거래소 & 시즌랭킹", "📚 투자 아카데미", "🛍️ 상점/커뮤니티"])

# 페이지 1: 홈
if page == "🏠 홈/대시보드":
    st.title("📊 투자 대시보드")
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 총 자산", f"{total_assets:,.0f}원")
    c2.metric("💎 포인트", f"{st.session_state.points}P")
    c3.metric("📈 리그 등급", st.session_state.tier)
    
    st.divider()
    if not st.session_state.daily_check:
        if st.button("📅 오늘자 출석체크 (+50P)"):
            st.session_state.points += 50; st.session_state.daily_check = True; st.rerun()
    else: st.success("✅ 오늘 출석을 완료했습니다.")

# 페이지 2: 거래소 및 랭킹 (시즌 타이머 & 승급 기능)
elif page == "🛒 거래소 & 시즌랭킹":
    m_col, r_col = st.columns([1.8, 1.2])
    with m_col:
        target = st.selectbox("종목 선택", list(stock_map.keys()))
        p, df = fetch_stock_data(target)
        if df is not None:
            fig = go.Figure(data=[go.Scatter(x=df.index.strftime('%H:%M'), y=df['Close'], mode='lines+markers', line=dict(color='#3b82f6', width=2))])
            fig.update_layout(paper_bgcolor='white', plot_bgcolor='white', xaxis=dict(type='category', showgrid=True), height=400, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
        
        st.write(f"### 현재가: **{p:,}원**")
        qty = st.number_input("수량", min_value=1, value=1)
        b, s = st.columns(2)
        if b.button("매수", use_container_width=True, disabled=st.session_state.is_ended):
            if st.session_state.balance >= p*qty:
                st.session_state.balance -= p*qty; st.session_state.portfolio[target] += qty; st.rerun()
        if s.button("매도", use_container_width=True, disabled=st.session_state.is_ended):
            if st.session_state.portfolio[target] >= qty:
                st.session_state.balance += p*qty; st.session_state.portfolio[target] -= qty; st.rerun()

    with r_col:
        # 💡 시즌 타이머
        if not st.session_state.is_ended:
            st.markdown(f'<div class="timer-box">⏳ 시즌 종료까지: {int(seconds_left // 60)}분 {int(seconds_left % 60)}초</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="timer-box">🏁 시즌이 종료되었습니다!</div>', unsafe_allow_html=True)
        
        st.subheader("🏆 실시간 시즌 랭킹")
        my_rank_data = {"닉네임": f"{st.session_state.user_name} (나) ⭐", "자산": total_assets}
        all_p = sorted(st.session_state.bots + [my_rank_data], key=lambda x: x['자산'], reverse=True)
        
        my_pos = 10
        for idx, player in enumerate(all_p):
            if "⭐" in player['닉네임']: my_pos = idx + 1
            medal = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else f"{idx+1}위"
            st.markdown(f'<div class="rank-card">{medal} {player["닉네임"]} <br> 자산: {player["자산"]:,.0f}원</div>', unsafe_allow_html=True)
        
        # 💡 승급 로직
        if st.session_state.is_ended:
            if my_pos <= 3:
                st.success(f"축하합니다! {my_pos}위로 시즌을 마쳐 다음 리그 승급이 가능합니다!")
                next_tier = tier_cfg[st.session_state.tier]['next']
                if next_tier != "마스터" and st.button(f"🚀 {next_tier} 리그로 승급하기"):
                    st.session_state.update({
                        'tier': next_tier, 'balance': tier_cfg[next_tier]['seed'],
                        'portfolio': {s: 0 for s in stock_map}, 'is_ended': False,
                        'bots': init_season_bots(next_tier),
                        'season_end_time': datetime.now() + timedelta(minutes=5)
                    })
                    st.rerun()
            else:
                st.error("아쉽게도 TOP 3에 들지 못해 승급에 실패했습니다.")
                if st.button("🔄 시즌 재도전"):
                    st.session_state.update({'is_ended': False, 'season_end_time': datetime.now() + timedelta(minutes=5)})
                    st.rerun()

# 페이지 3: 아카데미 (사전 순환 & 3개 이상의 퀴즈)
elif page == "📚 투자 아카데미":
    st.title("📚 지식 성장 아카데미")
    t1, t2 = st.tabs(["📖 용어 사전", "❓ 포인트 퀴즈"])
    
    with t1:
        st.subheader("💡 주식 핵심 용어 (5개씩 순환)")
        start = st.session_state.term_idx
        current_terms = terms_pool[start:start+5]
        for t in current_terms:
            st.markdown(f'<div class="term-box"><b>{t["t"]}</b>: {t["d"]}</div>', unsafe_allow_html=True)
        if st.button("🔄 다음 용어 보기"):
            st.session_state.term_idx = (st.session_state.term_idx + 5) % len(terms_pool)
            st.rerun()

    with t2:
        st.subheader("💎 포인트 획득 퀴즈 (3문항 이상)")
        for i, q_item in enumerate(quiz_pool):
            if not st.session_state.quiz_cleared[i]:
                st.markdown(f"**Q{i+1}. {q_item['q']}**")
                ans = st.radio("정답 선택", q_item['o'], key=f"q_{i}")
                if st.button(f"Q{i+1} 정답 확인", key=f"btn_{i}"):
                    if ans == q_item['a']:
                        st.session_state.points += int(100 * tier_cfg[st.session_state.tier]['pt_mul'])
                        st.session_state.quiz_cleared[i] = True
                        st.success("정답입니다! 포인트가 지급되었습니다.")
                        st.rerun()
            else:
                st.write(f"✅ Q{i+1} 문제를 이미 맞혔습니다.")

# 페이지 4: 상점 및 커뮤니티 (오류 수정 완료)
elif page == "🛍️ 상점/커뮤니티":
    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("🛍️ 포인트 상점")
        st.write(f"보유 포인트: **{st.session_state.points} P**")
        # 💡 [NameError 해결] 전역 shop_items 사용
        for t_name, items in shop_items.items():
            st.write(f"**[{t_name} 리그 전용]**")
            sc1, sc2 = st.columns(2)
            for i, (name, price) in enumerate(items.items()):
                locked = (t_name == "고급" and st.session_state.tier != "고급") or (t_name == "중급" and st.session_state.tier == "초급")
                with [sc1, sc2][i % 2]:
                    if locked: st.button(f"🔒 {name}", disabled=True, key=f"l_{name}")
                    elif name in st.session_state.inventory:
                        if st.button(f"장착: {name}", key=f"e_{name}"): st.session_state.equipped = name.split()[-1]
                    else:
                        if st.button(f"구매: {price}P", key=f"b_{name}"):
                            if st.session_state.points >= price:
                                st.session_state.points -= price; st.session_state.inventory.append(name); st.rerun()
    with c2:
        st.subheader("💬 실시간 투자 소통")
        st.markdown('<div class="chat-box">', unsafe_allow_html=True)
        for m in st.session_state.messages[-10:]:
            st.write(f"**{m['user']}**: {m['text']}")
        st.markdown('</div>', unsafe_allow_html=True)
        with st.form("chat", clear_on_submit=True):
            m = st.text_input("메시지")
            if st.form_submit_button("전송"):
                st.session_state.messages.append({"user": st.session_state.user_name, "text": m}); st.rerun()

st.sidebar.divider()
if st.sidebar.button("🔄 시즌 초기화/로그아웃"):
    for k in list(st.session_state.keys()): del st.session_state[k]
    st.rerun()
