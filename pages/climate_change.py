import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from datetime import datetime
from scipy import stats

# 페이지 설정
st.set_page_config(
    page_title="서울 기후 변화 분석 대시보드",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일링
st.markdown("""
<style>
    .main-title {
        text-align: center;
        color: #1f77b4;
        font-size: 2.5em;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .subtitle {
        text-align: center;
        color: #555;
        font-size: 1.1em;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">🌡️ 서울 기후 변화 분석 대시보드</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">119년 일일 기온 데이터로 보는 지구 온난화 (+4.95°C, 1907~2026)</p>', unsafe_allow_html=True)
st.markdown("---")

# =========== 데이터 로드 및 전처리 ===========
@st.cache_data
def load_and_process_data():
    df = pd.read_csv('/mnt/user-data/uploads/ta_20260619190504.csv')
    
    # 날짜 정제
    df['날짜'] = df['날짜'].str.strip()
    df['날짜'] = pd.to_datetime(df['날짜'])
    
    # 파생변수 생성
    df['연도'] = df['날짜'].dt.year
    df['월'] = df['날짜'].dt.month
    df['일'] = df['날짜'].dt.day
    df['연월'] = df['날짜'].dt.to_period('M')
    df['일교차'] = df['최고기온(℃)'] - df['최저기온(℃)']
    
    # 계절 구분
    def get_season(month):
        if month in [3, 4, 5]:
            return '봄'
        elif month in [6, 7, 8]:
            return '여름'
        elif month in [9, 10, 11]:
            return '가을'
        else:
            return '겨울'
    
    df['계절'] = df['월'].apply(get_season)
    
    # 연대 구분
    def get_decade(year):
        return (year // 10) * 10
    
    df['연대'] = df['연도'].apply(get_decade)
    
    return df

df = load_and_process_data()

# =========== 사이드바 설정 ===========
st.sidebar.header("⚙️ 설정")

chart_type = st.sidebar.radio(
    "📊 차트 유형 선택",
    ["📈 추세선 분석", "🔥 월별 히트맵", "📅 계절 분석", 
     "🏆 기온 기록 박물관", "📊 일교차 분석"],
    index=0
)

year_range = st.sidebar.slider(
    "📅 연도 범위 선택",
    int(df['연도'].min()),
    int(df['연도'].max()),
    (int(df['연도'].min()), int(df['연도'].max()))
)

seasons_selected = st.sidebar.multiselect(
    "🏷️ 계절 필터",
    ['봄', '여름', '가을', '겨울'],
    default=['봄', '여름', '가을', '겨울']
)

# 데이터 필터링
df_filtered = df[(df['연도'] >= year_range[0]) & (df['연도'] <= year_range[1]) & 
                 (df['계절'].isin(seasons_selected))]

# =========== 메인 대시보드 메트릭 ===========
col1, col2, col3, col4 = st.columns(4)

with col1:
    avg_temp = df_filtered['평균기온(℃)'].mean()
    st.metric("🌡️ 평균 기온", f"{avg_temp:.2f}°C")

with col2:
    max_temp = df_filtered['최고기온(℃)'].max()
    st.metric("🔥 최고 기온", f"{max_temp:.1f}°C")

with col3:
    min_temp = df_filtered['최저기온(℃)'].min()
    st.metric("❄️ 최저 기온", f"{min_temp:.1f}°C")

with col4:
    avg_range = df_filtered['일교차'].mean()
    st.metric("📏 평균 일교차", f"{avg_range:.2f}°C")

st.markdown("---")

# =========== 1️⃣ 추세선 분석 ===========
if chart_type == "📈 추세선 분석":
    st.subheader("📈 119년 연도별 평균 기온 추이")
    
    # 연도별 평균 기온 계산
    yearly_data = df.groupby('연도').agg({
        '평균기온(℃)': 'mean',
        '최고기온(℃)': 'mean',
        '최저기온(℃)': 'mean'
    }).reset_index()
    
    # 5년 이동평균
    yearly_data['5년이동평균'] = yearly_data['평균기온(℃)'].rolling(window=5, center=True).mean()
    
    # 선형 회귀선
    x = yearly_data['연도'].values
    y = yearly_data['평균기온(℃)'].values
    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)
    trend_line = p(x)
    
    fig = go.Figure()
    
    # 원본 데이터
    fig.add_trace(go.Scatter(
        x=yearly_data['연도'],
        y=yearly_data['평균기온(℃)'],
        mode='lines+markers',
        name='연도별 평균기온',
        line=dict(color='rgba(100, 150, 200, 0.6)', width=2),
        marker=dict(size=4),
        hovertemplate='<b>%{x}년</b><br>평균기온: %{y:.2f}°C<extra></extra>'
    ))
    
    # 5년 이동평균
    fig.add_trace(go.Scatter(
        x=yearly_data['연도'],
        y=yearly_data['5년이동평균'],
        mode='lines',
        name='5년 이동평균',
        line=dict(color='#FF6B6B', width=3),
        hovertemplate='<b>%{x}년</b><br>5년평균: %{y:.2f}°C<extra></extra>'
    ))
    
    # 트렌드선
    fig.add_trace(go.Scatter(
        x=yearly_data['연도'],
        y=trend_line,
        mode='lines',
        name='장기 추세선',
        line=dict(color='purple', width=2, dash='dash'),
        hovertemplate='<b>%{x}년</b><br>추세: %{y:.2f}°C<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"연도별 평균 기온 변화 (상승률: {z[0]:.4f}°C/년)",
        xaxis_title="연도",
        yaxis_title="평균 기온 (°C)",
        hovermode='x unified',
        template="plotly_white",
        height=600,
        font=dict(size=11)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 통계 정보
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"""
        **지구 온난화 지수**
        
        1907-1950년: +{yearly_data[yearly_data['연도']==1950]['평균기온(℃)'].values[0] - yearly_data[yearly_data['연도']==1907]['평균기온(℃)'].values[0]:.2f}°C
        """)
    
    with col2:
        st.info(f"""
        **최근 50년 변화**
        
        {int(df['연도'].max())-50}~{int(df['연도'].max())}년: +{yearly_data[yearly_data['연도']==int(df['연도'].max())]['평균기온(℃)'].values[0] - yearly_data[yearly_data['연도']==int(df['연도'].max())-50]['평균기온(℃)'].values[0]:.2f}°C
        """)
    
    with col3:
        st.info(f"""
        **총 상승량**
        
        1907~2026년: +{yearly_data['평균기온(℃)'].iloc[-1] - yearly_data['평균기온(℃)'].iloc[0]:.2f}°C
        """)

# =========== 2️⃣ 월별 히트맵 ===========
elif chart_type == "🔥 월별 히트맵":
    st.subheader("🔥 서울의 기후 지문 - 월별 × 연도 기온 분포")
    
    # 월별-연도 기온 피벗
    pivot_data = df.pivot_table(
        values='평균기온(℃)',
        index='월',
        columns='연도',
        aggfunc='mean'
    )
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot_data.values,
        x=pivot_data.columns,
        y=['1월', '2월', '3월', '4월', '5월', '6월', 
           '7월', '8월', '9월', '10월', '11월', '12월'],
        colorscale='RdBu_r',
        zmid=11.83,  # 전체 평균
        colorbar=dict(title="기온(°C)"),
        hovertemplate='<b>%{customdata}월, %{x}년</b><br>평균기온: %{z:.1f}°C<extra></extra>',
        customdata=np.repeat(np.arange(1, 13), len(pivot_data.columns)).reshape(12, -1)
    ))
    
    fig.update_layout(
        title="월별 × 연도 기온 변화",
        xaxis_title="연도",
        yaxis_title="월",
        height=500,
        font=dict(size=11)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("""
    **해석:**
    - 🔵 파란색: 평년보다 낮은 기온
    - ⚪ 흰색: 평년 기온
    - 🔴 빨간색: 평년보다 높은 기온
    - 시간이 지나면서 **빨간색이 점점 진해지는** 추세 = 지구 온난화
    """)

# =========== 3️⃣ 계절 분석 ===========
elif chart_type == "📅 계절 분석":
    st.subheader("📅 계절별 기온 분포 변화")
    
    # 계절별 데이터
    seasonal_data = []
    for season in ['봄', '여름', '가을', '겨울']:
        season_df = df[df['계절'] == season]
        seasonal_data.append({
            '계절': season,
            '평균': season_df['평균기온(℃)'].mean(),
            '최고': season_df['최고기온(℃)'].mean(),
            '최저': season_df['최저기온(℃)'].mean()
        })
    
    # 바이올린 플롯
    fig = go.Figure()
    
    for season in ['봄', '여름', '가을', '겨울']:
        season_temps = df[df['계절'] == season]['평균기온(℃)']
        fig.add_trace(go.Violin(
            y=season_temps,
            name=season,
            box_visible=True,
            meanline_visible=True,
            points=False,
            hovertemplate='<b>%{x}</b><br>기온: %{y:.1f}°C<extra></extra>'
        ))
    
    fig.update_layout(
        title="계절별 기온 분포",
        yaxis_title="평균 기온 (°C)",
        template="plotly_white",
        height=500,
        font=dict(size=11)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 계절별 통계표
    st.subheader("📊 계절별 기온 통계")
    seasonal_stats = df.groupby('계절').agg({
        '평균기온(℃)': ['mean', 'std', 'min', 'max'],
        '최고기온(℃)': 'mean',
        '최저기온(℃)': 'mean'
    }).round(2)
    
    seasonal_stats.columns = ['평균', '표준편차', '최소', '최대', '평균최고', '평균최저']
    seasonal_order = {'봄': 0, '여름': 1, '가을': 2, '겨울': 3}
    seasonal_stats = seasonal_stats.reindex(sorted(seasonal_stats.index, key=lambda x: seasonal_order[x]))
    
    st.dataframe(seasonal_stats, use_container_width=True)
    
    # 연대별 계절 비교
    st.subheader("📈 연대별 계절 기온 변화")
    
    decade_seasonal = df.groupby(['연대', '계절'])['평균기온(℃)'].mean().reset_index()
    
    fig = px.line(
        decade_seasonal,
        x='연대',
        y='평균기온(℃)',
        color='계절',
        markers=True,
        title="연대별 계절 기온 변화 추이"
    )
    
    fig.update_layout(
        xaxis_title="연대",
        yaxis_title="평균 기온 (°C)",
        height=500,
        template="plotly_white",
        font=dict(size=11)
    )
    
    st.plotly_chart(fig, use_container_width=True)

# =========== 4️⃣ 기온 기록 박물관 ===========
elif chart_type == "🏆 기온 기록 박물관":
    st.subheader("🏆 역사 속의 극한 기후")
    
    # 극값 정보
    col1, col2 = st.columns(2)
    
    with col1:
        max_temp_row = df[df['최고기온(℃)'] == df['최고기온(℃)'].max()].iloc[0]
        st.error(f"""
        ### 🔥 최고 기온 기록
        **{max_temp_row['최고기온(℃)']:.1f}°C**
        
        📅 **{max_temp_row['날짜'].strftime('%Y년 %m월 %d일')}**
        
        이날은 여름철 무더위 속 가장 높은 기온이 기록됨
        """)
    
    with col2:
        min_temp_row = df[df['최저기온(℃)'] == df['최저기온(℃)'].min()].iloc[0]
        st.info(f"""
        ### ❄️ 최저 기온 기록
        **{min_temp_row['최저기온(℃)']:.1f}°C**
        
        📅 **{min_temp_row['날짜'].strftime('%Y년 %m월 %d일')}**
        
        이날은 겨울철 혹한 속 가장 낮은 기온이 기록됨
        """)
    
    st.markdown("---")
    
    # 연도별 최고/최저 기온
    st.subheader("📊 연도별 극값 변화")
    
    yearly_extremes = df.groupby('연도').agg({
        '최고기온(℃)': 'max',
        '최저기온(℃)': 'min',
        '평균기온(℃)': 'mean'
    }).reset_index()
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=yearly_extremes['연도'],
        y=yearly_extremes['최고기온(℃)'],
        mode='markers+lines',
        name='연도별 최고기온',
        line=dict(color='red'),
        marker=dict(size=4),
        hovertemplate='<b>%{x}년</b><br>최고: %{y:.1f}°C<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=yearly_extremes['연도'],
        y=yearly_extremes['최저기온(℃)'],
        mode='markers+lines',
        name='연도별 최저기온',
        line=dict(color='blue'),
        marker=dict(size=4),
        hovertemplate='<b>%{x}년</b><br>최저: %{y:.1f}°C<extra></extra>'
    ))
    
    fig.update_layout(
        title="연도별 최고/최저 기온 기록",
        xaxis_title="연도",
        yaxis_title="기온 (°C)",
        hovermode='x unified',
        template="plotly_white",
        height=500,
        font=dict(size=11)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Top 10 기록
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 Top 10 최고 기온 기록")
        top_max = df.nlargest(10, '최고기온(℃)')[['날짜', '최고기온(℃)']].reset_index(drop=True)
        top_max['순위'] = range(1, 11)
        top_max['날짜'] = top_max['날짜'].dt.strftime('%Y-%m-%d')
        st.dataframe(top_max[['순위', '날짜', '최고기온(℃)']].set_index('순위'), use_container_width=True, hide_index=False)
    
    with col2:
        st.subheader("❄️ Top 10 최저 기온 기록")
        top_min = df.nsmallest(10, '최저기온(℃)')[['날짜', '최저기온(℃)']].reset_index(drop=True)
        top_min['순위'] = range(1, 11)
        top_min['날짜'] = top_min['날짜'].dt.strftime('%Y-%m-%d')
        st.dataframe(top_min[['순위', '날짜', '최저기온(℃)']].set_index('순위'), use_container_width=True, hide_index=False)

# =========== 5️⃣ 일교차 분석 ===========
elif chart_type == "📊 일교차 분석":
    st.subheader("📏 기온 변동성 분석 - 일교차(최고-최저)")
    
    # 연도별 평균 일교차
    yearly_range = df.groupby('연도')['일교차'].mean().reset_index()
    yearly_range.columns = ['연도', '평균일교차']
    
    # 추세선
    x = yearly_range['연도'].values
    y = yearly_range['평균일교차'].values
    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)
    trend_line = p(x)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=yearly_range['연도'],
        y=yearly_range['평균일교차'],
        mode='lines+markers',
        name='연도별 평균 일교차',
        line=dict(color='orange', width=2),
        marker=dict(size=5),
        hovertemplate='<b>%{x}년</b><br>평균 일교차: %{y:.2f}°C<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=yearly_range['연도'],
        y=trend_line,
        mode='lines',
        name='추세선',
        line=dict(color='red', width=2, dash='dash'),
        hovertemplate='<b>%{x}년</b><br>추세: %{y:.2f}°C<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"연도별 평균 일교차 변화 (추세: {z[0]:+.4f}°C/년)",
        xaxis_title="연도",
        yaxis_title="평균 일교차 (°C)",
        hovermode='x unified',
        template="plotly_white",
        height=500,
        font=dict(size=11)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 월별 일교차
    st.subheader("📅 월별 평균 일교차")
    
    monthly_range = df.groupby('월')[['일교차', '평균기온(℃)']].agg({'일교차': 'mean', '평균기온(℃)': 'mean'}).reset_index()
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=['1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월'],
        y=monthly_range['일교차'],
        name='평균 일교차',
        marker=dict(color='lightblue'),
        hovertemplate='<b>%{x}</b><br>일교차: %{y:.2f}°C<extra></extra>'
    ))
    
    fig.update_layout(
        title="월별 평균 일교차 (더운 낮과 추운 밤의 차이)",
        yaxis_title="일교차 (°C)",
        template="plotly_white",
        height=400,
        font=dict(size=11),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 통계
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📏 전체 평균 일교차", f"{df['일교차'].mean():.2f}°C")
    
    with col2:
        st.metric("📈 최대 일교차", f"{df['일교차'].max():.1f}°C")
    
    with col3:
        max_range_date = df[df['일교차'] == df['일교차'].max()]['날짜'].iloc[0]
        st.metric("📅 발생 날짜", max_range_date.strftime('%Y-%m-%d'))

# =========== 통계표 ===========
st.markdown("---")
st.subheader("📋 통계 요약")

tab1, tab2, tab3 = st.tabs(["📊 월별 통계", "📈 연대별 통계", "🎯 선택 기간 통계"])

with tab1:
    monthly_stats = df.groupby('월').agg({
        '평균기온(℃)': ['mean', 'std'],
        '최고기온(℃)': 'mean',
        '최저기온(℃)': 'mean',
        '일교차': 'mean'
    }).round(2)
    
    monthly_stats.columns = ['평균', '표준편차', '평균최고', '평균최저', '평균일교차']
    monthly_stats.index = ['1월', '2월', '3월', '4월', '5월', '6월', 
                          '7월', '8월', '9월', '10월', '11월', '12월']
    
    st.dataframe(monthly_stats, use_container_width=True)

with tab2:
    decade_stats = df.groupby('연대').agg({
        '평균기온(℃)': ['mean', 'std', 'min', 'max'],
        '일교차': 'mean'
    }).round(2)
    
    decade_stats.columns = ['평균기온', '표준편차', '최저기온', '최고기온', '평균일교차']
    decade_stats.index = [f"{int(idx)}년대" for idx in decade_stats.index]
    
    st.dataframe(decade_stats, use_container_width=True)

with tab3:
    filtered_stats = df_filtered.agg({
        '평균기온(℃)': ['mean', 'std', 'min', 'max'],
        '최고기온(℃)': 'max',
        '최저기온(℃)': 'min',
        '일교차': 'mean'
    }).round(2)
    
    summary_data = {
        '지표': ['평균 기온', '기온 표준편차', '최고 기온', '최저 기온', '평균 일교차'],
        '값': [
            f"{filtered_stats[('평균기온(℃)', 'mean')]:.2f}°C",
            f"{filtered_stats[('평균기온(℃)', 'std')]:.2f}°C",
            f"{filtered_stats[('최고기온(℃)', 'max')]:.1f}°C",
            f"{filtered_stats[('최저기온(℃)', 'min')]:.1f}°C",
            f"{filtered_stats[('일교차', 'mean')]:.2f}°C"
        ]
    }
    
    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

# =========== 하단 정보 ===========
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9em;'>

### 📊 데이터 정보
- **출처**: 기상청 (서울 관측소 코드: 108)
- **기간**: 1907년 10월 1일 ~ 2026년 6월 18일 (119년)
- **데이터 개수**: 42,931개 일일 기온 기록
- **주요 발견**: 119년간 평균 기온 상승 +4.95°C (지구 온난화)

**주의**: 이 대시보드는 교육 및 분석 목적으로만 사용됩니다. 
과거 기후 데이터가 미래를 완벽하게 예측하지 않습니다.

</div>
""", unsafe_allow_html=True)
