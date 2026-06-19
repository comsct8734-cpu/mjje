import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np

# 페이지 설정
st.set_page_config(
    page_title="Global Top 10 Stock Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 제목
st.title("📊 글로벌 시가총액 Top 10 주식 대시보드")
st.markdown("---")

# 글로벌 시가총액 top 10 기업
top_10_companies = {
    'AAPL': 'Apple',
    'MSFT': 'Microsoft',
    'GOOGL': 'Alphabet (Google)',
    'AMZN': 'Amazon',
    'NVDA': 'NVIDIA',
    'TSLA': 'Tesla',
    'META': 'Meta',
    'BRK.B': 'Berkshire Hathaway',
    'AVGO': 'Broadcom',
    'ASML': 'ASML'
}

# 캐싱을 통한 데이터 로드 최적화
@st.cache_data
def fetch_stock_data(ticker, start_date, end_date):
    try:
        data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        data['Return %'] = data['Adj Close'].pct_change() * 100
        return data
    except Exception as e:
        st.error(f"❌ {ticker} 데이터 로드 실패: {str(e)}")
        return None

# 날짜 설정
end_date = datetime.now()
start_date = end_date - timedelta(days=365)

# 사이드바 설정
st.sidebar.header("⚙️ 설정")
selected_stocks = st.sidebar.multiselect(
    "주식 선택",
    list(top_10_companies.keys()),
    default=['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA'],
    format_func=lambda x: f"{x} - {top_10_companies[x]}"
)

chart_type = st.sidebar.radio(
    "차트 유형",
    ["종가 추이", "수익률(%) 비교", "일일 변화율"]
)

# 데이터 로드
st.sidebar.info("📡 데이터를 로드하는 중입니다...")

stock_data = {}
for ticker in selected_stocks:
    data = fetch_stock_data(ticker, start_date, end_date)
    if data is not None:
        stock_data[ticker] = data

if not stock_data:
    st.error("선택한 주식의 데이터를 로드할 수 없습니다.")
    st.stop()

# 메인 대시보드
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("📌 분석 기간", f"{(end_date - start_date).days}일")

with col2:
    st.metric("📊 선택된 주식", len(selected_stocks))

with col3:
    st.metric("📈 마지막 업데이트", end_date.strftime("%Y-%m-%d"))

st.markdown("---")

# 차트 1: 종가 추이
if chart_type == "종가 추이":
    st.subheader("📈 종가 추이")
    
    fig = go.Figure()
    
    for ticker in selected_stocks:
        data = stock_data[ticker]
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['Adj Close'],
            mode='lines',
            name=f"{ticker} - {top_10_companies[ticker]}",
            line=dict(width=2)
        ))
    
    fig.update_layout(
        title="최근 1년 종가 변동",
        xaxis_title="날짜",
        yaxis_title="종가 ($)",
        hovermode='x unified',
        template="plotly_white",
        height=500,
        font=dict(size=11)
    )
    
    st.plotly_chart(fig, use_container_width=True)

# 차트 2: 수익률(%) 비교
elif chart_type == "수익률(%) 비교":
    st.subheader("💹 수익률(%) 비교")
    
    # 각 주식의 누적 수익률 계산
    returns_data = {}
    for ticker in selected_stocks:
        data = stock_data[ticker]
        initial_price = data['Adj Close'].iloc[0]
        cumulative_return = ((data['Adj Close'] - initial_price) / initial_price) * 100
        returns_data[ticker] = cumulative_return
    
    fig = go.Figure()
    
    for ticker in selected_stocks:
        fig.add_trace(go.Scatter(
            x=stock_data[ticker].index,
            y=returns_data[ticker],
            mode='lines',
            name=f"{ticker} - {top_10_companies[ticker]}",
            line=dict(width=2)
        ))
    
    fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="기준선")
    
    fig.update_layout(
        title="누적 수익률 (%)",
        xaxis_title="날짜",
        yaxis_title="수익률 (%)",
        hovermode='x unified',
        template="plotly_white",
        height=500,
        font=dict(size=11)
    )
    
    st.plotly_chart(fig, use_container_width=True)

# 차트 3: 일일 변화율
elif chart_type == "일일 변화율":
    st.subheader("📊 일일 변화율 분포")
    
    fig = go.Figure()
    
    for ticker in selected_stocks:
        data = stock_data[ticker]
        daily_returns = data['Return %'].dropna()
        
        fig.add_trace(go.Box(
            y=daily_returns,
            name=f"{ticker} - {top_10_companies[ticker]}",
            boxmean='sd'
        ))
    
    fig.update_layout(
        title="일일 변화율 분포 (Box Plot)",
        yaxis_title="일일 변화율 (%)",
        template="plotly_white",
        height=500,
        font=dict(size=11),
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# 통계 테이블
st.subheader("📋 주요 통계")

stats_data = []
for ticker in selected_stocks:
    data = stock_data[ticker]
    
    current_price = data['Adj Close'].iloc[-1]
    start_price = data['Adj Close'].iloc[0]
    total_return = ((current_price - start_price) / start_price) * 100
    
    max_price = data['Adj Close'].max()
    min_price = data['Adj Close'].min()
    volatility = data['Return %'].std()
    
    stats_data.append({
        '종목': f"{ticker} - {top_10_companies[ticker]}",
        '현재가': f"${current_price:.2f}",
        '시작가': f"${start_price:.2f}",
        '수익률(%)': f"{total_return:.2f}%",
        '최고가': f"${max_price:.2f}",
        '최저가': f"${min_price:.2f}",
        '변동성(%)': f"{volatility:.2f}%"
    })

stats_df = pd.DataFrame(stats_data)
st.dataframe(stats_df, use_container_width=True, hide_index=True)

st.markdown("---")

# 상관관계 분석
if len(selected_stocks) > 1:
    st.subheader("🔗 상관관계 분석")
    
    correlation_data = {}
    for ticker in selected_stocks:
        correlation_data[ticker] = stock_data[ticker]['Return %'].dropna()
    
    # 같은 길이로 정렬
    min_length = min(len(v) for v in correlation_data.values())
    for ticker in selected_stocks:
        correlation_data[ticker] = correlation_data[ticker].iloc[-min_length:]
    
    corr_df = pd.DataFrame(correlation_data)
    correlation_matrix = corr_df.corr()
    
    fig = go.Figure(data=go.Heatmap(
        z=correlation_matrix.values,
        x=correlation_matrix.columns,
        y=correlation_matrix.columns,
        colorscale='RdBu',
        zmid=0,
        text=np.round(correlation_matrix.values, 2),
        texttemplate='%{text}',
        textfont={"size": 10}
    ))
    
    fig.update_layout(
        title="주식 간 수익률 상관관계",
        height=500,
        font=dict(size=11)
    )
    
    st.plotly_chart(fig, use_container_width=True)

# 하단 정보
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 12px;'>
    📊 데이터 출처: Yahoo Finance | 자동 업데이트: 매일 시장 마감 후
</div>
""", unsafe_allow_html=True)
