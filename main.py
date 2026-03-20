import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import random
from datetime import datetime, timedelta

# 1. 페이지 설정 및 다이내믹 테마 시스템
st.set_page_config(page_title="원광대 AI 퀀트 투자 터미널 v12", layout="wide")

st.sidebar.title("🎮 시스템 및 시즌 제어")
theme_choice = st.sidebar.radio("배경 테마 선택", ["라이트 모드", "다크 모드"])

if theme_choice == "다크 모드":
    bg, txt, card, border = "#0e1117", "#ffffff", "#1d2026", "#3d414a"
    plotly_template = "plotly_dark"
else:
    bg, txt, card, border = "#ffffff", "#000000", "#f8fafc", "#e2e8f0"
    plotly_template = "plotly_white"

# [가독성 강화 CSS] 모든 텍스트에 !important 적용 및 전문 앱 스타일링
st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg} !important; color: {txt} !important; }}
    h1, h2, h3, h4, p, span, div, label, .stMarkdown, .stTable {{ color: {txt} !important; }}
    [data-testid="stWidgetLabel"] p {{ color: {txt} !important; font-weight: bold; }}
    .stMetric {{ background-color: {card} !important; padding: 15px; border-radius: 12px; border: 1px solid {border} !important; }}
    .rank-card {{ background-color: {card} !important; border-radius: 10px; padding: 12px; border: 1px solid {border} !important; margin-bottom: 8px; }}
    .quiz-container {{ background-color: {card} !important; padding: 20px; border-radius: 12px; border-left: 6px solid #ef4444 !important; margin-bottom: 15px; }}
    .timer-box {{ background-color: #ef4444; color: white !important; padding: 15px; border-radius: 12px; text-align: center; font-size: 1.3rem; font-weight: bold; margin-bottom: 10px; }}
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 세트 및 설정
stock_map = {
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "NVIDIA": "NVDA",
    "애플": "AAPL", "테슬라": "TSLA", "마이크로소프트": "MSFT", "아마존": "AMZN", "현대차": "005380.KS"
}

avatar_base = {"🛡️ 든든한 가디언": "🐢", "🚀 불타는 로켓": "🚀", "⚖️ 냉철한 분석가": "💻", "🌱 투자 꿈나무": "🌱", "🐣 분석 대기 중": "🥚"}

quiz_pool = [
    {"q": "주식 시장에서 '상승장'을 의미하는 동물은?", "a": "황소(Bull)", "o": ["황소(Bull)", "곰(Bear)", "사자(Lion)"]},
    {"q": "기업 이익의 일부를 주주에게 나누어 주는 보너스는?", "a": "배당금", "o": ["배당금", "이자", "상여금"]},
    {"q": "상장 주식수 x 주가는?", "a": "시가총액", "o": ["매출액", "시가총액", "순이익"]},
    {"q": "주가가 급락할 때 시장 충격을 완화하기 위해 매매를 일시 중단하는 제도는?", "a": "서킷브레이커", "o": ["사이드카", "서킷브레이커", "손절매"]}
]

# 3. 실시간 가격 엔진 (v12 업그레이드: 캔들스틱용 과거 데이터 추가 추출)
@st.cache_data(ttl=30)
def fetch_realtime_data(target_name):
    ticker = stock_map[target_name]
    try:
        # 최근 5일간의 15분 단위 데이터 가져오기 (캔들차트용)
        data = yf.download(ticker, period="5d", interval="15m", progress=False)
        current_price = data['Close'].iloc[-1]
        if ".KS" not in ticker: current_price *= 1415 # 환율 적용
        
        # 행동분석용 실시간 가격 계산 (노이즈 추가)
        noise_price = int(current_price * (1 + (np.random.rand()-0.5)*0.005))
        return noise_price, data
    except:
        return 100000, pd.DataFrame() # 에러 발생 시 더미 데이터

# 4. 세션 상태 초기화 (v12 업그레이드: 거래 내역 로그 추가)
if 'user_name' not in st.session_state:
    st.session_state.update({
        'user_name': "", 'difficulty': "", 'balance': 0.0, 'points': 0,
        'portfolio': {s: 0 for s in stock_map}, 'trade_log': [], # 거래 기록 저장
        'trade_count': 0, 'tech_focus': 0, 'avatar': "🐣 분석 대기 중",
        'attendance': False, 'inventory': [], 'equipped': "",
        'quiz_cleared': [False] * len(quiz_pool), 'bots': [],
        'season_end_time': None, 'is_season_ended': False
    })

def init_bots(diff):
    names = ["퀀트장인", "익산불개미", "여의도황소", "나스닥귀신", "버핏지망생", "단타의신", "월스트리트", "AI알고리즘", "풀매수전사"]
    base = {"초급": 50000000, "중급": 10000000, "상급": 1000000}[diff]
    return [{"닉네임": n, "자산": base * (1 + (random.random()-0.5)*0.2), "성향": "🛡️ 든든한 가디언", "난이도": diff} for n in names]

# 5. 로그인 화면
if not st.session_state.user_name:
    st.title("👨‍🔬 원광대 AI 퀀트 투자 터미널")
    with st.container(border=True):
        name = st.text_input("닉네임 입력")
        diff_choice = st.selectbox("참여 등급", ["초급 (5,000만)", "중급 (1,000만)", "상급 (100만)"])
        if st.button("시스템 가동"):
            if name:
                st.session_state.user_name = name; dl = diff_choice.split()[0]
                st.session_state.difficulty = dl; st.session_state.balance = 50000000.0 if "초급" in diff_choice else 10000000.0 if "중급" in diff_choice else 1000000.0
                st.session_state.bots = init_bots(dl)
                st.session_state.season_end_time = datetime.now() + timedelta(minutes=5)
                st.rerun()
    st.stop()

# 6. 타이머 실시간 계산
time_left = st.session_state.season_end_time - datetime.now()
seconds_left = max(0, time_left.total_seconds())
if seconds_left <= 0: st.session_state.is_season_ended = True

st.sidebar.markdown(f"### ⏳ 시즌 종료까지")
if not st.session_state.is_season_ended:
    st.sidebar.subheader(f"{int(seconds_left // 60)}분 {int(seconds_left % 60)}초")
else:
    st.sidebar.error("🏁 시즌 종료")

# 7. 실시간 데이터 가져오기 및 총 자산 계산 (자산 고정 버그 해결 완료)
# 주의: 모든 종목의 실시간 데이터를 한 번에 가져와야 랭킹이 실시간으로 변함
live_prices = {}; stock_histories = {}
total_stock_value = 0
for n in stock_map.keys():
    price, history = fetch_realtime_data(n)
    live_prices[n] = price
    stock_histories[n] = history
    total_stock_value += st.session_state.portfolio[n] * price

# 총 자산 = 현금 잔고 + 보유 주식 실시간 가치
total_assets = st.session_state.balance + total_stock_value

# 봇 자산 실시간 변동 (시즌 종료 전까지만)
if not st.session_state.is_season_ended:
    for bot in st.session_state.bots: bot['자산'] *= (1 + (random.random()-0.5)*0.003)

# 상단 대시보드
full_avatar = f"{avatar_base.get(st.session_state.avatar, '🥚')} {st.session_state.equipped}"
st.title(f"{full_avatar} {st.session_state.user_name} 관제 센터")

col_h1, col_h2, col_h3 = st.columns([1.5, 1.5, 1])
col_h1.metric("💵 현금 잔고", f"{st.session_state.balance:,.0f}원")
col_h2.metric("🏆 실시간 총 자산", f"{total_assets:,.0f}원")
with col_h3:
    if not st.session_state.attendance:
        if st.button("📅 출석 체크 (+5만/10P)"):
            st.session_state.balance += 50000; st.session_state.points += 10; st.session_state.attendance = True; st.rerun()
    else: st.success("✅ 출석 완료")

st.divider()

# 8. 기능 통합 탭 (v12 업그레이드: 포트폴리오 차트, 거래 로그 추가)
tab_market, tab_portfolio, tab_quiz, tab_history = st.tabs(["🛒 거래소 & 랭킹", "📂 내 포트폴리오(차트)", "❓ 주식 퀴즈", "📜 거래 내역 로그"])

with tab_market:
    m_col, r_col = st.columns([2, 1])
    with m_col:
        # [v12 업그레이드] 캔들스틱 차트 및 분석 도구
        target_stock = st.selectbox("분석 및 거래 종목 선택", list(stock_map.keys()))
        df = stock_histories[target_stock]
        
        if not df.empty:
            # 전문 캔들스틱 차트 생성
            fig = go.Figure(data=[go.Candlestick(
                x=df.index,
                open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                increasing_line_color='#ef4444', decreasing_line_color='#3b82f6', # 한국식 색상
                name='시세'
            )])
            
            # [v12 업그레이드] 기술적 분석: 5일 이동평균선 추가
            df['MA5'] = df['Close'].rolling(window=5).mean()
            fig.add_trace(go.Scatter(x=df.index, y=df['MA5'], mode='lines', line=dict(color='#f59e0b', width=1.5), name='5일 이동평균선'))

            fig.update_layout(
                title=f"📈 {target_stock} 5일 분석 차트 (15분 봉)",
                template=plotly_template,
                xaxis_rangeslider_visible=False,
                height=500,
                margin=dict(l=10, r=10, t=40, b=10)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("데이터를 불러오지 못했습니다.")

        # 거래 UI
        qty = st.number_input("거래 수량 설정", min_value=1, value=1, disabled=st.session_state.is_season_ended)
        price = live_prices[target_stock]
        b_col, s_col = st.columns(2)
        
        if b_col.button(f"매수 ({price:,}원)", key="btn_buy", disabled=st.session_state.is_season_ended):
            if st.session_state.balance >= price * qty:
                st.session_state.balance -= price * qty; st.session_state.portfolio[target_stock] += qty
                st.session_state.trade_count += 1
                # [v12 업그레이드] 거래 로그 기록
                st.session_state.trade_log.append({"시간": datetime.now().strftime("%H:%M:%S"), "종목": target_stock, "종류": "매수", "수량": qty, "가격": price})
                if target_stock in ["NVIDIA", "애플", "테슬라"]: st.session_state.tech_focus += 1
                st.rerun()
        if s_col.button(f"매도 ({price:,}원)", key="btn_sell", disabled=st.session_state.is_season_ended):
            if st.session_state.portfolio[target_stock] >= qty:
                st.session_state.balance += price * qty; st.session_state.portfolio[target_stock] -= qty
                st.session_state.trade_count += 1
                st.session_state.trade_log.append({"시간": datetime.now().strftime("%H:%M:%S"), "종목": target_stock, "종류": "매도", "수량": qty, "가격": price})
                st.rerun()
    
    with r_col:
        st.subheader(f"🏆 {st.session_state.difficulty} 시즌 랭킹")
        user_rank_info = {"닉네임": f"{st.session_state.user_name} ⭐", "자산": total_assets}
        all_p = sorted(st.session_state.bots + [user_rank_info], key=lambda x: x["자산"], reverse=True)
        
        user_final_rank = 10
        for idx, p in enumerate(all_p):
            if "⭐" in p["닉네임"]: user_final_rank = idx + 1
            medal = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else f"{idx+1}위"
            st.markdown(f'<div class="rank-card">{medal} {p["닉네임"]} <br> 자산: {p["자산"]:,.0f}원</div>', unsafe_allow_html=True)
        
        # 💡 [핵심] 랭킹 바로 밑에 큼직한 타이머 배치
        if not st.session_state.is_season_ended:
            st.markdown(f'<div class="timer-box">⏳ 시즌 종료까지: {int(seconds_left // 60)}분 {int(seconds_left % 60)}초</div>', unsafe_allow_html=True)
            if st.button("🔄 시세 및 순위 새로고침"): st.rerun()
        else:
            # 승급 시스템 로직 (5분 시즌 종료 후 작동)
            st.divider()
            if user_final_rank <= 3:
                st.success(f"🎊 최종 {user_final_rank}위! 다음 스테이지 승급 가능")
                target = "중급" if st.session_state.difficulty == "초급" else "상급"
                if st.session_state.difficulty != "상급" and st.button(f"🚀 {target} 스테이지 승급하기"):
                    st.session_state.update({'difficulty': target, 'balance': 10000000.0 if target=="중급" else 1000000.0, 'portfolio': {s: 0 for s in stock_map}, 'trade_log': [], 'is_season_ended': False, 'season_end_time': datetime.now() + timedelta(minutes=5), 'bots': init_bots(target)})
                    st.rerun()
            else:
                st.error("아쉽게 승급에 실패했습니다. (TOP 3 진입 실패)"); st.button("🔄 시즌 재도전", on_click=lambda: st.session_state.update({'is_season_ended': False, 'season_end_time': datetime.now() + timedelta(minutes=5), 'balance': 50000000.0 if st.session_state.difficulty == "초급" else 10000000.0 if st.session_state.difficulty == "중급" else 1000000.0, 'portfolio': {s: 0 for s in stock_map}, 'trade_log': []}))

# [탭 2: 내 포트폴리오 - v12 업그레이드 원형 차트 추가]
with tab_portfolio:
    st.header("📂 내 자산 상세 분석")
    col_v1, col_v2 = st.columns([1, 1.5])
    
    with col_v1:
        st.subheader("📊 자산 구성")
        st.metric("가용 현금", f"{st.session_state.balance:,.0f}원")
        st.metric("주식 평가액", f"{total_stock_value:,.0f}원")
        st.divider()
        # 보유 종목 리스트
        for s in stock_map.keys():
            if st.session_state.portfolio[s] > 0:
                st.write(f"**{s}**: {st.session_state.portfolio[s]}주 ({st.session_state.portfolio[s]*live_prices[s]:,.0f}원)")

    with col_v2:
        st.subheader("🍕 자산 배분 비중 (원형 차트)")
        if total_stock_value > 0:
            labels = [s for s in stock_map.keys() if st.session_state.portfolio[s] > 0]
            values = [st.session_state.portfolio[s] * live_prices[s] for s in labels]
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=labels, values=values,
                hole=.3, # 도넛 차트 형태
                textinfo='label+percent',
                marker=dict(colors=['#ef4444', '#3b82f6', '#f59e0b', '#22c55e', '#a855f7']) # 개성있는 색상
            )])
            fig_pie.update_layout(template=plotly_template, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("아직 보유 중인 주식이 없습니다. 거래소에서 주식을 매수해 보세요!")

# [탭 3: 퀴즈 - 순수 주식 문제 및 중복 보상 해결 완료]
with tab_quiz:
    st.header("🧠 주식 상식 퀴즈")
    st.write("문제를 맞히면 10,000원과 10P가 지급됩니다. (각 문제당 1회 한정)")
    for i, item in enumerate(quiz_pool):
        if st.session_state.quiz_cleared[i]: st.success(f"✅ Q{i+1} 완료! (보상 지급됨)")
        else:
            with st.container():
                st.markdown(f'<div class="quiz-container"><b>Q{i+1}. {item["q"]}</b></div>', unsafe_allow_html=True)
                ans = st.radio("정답 선택", item['o'], key=f"q_{i}", index=None)
                if st.button("정답 제출", key=f"btn_{i}"):
                    if ans == item['a']:
                        st.session_state.quiz_cleared[i] = True; st.session_state.balance += 10000; st.session_state.points += 10; st.balloons(); st.rerun()
                    else: st.error("오답입니다!")

# [탭 4: 거래 내역 로그 - v12 업그레이드 추가]
with tab_history:
    st.header("📜 시즌 거래 기록 로그")
    if st.session_state.trade_log:
        # 최근 거래가 위로 오도록 역순 출력
        df_log = pd.DataFrame(st.session_state.trade_log).iloc[::-1]
        st.table(df_log) # 깔끔한 표 형태로 출력
    else:
        st.info("아직 거래 내역이 없습니다.")

st.divider()
if st.button("🔄 시스템 초기화 (모든 데이터 리셋)"):
    for k in list(st.session_state.keys()): del st.session_state[k]
    st.rerun()
st.latex(r"Asset_{total} = Cash + \sum (Price_{real} \times Quantity)")
