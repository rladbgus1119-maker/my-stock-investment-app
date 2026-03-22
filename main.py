import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import numpy as np
import random
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. 페이지 설정 및 실시간 틱 시스템
st.set_page_config(page_title="AI 실시간 투자 터미널 v25", layout="wide")

# 1초마다 앱을 자동 새로고침하여 타이머와 실시간 자산을 반영 (1000ms = 1초)
st_autorefresh(interval=1000, key="datarefresh")

# 사이드바 테마 및 환경 설정
st.sidebar.title("🎨 UI 환경 설정")
theme_choice = st.sidebar.radio("배경 테마 선택", ["라이트 모드", "다크 모드"])

if theme_choice == "다크 모드":
    bg, txt, card, border, plotly_template = "#0e1117", "#ffffff", "#1d2026", "#3d414a", "plotly_dark"
else:
    bg, txt, card, border, plotly_template = "#ffffff", "#000000", "#f8fafc", "#e2e8f0", "plotly_white"

# 가독성 강화 CSS
st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg} !important; color: {txt} !important; }}
    h1, h2, h3, h4, p, span, div, label, .stMarkdown, .stTable {{ color: {txt} !important; }}
    [data-testid="stWidgetLabel"] p {{ color: {txt} !important; font-weight: bold; }}
    .stMetric {{ background-color: {card} !important; padding: 15px; border-radius: 12px; border: 1px solid {border} !important; }}
    .rank-card {{ background-color: {card} !important; border-radius: 10px; padding: 12px; border: 1px solid {border} !important; margin-bottom: 8px; }}
    .quiz-container {{ background-color: {card} !important; padding: 20px; border-radius: 12px; border-left: 6px solid #ef4444 !important; margin-bottom: 15px; }}
    .timer-box {{ background-color: #ef4444; color: white !important; padding: 15px; border-radius: 12px; text-align: center; font-size: 1.4rem; font-weight: bold; margin-bottom: 15px; }}
    .top-gainer-box {{ background-color: #ef4444; color: white !important; padding: 12px; border-radius: 12px; text-align: center; font-weight: bold; border: 2px solid #ffd700; }}
    .term-box {{ background-color: {card} !important; padding: 15px; border-radius: 10px; border: 1px solid {border} !important; margin-bottom: 10px; }}
    .profit {{ color: #ef4444 !important; font-weight: bold; }}
    .loss {{ color: #3b82f6 !important; font-weight: bold; }}
    .strategy-tag {{ background-color: #3b82f6; color: white !important; padding: 2px 8px; border-radius: 5px; font-size: 0.8rem; }}
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 세트
stock_map = {
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "NVIDIA": "NVDA",
    "애플": "AAPL", "테슬라": "TSLA", "마이크로소프트": "MSFT", "아마존": "AMZN", "현대차": "005380.KS"
}

terms_pool = [
    {"t": "코스피(KOSPI)", "d": "한국 거래소에 상장된 종합주가지수."},
    {"t": "블루칩(Blue Chip)", "d": "수익성, 성장성, 안정성이 높은 대형 우량주."},
    {"t": "서킷브레이커", "d": "주가 급락 시 시장 안정을 위해 매매를 일시 중단하는 제도."},
    {"t": "배당금", "d": "기업의 이익 중 일부를 주주에게 나누어 주는 현금."},
    {"t": "시가총액", "d": "상장 주식수 × 현재 주가. 기업의 전체 몸값."},
    {"t": "익절", "d": "수익이 난 상태에서 주식을 팔아 이익을 확정하는 것."},
    {"t": "손절매", "d": "더 큰 손실을 막기 위해 현재 손해를 감수하고 파는 것."},
    {"t": "공매도", "d": "주가 하락을 예상하고 주식을 빌려서 파는 투자 기법."},
    {"t": "PER", "d": "주가수익비율. 주가가 1주당 수익의 몇 배인지 나타내는 지표."},
    {"t": "PBR", "d": "주가순자산비율. 주가가 1주당 자산의 몇 배인지 나타내는 지표."},
    {"t": "예수금", "d": "주식을 사기 위해 계좌에 넣어둔 현금."},
    {"t": "보통주", "d": "주주총회에서 의결권을 가지는 일반적인 주식."},
    {"t": "우선주", "d": "의결권은 없지만 배당을 더 많이 받는 주식."},
    {"t": "유상증자", "d": "기업이 자금을 조달하기 위해 새로 주식을 발행해 파는 것."},
    {"t": "공모주", "d": "기업이 상장할 때 일반인에게 청약을 받는 주식."}
]

quiz_pool = [
    {"q": "주식 시장에서 '상승장'을 의미하는 동물은?", "a": "황소(Bull)", "o": ["황소(Bull)", "곰(Bear)", "사자(Lion)"]},
    {"q": "기업 이익의 일부를 주주에게 나누어 주는 보너스는?", "a": "배당금", "o": ["배당금", "이자", "상여금"]},
    {"q": "상장 주식수 x 주가는?", "a": "시가총액", "o": ["매출액", "시가총액", "순이익"]}
]

# 3. 실시간 주가 및 차트 엔진 (v25 수정: Multi-index 대응 및 등락률 계산)
@st.cache_data(ttl=20)
def fetch_robust_data(target_name):
    ticker = stock_map[target_name]
    try:
        df = yf.download(ticker, period="1mo", interval="60m", progress=False)
        # 💡 [핵심 해결] Multi-index 컬럼을 단일 컬럼으로 강제 변환 (그래프 안 뜨는 문제 해결)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        if df.empty: return 100000, 0, pd.DataFrame()
        
        current_p = df['Close'].iloc[-1]
        start_p = df['Open'].iloc[0] # 오늘 기준 시작가 (간략화)
        daily_change = ((current_p - start_p) / start_p) * 100
        
        if ".KS" not in ticker: current_p *= 1410 # 실시간 환율 적용
        return int(current_p), daily_change, df
    except:
        return 100000, 0, pd.DataFrame()

# 4. 세션 상태 초기화
if 'user_name' not in st.session_state:
    st.session_state.update({
        'user_name': "", 'difficulty': "", 'balance': 0.0, 'points': 0,
        'portfolio': {s: {'qty': 0, 'avg_price': 0} for s in stock_map}, # 평단가 포함 구조
        'trade_log': [], 'bots': [], 'season_end_time': None, 'is_season_ended': False,
        'quiz_cleared': [False] * len(quiz_pool), 'term_idx': 0
    })

def init_bots(diff):
    names = ["퀀트마스터", "익산불개미", "여의도황소", "나스닥귀신", "버핏지망생", "단타의신", "월스트리트", "AI알고리즘", "풀매수전사"]
    base = {"초급": 50000000, "중급": 10000000, "상급": 1000000}[diff]
    bots = []
    for n in names:
        # 봇 매매 로그 생성 (분석용)
        bot_log = [{"시간": "시즌 중", "종목": random.choice(list(stock_map.keys())), "종류": "매수", "수량": 1, "가격": 70000} for _ in range(2)]
        bots.append({
            "닉네임": n, "자산": base * (1 + (random.random()-0.5)*0.2), 
            "log": bot_log, "strategy": random.choice(["공격적 기술주 투자", "안정적 매집", "치밀한 단타"]),
            "난이도": diff
        })
    return bots

# 5. 로그인 화면 ('시작' 버튼 반영)
if not st.session_state.user_name:
    st.title("🏆 AI 투자 5분 시즌제 챌린지")
    with st.container(border=True):
        name = st.text_input("닉네임 입력")
        diff_choice = st.selectbox("참여 등급", ["초급 (5,000만)", "중급 (1,000만)", "상급 (100만)"])
        if st.button("시작"):
            if name:
                st.session_state.user_name = name; dl = diff_choice.split()[0]
                st.session_state.difficulty = dl; st.session_state.balance = 50000000.0 if "초급" in diff_choice else 10000000.0 if "중급" in diff_choice else 1000000.0
                st.session_state.bots = init_bots(dl)
                st.session_state.season_end_time = datetime.now() + timedelta(minutes=5)
                st.rerun()
    st.stop()

# 6. 실시간 자산 및 상승왕 계산
time_left = st.session_state.season_end_time - datetime.now()
sec_left = max(0, time_left.total_seconds())
if sec_left <= 0: st.session_state.is_season_ended = True

live_prices = {}; live_changes = {}; live_charts = {}
total_stock_value = 0
for n in stock_map.keys():
    p, c, h = fetch_robust_data(n)
    live_prices[n] = p; live_changes[n] = c; live_charts[n] = h
    total_stock_value += st.session_state.portfolio[n]['qty'] * p

# 💡 [핵심] 총 자산 실시간 합산 (버그 해결)
total_assets = st.session_state.balance + total_stock_value

# 💡 [핵심] 오늘의 상승왕 로직
top_stock = max(live_changes, key=live_changes.get)
top_val = live_changes[top_stock]

# 봇 자산 실시간 변동
if not st.session_state.is_season_ended:
    for bot in st.session_state.bots: bot['자산'] *= (1 + (random.random()-0.5)*0.003)

# 7. 대시보드 출력 (환영 메시지)
st.title(f"📈 {st.session_state.user_name}님 환영합니다!")
col_h1, col_h2, col_h3 = st.columns([1.2, 1.2, 1.6])
col_h1.metric("💵 가용 현금", f"{st.session_state.balance:,.0f}원")
col_h2.metric("🏆 실시간 총 자산", f"{total_assets:,.0f}원")
with col_h3:
    st.markdown(f'<div class="top-gainer-box">🚀 오늘의 상승왕: {top_stock} (+{top_val:.2f}%)</div>', unsafe_allow_html=True)

st.divider()

# 8. 기능 탭
tab_market, tab_portfolio, tab_quiz, tab_academy = st.tabs(["🛒 거래소 & 랭킹", "📂 자산 분석", "❓ 주식 퀴즈", "📚 주식 사전"])

# [탭 1: 거래소 & 10인 랭킹 & 승자 분석]
with tab_market:
    m_col, r_col = st.columns([1.8, 1.2])
    with m_col:
        target = st.selectbox("종목 선택", list(stock_map.keys()))
        df = live_charts[target]
        if not df.empty:
            # 전문 캔들스틱 차트
            fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], increasing_line_color='#ef4444', decreasing_line_color='#3b82f6')])
            fig.update_layout(template=plotly_template, xaxis_rangeslider_visible=False, height=400, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig, use_container_width=True)
        
        # 수익률 표시 및 매매 UI
        p_now = live_prices[target]; hold = st.session_state.portfolio[target]
        profit_pct = ((p_now - hold['avg_price']) / hold['avg_price'] * 100) if hold['qty'] > 0 else 0
        
        st.write(f"### 현재가: {p_now:,}원 ({live_changes[target]:+.2f}%)")
        if hold['qty'] > 0:
            color = "profit" if profit_pct > 0 else "loss"
            st.markdown(f"보유: **{hold['qty']}주** | 평단: **{hold['avg_price']:,.0f}원** | 수익률: <span class='{color}'>{profit_pct:.2f}%</span>", unsafe_allow_html=True)

        qty = st.number_input("수량 설정", min_value=1, value=1, disabled=st.session_state.is_season_ended)
        b_c, s_c = st.columns(2)
        if b_c.button(f"매수", key=f"buy_{target}", disabled=st.session_state.is_season_ended):
            if st.session_state.balance >= p_now * qty:
                new_qty = hold['qty'] + qty
                new_avg = ((hold['avg_price'] * hold['qty']) + (p_now * qty)) / new_qty
                st.session_state.balance -= p_now * qty
                st.session_state.portfolio[target] = {'qty': new_qty, 'avg_price': int(new_avg)}
                st.session_state.trade_log.append({"시간": datetime.now().strftime("%H:%M"), "종목": target, "종류": "매수", "수량": qty, "가격": p_now})
                st.rerun()
        if s_c.button(f"매도", key=f"sell_{target}", disabled=st.session_state.is_season_ended):
            if hold['qty'] >= qty:
                st.session_state.balance += p_now * qty
                st.session_state.portfolio[target]['qty'] -= qty
                st.session_state.trade_log.append({"시간": datetime.now().strftime("%H:%M"), "종목": target, "종류": "매도", "수량": qty, "가격": p_now})
                st.rerun()

    with r_col:
        if not st.session_state.is_season_ended:
            st.markdown(f'<div class="timer-box">⏳ 시즌 종료까지: {int(sec_left//60)}분 {int(sec_left%60)}초</div>', unsafe_allow_html=True)
        else:
            st.error("🏁 시즌 종료 (TOP 3 분석 가능)")

        st.subheader("🏆 시즌 랭킹 (10인)")
        user_rank_data = {"닉네임": f"{st.session_state.user_name} ⭐", "자산": total_assets, "log": st.session_state.trade_log, "strategy": "사용자 맞춤 투자"}
        all_p = sorted(st.session_state.bots + [user_rank_data], key=lambda x: x["자산"], reverse=True)
        
        user_rank = 10
        for idx, p in enumerate(all_p):
            if "⭐" in p["닉네임"]: user_rank = idx + 1
            medal = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else f"{idx+1}위"
            
            # 💡 [핵심] 시즌 종료 시 승자 분석 기능
            if st.session_state.is_season_ended and idx < 3:
                with st.expander(f"{medal} {p['닉네임']} (분석하기)"):
                    st.write(f"**💰 최종 자산:** {p['자산']:,.0f}원")
                    st.markdown(f"<span class='strategy-tag'>{p.get('strategy', 'AI 분석 전략')}</span>", unsafe_allow_html=True)
                    st.write("**📝 최근 매매 경로:**")
                    if p.get('log'): st.table(pd.DataFrame(p['log']).tail(5))
                    else: st.write("내역 없음")
            else:
                st.markdown(f'<div class="rank-card">{medal} {p["닉네임"]} <br> {p["자산"]:,.0f}원</div>', unsafe_allow_html=True)
        
        # 승급 시스템
        if st.session_state.is_season_ended and user_rank <= 3:
            st.success("승급 가능!")
            target_level = "중급" if st.session_state.difficulty == "초급" else "상급"
            if st.session_state.difficulty != "상급" and st.button(f"🚀 {target_level}으로 승급"):
                st.session_state.update({'difficulty': target_level, 'balance': 10000000.0 if target_level=="중급" else 1000000.0, 'portfolio': {s: {'qty': 0, 'avg_price': 0} for s in stock_map}, 'is_season_ended': False, 'season_end_time': datetime.now() + timedelta(minutes=5), 'bots': init_bots(target_level)})
                st.rerun()

# [기타 탭: 포트폴리오, 퀴즈, 사전]
with tab_portfolio:
    if total_stock_value > 0:
        labels = [s for s in stock_map.keys() if st.session_state.portfolio[s]['qty'] > 0]
        values = [st.session_state.portfolio[s]['qty'] * live_prices[s] for s in labels]
        st.plotly_chart(go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)]))
    else: st.info("보유 주식이 없습니다.")

with tab_quiz:
    for i, item in enumerate(quiz_pool):
        if st.session_state.quiz_cleared[i]: st.success(f"✅ Q{i+1} 완료")
        else:
            st.markdown(f'<div class="quiz-container"><b>Q{i+1}. {item["q"]}</b></div>', unsafe_allow_html=True)
            ans = st.radio("정답 선택", item['o'], key=f"q_{i}", index=None)
            if st.button("제출", key=f"btn_{i}"):
                if ans == item['a']:
                    st.session_state.quiz_cleared[i] = True; st.session_state.balance += 10000; st.rerun()

with tab_academy:
    st.header("📚 주식 용어 사전 (5개 순환)")
    start = st.session_state.term_idx
    for t in terms_pool[start:start+5]:
        st.markdown(f'<div class="term-box"><b>{t["t"]}</b>: {t["d"]}</div>', unsafe_allow_html=True)
    if st.button("🔄 다음 용어 보기"):
        st.session_state.term_idx = (st.session_state.term_idx + 5) % len(terms_pool); st.rerun()

st.divider()
st.latex(r"Profit\_Yield = \frac{Current\_Price - Avg\_Price}{Avg\_Price} \times 100 \%")
if st.button("🔄 시스템 초기화"):
    for k in list(st.session_state.keys()): del st.session_state[k]
    st.rerun()
