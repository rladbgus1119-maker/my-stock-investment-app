import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import numpy as np
import random
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. 시스템 설정
st.set_page_config(page_title="AI 퀀트 유니버스 v30", layout="wide")

# 💡 [피드백 반영] 그래프 피로도 감소를 위해 새로고침 주기를 10초(10000ms)로 변경
st_autorefresh(interval=10000, key="global_tick")

# 2. 세션 상태 초기화
if 'user_name' not in st.session_state:
    st.session_state.update({
        'user_name': "", 'tier': "초급", 'balance': 0.0, 'points': 0,
        'portfolio': {}, 'trade_log': [], 'messages': [], 
        'inventory': [], 'equipped': "🥚", 'daily_quiz': False, 'daily_check': False,
        'trade_count': 0, 'tech_focus': 0, 'avatar_type': "🌱 투자 꿈나무",
        'season_end': None, 'quiz_cleared': [False]*5, 'term_idx': 0,
        'bots': [] # 리그별 경쟁 봇 데이터
    })

# 3. 데이터 및 티어 설정
stock_map = {
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", 
    "NVIDIA": "NVDA", "애플": "AAPL", "테슬라": "TSLA"
}

tier_cfg = {
    "초급": {"seed": 100000000, "pt_mul": 1.0, "safe_net": 1000000, "limit": 500000, "color": "#238636"},
    "중급": {"seed": 50000000, "pt_mul": 2.5, "safe_net": 500000, "limit": 200000, "color": "#1f6feb"},
    "고급": {"seed": 10000000, "pt_mul": 5.0, "safe_net": 100000, "limit": 50000, "color": "#8957e5"}
}

# 4. 화이트 테마 및 UI 스타일링
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #000000; }
    .metric-card { background: #f8fafc; padding: 20px; border-radius: 15px; border: 1px solid #e2e8f0; color: black; }
    .rank-card { background: #ffffff; padding: 12px; border-radius: 10px; border: 1px solid #e2e8f0; margin-bottom: 8px; color: black; border-left: 5px solid #3b82f6; }
    .chat-box { background: #f1f5f9; border: 1px solid #cbd5e1; height: 300px; overflow-y: auto; padding: 15px; border-radius: 10px; color: black; }
    .timer-box { background: #ef4444; color: white !important; padding: 15px; border-radius: 12px; text-align: center; font-weight: bold; }
    .term-box { background: #f8fafc; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0; margin-bottom: 10px; color: black; }
    </style>
""", unsafe_allow_html=True)

# 5. 핵심 엔진 함수
@st.cache_data(ttl=60) # 데이터 캐싱 시간을 늘려 그래프 변화 속도 조절
def fetch_stock(name):
    try:
        df = yf.download(stock_map[name], period="5d", interval="30m", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        curr = int(df['Close'].iloc[-1] * (1 if ".KS" in stock_map[name] else 1410))
        return curr, df
    except: return 100000, None

def init_bots(league):
    names = ["퀀트마스터", "익산불개미", "여의도황소", "나스닥귀신", "버핏지망생", "단타의신"]
    base = tier_cfg[league]['seed']
    return [{"닉네임": n, "자산": base * (1 + (random.random()-0.5)*0.15)} for n in names]

# --- 💡 [피드백 반영] 6. 로그인 화면 (난이도 선택 포함) ---
if not st.session_state.user_name:
    st.title("🚀 AI 투자 RPG: 퀀트 유니버스")
    st.markdown("### 환영합니다! 투자를 시작하기 전 설정을 완료해주세요.")
    
    with st.container(border=True):
        col_l, col_r = st.columns(2)
        with col_l:
            u_name = st.text_input("사용자 닉네임", placeholder="이름을 입력하세요")
        with col_r:
            u_tier = st.selectbox("참여 리그(난이도) 선택", ["초급", "중급", "고급"], 
                                help="초급: 1억 / 중급: 5천만 / 고급: 1천만 시드머니 지급")
        
        st.write(f"✅ **{u_tier}** 리그 선택 시 **{tier_cfg[u_tier]['seed']:,}원**이 지급됩니다.")
        
        if st.button("시작하기", use_container_width=True):
            if u_name:
                st.session_state.update({
                    'user_name': u_name, 'tier': u_tier, 
                    'balance': tier_cfg[u_tier]['seed'], 
                    'portfolio': {s: 0 for s in stock_map},
                    'bots': init_bots(u_tier),
                    'season_end': datetime.now() + timedelta(minutes=10)
                })
                st.rerun()
            else: st.error("닉네임을 입력해야 합니다!")
    st.stop()

# 실시간 자산 및 랭킹 데이터 계산
current_prices = {}; total_stock_val = 0
for s in stock_map:
    p, _ = fetch_stock(s)
    current_prices[s] = p
    total_stock_val += st.session_state.portfolio.get(s, 0) * p
total_assets = st.session_state.balance + total_stock_val

# 봇 자산 실시간 변동 (경쟁심 유발)
for b in st.session_state.bots: b['자산'] *= (1 + (random.random()-0.5)*0.01)

# --- 7. 메인 화면 구성 ---
st.sidebar.title(f"🎮 {st.session_state.tier} 리그")
st.sidebar.subheader(f"{st.session_state.equipped} {st.session_state.user_name}")
page = st.sidebar.radio("🧭 메뉴", ["🏠 대시보드", "🛒 거래소 & 랭킹", "📚 투자 아카데미", "🛍️ 상점/커뮤니티"])

# 페이지 1: 대시보드
if page == "🏠 대시보드":
    st.title(f"📊 {st.session_state.user_name}님의 투자 현황")
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 총 자산", f"{total_assets:,.0f}원")
    c2.metric("💎 포인트", f"{st.session_state.points}P")
    c3.metric("🔥 거래 횟수", f"{st.session_state.trade_count}회")

    st.divider()
    st.subheader("📈 내 포트폴리오 비중")
    if total_stock_val > 0:
        labels = [s for s in stock_map if st.session_state.portfolio.get(s,0) > 0]
        values = [st.session_state.portfolio[s] * current_prices[s] for s in labels]
        fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])
        fig_pie.update_layout(paper_bgcolor='white', margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_pie, use_container_width=True)
    else: st.info("보유 중인 주식이 없습니다.")

# 페이지 2: 거래소 및 랭킹 (피드백 반영)
elif page == "🛒 거래소 & 랭킹":
    m_col, r_col = st.columns([1.8, 1.2])
    
    with m_col:
        st.subheader("📉 실시간 시세 차트")
        target = st.selectbox("종목 선택", list(stock_map.keys()))
        p, df = fetch_stock(target)
        if df is not None:
            # 화이트 배경의 전문 차트
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df.index.strftime('%H:%M'), y=df['Close'], 
                                     mode='lines+markers', line=dict(color='#3b82f6', width=2)))
            fig.update_layout(paper_bgcolor='white', plot_bgcolor='white',
                            xaxis=dict(type='category', showgrid=True, gridcolor='#f1f5f9'),
                            yaxis=dict(showgrid=True, gridcolor='#f1f5f9'),
                            height=400, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
        
        st.write(f"### 현재가: **{p:,}원**")
        qty = st.number_input("수량", min_value=1, value=1)
        b, s = st.columns(2)
        if b.button("매수", use_container_width=True):
            if st.session_state.balance >= p*qty:
                st.session_state.balance -= p*qty; st.session_state.portfolio[target] += qty
                st.session_state.trade_count += 1; st.rerun()
        if s.button("매도", use_container_width=True):
            if st.session_state.portfolio[target] >= qty:
                st.session_state.balance += p*qty; st.session_state.portfolio[target] -= qty
                st.session_state.trade_count += 1; st.rerun()

    with r_col:
        # 💡 [피드백 반영] 실시간 랭킹 시스템
        st.subheader(f"🏆 {st.session_state.tier} 리그 랭킹")
        my_data = {"닉네임": f"{st.session_state.user_name} (나) ⭐", "자산": total_assets}
        all_ranks = sorted(st.session_state.bots + [my_data], key=lambda x: x['자산'], reverse=True)
        
        for idx, player in enumerate(all_ranks):
            medal = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else f"{idx+1}위"
            st.markdown(f"""
                <div class="rank-card">
                    <b>{medal} {player['닉네임']}</b><br>
                    자산: {player['자산']:,.0f}원
                </div>
            """, unsafe_allow_html=True)

# 페이지 3: 아카데미 (팁/퀴즈/사전)
elif page == "📚 투자 아카데미":
    st.title("📚 투자 지식 아카데미")
    t1, t2, t3 = st.tabs(["💡 투자 팁", "❓ 포인트 퀴즈", "📖 주식 사전"])
    
    with t1:
        st.write("### 리그별 포인트 혜택")
        st.info(f"현재 당신의 리그는 **{st.session_state.tier}** 입니다. 포인트 획득 배율: **{tier_cfg[st.session_state.tier]['pt_mul']}배**")
        st.write("- 시드머니가 적은 고급 리그일수록 포인트 보상이 기하급수적으로 늘어납니다.")
    with t2:
        if not st.session_state.daily_quiz:
            ans = st.radio("주식 시장에서 'Bear Market'은 어떤 시장인가요?", ["상승장", "하락장", "횡보장"])
            if st.button("정답 제출"):
                if ans == "하락장":
                    st.session_state.points += int(100 * tier_cfg[st.session_state.tier]['pt_mul'])
                    st.session_state.daily_quiz = True; st.rerun()
        else: st.success("✅ 오늘 퀴즈를 맞혔습니다!")
    with t3:
        for t in ["코스피", "배당", "시가총액", "공매도", "블루칩"]:
            st.markdown(f'<div class="term-box"><b>{t}</b>: 주식 투자의 필수 용어입니다.</div>', unsafe_allow_html=True)

# 페이지 4: 상점 및 커뮤니티
elif page == "🛍️ 상점/커뮤니티":
    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("🛍️ 포인트 상점")
        st.write(f"보유 포인트: **{st.session_state.points} P**")
        # 티어별 아이템 해금 로직
        for t, items in shop_items.items():
            st.write(f"**[{t} 리그 전용]**")
            cols = st.columns(2)
            for i, (name, price) in enumerate(items.items()):
                locked = (t == "고급" and st.session_state.tier != "고급") or (t == "중급" and st.session_state.tier == "초급")
                with cols[i % 2]:
                    if locked: st.button(f"🔒 {name}", disabled=True)
                    elif name in st.session_state.inventory: 
                        if st.button(f"장착: {name}"): st.session_state.equipped = name.split()[-1]
                    else:
                        if st.button(f"구매: {name} ({price}P)"):
                            if st.session_state.points >= price:
                                st.session_state.points -= price; st.session_state.inventory.append(name); st.rerun()
    with c2:
        st.subheader("💬 실시간 광장")
        st.markdown('<div class="chat-box">', unsafe_allow_html=True)
        for m in st.session_state.messages[-10:]:
            st.write(f"**{m['user']}**: {m['text']}")
        st.markdown('</div>', unsafe_allow_html=True)
        with st.form("chat", clear_on_submit=True):
            m = st.text_input("메시지")
            if st.form_submit_button("전송"):
                st.session_state.messages.append({"user": st.session_state.user_name, "text": m}); st.rerun()

st.sidebar.divider()
if st.sidebar.button("🔄 로그아웃/초기화"):
    for k in list(st.session_state.keys()): del st.session_state[k]
    st.rerun()
