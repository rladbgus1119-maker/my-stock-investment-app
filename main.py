import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import numpy as np
import random
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. 시스템 설정
st.set_page_config(page_title="AI 퀀트 유니버스 v29", layout="wide")
st_autorefresh(interval=2000, key="global_tick")

# 2. 세션 상태 초기화 (오류 방지 및 모든 변수 통합)
if 'user_name' not in st.session_state:
    st.session_state.update({
        'user_name': "", 'tier': "초급", 'balance': 0.0, 'points': 0,
        'portfolio': {}, 'trade_log': [], 'messages': [], 
        'inventory': [], 'equipped': "🥚", 'daily_quiz': False, 'daily_check': False,
        'trade_count': 0, 'tech_focus': 0, 'avatar_type': "🌱 투자 꿈나무",
        'season_end': None, 'quiz_cleared': [False]*5, 'term_idx': 0
    })

# 3. 데이터 및 티어 설정
stock_map = {
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", 
    "NVIDIA": "NVDA", "애플": "AAPL", "테슬라": "TSLA"
}

tier_cfg = {
    "초급": {"seed": 100000000, "pt_mul": 1.0, "safe_net": 1000000, "limit": 500000},
    "중급": {"seed": 50000000, "pt_mul": 2.5, "safe_net": 500000, "limit": 200000},
    "고급": {"seed": 10000000, "pt_mul": 5.0, "safe_net": 100000, "limit": 50000}
}

shop_items = {
    "초급": {"🎈 풍선": 50, "👓 연습용 안경": 150},
    "중급": {"💼 비즈니스 가방": 1000, "📱 최신 스마트폰": 2500},
    "고급": {"👑 황금 왕관": 10000, "🏎️ 슈퍼카": 50000}
}

# 4. 가독성 및 차트 스타일링 (화이트 배경 최적화)
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #000000; }
    .metric-card { background: #f8fafc; padding: 20px; border-radius: 15px; border: 1px solid #e2e8f0; color: black; }
    .rank-card { background: #ffffff; padding: 12px; border-radius: 10px; border: 1px solid #e2e8f0; margin-bottom: 8px; color: black; }
    .chat-box { background: #f1f5f9; border: 1px solid #cbd5e1; height: 350px; overflow-y: auto; padding: 15px; border-radius: 10px; color: black; }
    .timer-box { background: #ef4444; color: white !important; padding: 15px; border-radius: 12px; text-align: center; font-weight: bold; }
    .term-box { background: #f8fafc; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0; margin-bottom: 10px; color: black; }
    </style>
""", unsafe_allow_html=True)

# 5. 핵심 엔진 함수
@st.cache_data(ttl=30)
def fetch_stock(name):
    try:
        df = yf.download(stock_map[name], period="5d", interval="30m", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        curr = int(df['Close'].iloc[-1] * (1 if ".KS" in stock_map[name] else 1410))
        return curr, df
    except: return 100000, None

def analyze_ai(count, tech):
    if count > 20: return "⚖️ 냉철한 분석가", "💻"
    if tech > 10: return "🚀 테크주 매니아", "🔥"
    return "🌱 투자 꿈나무", "🌱"

# 6. 로그인 화면
if not st.session_state.user_name:
    st.title("🚀 AI 투자 RPG: 유니버스")
    st.write("이미지와 같은 실시간 차트와 티어 시스템을 경험해보세요.")
    with st.container(border=True):
        name = st.text_input("닉네임")
        league = st.selectbox("난이도(리그) 선택", ["초급", "중급", "고급"])
        if st.button("시작"):
            if name:
                st.session_state.update({
                    'user_name': name, 'tier': league, 
                    'balance': tier_cfg[league]['seed'], 
                    'portfolio': {s: 0 for s in stock_map},
                    'season_end': datetime.now() + timedelta(minutes=5)
                })
                st.rerun()
    st.stop()

# 실시간 자산 계산
current_prices = {}; total_stock_val = 0
for s in stock_map:
    p, _ = fetch_stock(s)
    current_prices[s] = p
    total_stock_val += st.session_state.portfolio.get(s, 0) * p
total_assets = st.session_state.balance + total_stock_val

# --- 왕초보 구제 시스템 (시드머니 보호) ---
if total_assets < tier_cfg[st.session_state.tier]['limit']:
    st.session_state.balance += tier_cfg[st.session_state.tier]['safe_net']
    st.warning(f"💸 파산 방지! {st.session_state.tier} 등급 긴급 지원금이 지급되었습니다.")

# --- 메인 네비게이션 ---
st.sidebar.title(f"🎮 {st.session_state.user_name}의 터미널")
page = st.sidebar.radio("🧭 메뉴 이동", ["🏠 대시보드", "🛒 실시간 거래소", "📚 아카데미", "💬 커뮤니티", "🛍️ 포인트 상점"])

# 페이지 1: 대시보드
if page == "🏠 대시보드":
    st.title(f"{st.session_state.equipped} {st.session_state.user_name}님 환영합니다!")
    st.session_state.avatar_type, emoji = analyze_ai(st.session_state.trade_count, st.session_state.tech_focus)
    
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("💰 총 자산", f"{total_assets:,.0f}원")
    with col2: st.metric("💎 포인트", f"{st.session_state.points}P")
    with col3: st.metric("🏆 현재 리그", st.session_state.tier)

    st.info(f"🤖 AI 분석 결과: 당신은 **[{st.session_state.avatar_type}]** 성향입니다.")
    
    # 미션 및 출첵
    st.subheader("🎯 일일 미션")
    if not st.session_state.daily_check:
        if st.button("출석체크하고 포인트 받기"):
            st.session_state.points += int(50 * tier_cfg[st.session_state.tier]['pt_mul'])
            st.session_state.daily_check = True; st.rerun()
    else: st.success("✅ 오늘 출석 완료")

# 페이지 2: 거래소 및 등급별 랭킹
elif page == "🛒 실시간 거래소":
    m_col, r_col = st.columns([1.8, 1.2])
    with m_col:
        target = st.selectbox("종목 선택", list(stock_map.keys()))
        p, df = fetch_stock(target)
        if df is not None:
            # 📈 이미지와 동일한 화이트 배경 + 연속형 차트
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df.index.strftime('%H:%M'), y=df['Close'], 
                                     mode='lines+markers', line=dict(color='#3b82f6', width=3), name='주가 흐름'))
            fig.update_layout(
                paper_bgcolor='white', plot_bgcolor='white',
                xaxis=dict(type='category', showgrid=True, gridcolor='#e2e8f0'),
                yaxis=dict(showgrid=True, gridcolor='#e2e8f0'),
                height=450, margin=dict(l=10, r=10, t=30, b=10)
            )
            st.plotly_chart(fig, use_container_width=True)
        
        st.write(f"### 현재가: {p:,}원")
        qty = st.number_input("수량", min_value=1, value=1)
        b, s = st.columns(2)
        if b.button("매수"):
            if st.session_state.balance >= p*qty:
                st.session_state.balance -= p*qty; st.session_state.portfolio[target] += qty
                st.session_state.trade_count += 1
                if target in ["NVIDIA", "테슬라"]: st.session_state.tech_focus += 1
                st.rerun()
        if s.button("매도"):
            if st.session_state.portfolio[target] >= qty:
                st.session_state.balance += p*qty; st.session_state.portfolio[target] -= qty
                st.session_state.trade_count += 1; st.rerun()

    with r_col:
        # 타이머
        tl = st.session_state.season_end - datetime.now()
        sl = max(0, tl.total_seconds())
        if sl > 0: st.markdown(f'<div class="timer-box">⏳ 시즌 종료: {int(sl//60)}분 {int(sl%60)}초</div>', unsafe_allow_html=True)
        else: st.error("🏁 시즌 종료!")
        
        st.subheader(f"🏆 {st.session_state.tier} 리그 실시간 순위")
        st.markdown(f"<div class='rank-card'>🥇 {st.session_state.user_name} (나) <br> {total_assets:,.0f}원</div>", unsafe_allow_html=True)
        st.caption(f"※ {st.session_state.tier} 리그는 포인트 배율 {tier_cfg[st.session_state.tier]['pt_mul']}배가 적용됩니다.")

# 페이지 3: 아카데미 (팁/사전/퀴즈)
elif page == "📚 아카데미":
    t1, t2, t3 = st.tabs(["💡 투자 팁", "📖 용어 사전", "❓ 포인트 퀴즈"])
    with t1:
        st.info("고급 리그로 갈수록 포인트 획득량이 초급보다 5배 더 많아집니다!")
        st.write("- **분산 투자:** 한 종목에 몰빵하지 마세요.\n- **장기 투자:** 차트의 흔들림에 일일이 대응하지 마세요.")
    with t2:
        start = st.session_state.term_idx
        for t in ["코스피", "블루칩", "PER", "시가총액", "공매도"]:
            st.markdown(f'<div class="term-box"><b>{t}</b>: 주식 시장의 핵심 개념입니다.</div>', unsafe_allow_html=True)
    with t3:
        if not st.session_state.daily_quiz:
            ans = st.radio("기업의 이익 중 주주에게 나누어 주는 것은?", ["이자", "배당", "원금"])
            if st.button("정답 제출"):
                if ans == "배당":
                    st.session_state.points += int(100 * tier_cfg[st.session_state.tier]['pt_mul'])
                    st.session_state.daily_quiz = True; st.rerun()
        else: st.success("오늘의 퀴즈를 완료했습니다!")

# 페이지 4: 커뮤니티
elif page == "💬 커뮤니티":
    st.title("💬 실시간 투자자 광장")
    st.markdown('<div class="chat-box">', unsafe_allow_html=True)
    for m in st.session_state.messages[-10:]:
        st.write(f"**{m['user']}**: {m['text']}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    with st.form("chat", clear_on_submit=True):
        msg = st.text_input("메시지 입력")
        if st.form_submit_button("전송"):
            st.session_state.messages.append({"user": st.session_state.user_name, "text": msg})
            st.rerun()

# 페이지 5: 포인트 상점 (액세서리 해금)
elif page == "🛍️ 포인트 상점":
    st.title("🛍️ 액세서리 상점")
    st.write(f"현재 포인트: **{st.session_state.points} P**")
    for t, items in shop_items.items():
        st.subheader(f"[{t} 등급 전용]")
        cols = st.columns(len(items))
        for i, (name, price) in enumerate(items.items()):
            # 해금 로직
            locked = (t == "고급" and st.session_state.tier != "고급") or (t == "중급" and st.session_state.tier == "초급")
            with cols[i]:
                st.write(f"**{name}**")
                st.write(f"💰 {price} P")
                if locked: st.button("🔒 잠김", key=f"l_{name}", disabled=True)
                elif name in st.session_state.inventory:
                    if st.button("장착", key=f"e_{name}"): st.session_state.equipped = name.split()[-1]
                else:
                    if st.button("구매", key=f"b_{name}"):
                        if st.session_state.points >= price:
                            st.session_state.points -= price; st.session_state.inventory.append(name); st.rerun()

st.sidebar.divider()
if st.sidebar.button("🔄 전체 초기화"):
    for k in list(st.session_state.keys()): del st.session_state[k]
    st.rerun()
