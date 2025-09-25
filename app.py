import streamlit as st
import pandas as pd

# --- 1. 페이지 설정 ---
st.set_page_config(
    page_title="New 경제활동인구 대시보드",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. 데이터 로딩 및 캐싱 ---
@st.cache_data
def load_data(path):
    """CSV 파일을 로드하고, '계' 행 제외 및 '실업률' 컬럼을 추가합니다."""
    try:
        df = pd.read_csv(path)
        df = df[df['지역'] != '계'].copy()
        # 실업률 계산 (실업자 / 경제활동인구 * 100), 0으로 나누는 오류 방지
        df['실업률 (%)'] = df.apply(
            lambda row: (row['실업자 (천명)'] / row['경제활동인구 (천명)'] * 100) if row['경제활동인구 (천명)'] > 0 else 0,
            axis=1
        )
        return df
    except FileNotFoundError:
        st.error(f"'{path}' 파일을 찾을 수 없습니다. 스크립트와 동일한 디렉토리에 파일이 있는지 확인해주세요.")
        return None

# --- 3. 사이드바 필터 ---
def setup_sidebar(df):
    """사이드바에 필터를 설정하고 사용자의 선택을 반환합니다."""
    st.sidebar.header("🔎 데이터 필터")
    
    selected_years = st.sidebar.multiselect(
        '년도 선택:',
        options=sorted(df['년도'].unique(), reverse=True),
        default=sorted(df['년도'].unique(), reverse=True)[:1] # 기본값: 가장 최근 연도
    )

    selected_regions = st.sidebar.multiselect(
        '지역 선택:',
        options=sorted(df['지역'].unique()),
        default=['서울특별시', '경기도', '부산광역시', '인천광역시'] # 기본값: 주요 광역/도
    )
    return selected_years, selected_regions

# --- 4. 메인 대시보드 ---
def main_dashboard(df):
    """메인 대시보드의 레이아웃과 시각화를 구성합니다."""
    st.title("🚀 경제활동인구 동향 대시보드")
    st.markdown("사이드바에서 년도와 지역을 선택하여 데이터를 실시간으로 탐색하세요.")

    selected_years, selected_regions = setup_sidebar(df)

    # 필터링된 데이터
    if not selected_years or not selected_regions:
        st.warning("표시할 데이터를 보려면 년도와 지역을 하나 이상 선택해주세요.")
        return

    filtered_df = df[df['년도'].isin(selected_years) & df['지역'].isin(selected_regions)]

    if filtered_df.empty:
        st.warning("선택하신 조건에 해당하는 데이터가 없습니다.")
        return

    # --- 4.1. 핵심 지표 (KPI) ---
    total_employed = filtered_df['취업자 (천명)'].sum()
    total_unemployed = filtered_df['실업자 (천명)'].sum()
    avg_unemployment_rate = filtered_df['실업률 (%)'].mean()

    st.markdown("### 📌 요약 (선택된 기간 및 지역)")
    col1, col2, col3 = st.columns(3)
    col1.metric("총 취업자 (천명)", f"{total_employed:,.0f}")
    col2.metric("총 실업자 (천명)", f"{total_unemployed:,.0f}")
    col3.metric("평균 실업률 (%)", f"{avg_unemployment_rate:.2f}%")

    st.markdown("---")

    # --- 4.2. 데이터 시각화 ---
    col1, col2 = st.columns((1.5, 1)) # 차트 영역을 1.5:1 비율로 나눔

    with col1:
        st.subheader("📈 연도별 취업자 수 추이")
        if len(selected_years) > 1:
            line_chart_df = filtered_df.pivot_table(index='년도', columns='지역', values='취업자 (천명)', aggfunc='sum')
            st.line_chart(line_chart_df)
        else:
            st.info("추이 비교를 위해 2개 이상의 연도를 선택하세요.")

    with col2:
        st.subheader("📊 취업/실업 비율 (전체 합산)")
        ratio_data = pd.Series([total_employed, total_unemployed], index=['취업자', '실업자'])
        st.bar_chart(ratio_data) # 파이 차트 대신 막대 차트로 비율을 더 명확하게 표현
    
    st.subheader(f"🏢 지역별 실업률 비교 ({', '.join(map(str, selected_years))}년)")
    bar_chart_df = filtered_df.pivot_table(index='지역', values='실업률 (%)', aggfunc='mean')
    st.bar_chart(bar_chart_df)


    # --- 4.3. 상세 데이터 테이블 및 다운로드 ---
    with st.expander("📄 상세 데이터 보기"):
        st.dataframe(filtered_df.style.format({'실업률 (%)': '{:.2f}%'}))
        
        # CSV 다운로드 버튼
        csv_data = filtered_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 CSV로 다운로드",
            data=csv_data,
            file_name='filtered_economic_data.csv',
            mime='text/csv',
        )

# --- 앱 실행 ---
if __name__ == "__main__":
    data = load_data('경제활동_통합.csv')
    if data is not None:
        main_dashboard(data)
