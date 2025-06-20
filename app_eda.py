import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import platform

# ---------------------
# 한글 폰트 설정 (Windows, Mac)
# ---------------------
# 시스템에 따라 적절한 한글 폰트 설정
if platform.system() == 'Windows':
    plt.rc('font', family='Malgun Gothic')
elif platform.system() == 'Darwin': # Mac
    plt.rc('font', family='AppleGothic')
else: # Linux
    # Linux에서는 나눔폰트를 사용하기 위해 폰트 설치가 필요할 수 있습니다.
    # st.warning('Linux 환경에서는 한글 폰트 설정이 필요할 수 있습니다.')
    # 예: plt.rc('font', family='NanumGothic')
    pass

# 차트에서 마이너스 부호가 깨지는 현상 방지
plt.rcParams['axes.unicode_minus'] = False

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스 (수정됨)
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        st.markdown("---")
        st.header("과제 소개")
        st.markdown("""
        이 웹 애플리케이션은 두 가지 주요 데이터 분석 기능을 제공합니다.
        - **자전거 수요 예측 분석**: Kaggle의 Bike Sharing Demand 데이터를 활용하여 시간대별 자전거 대여량을 분석하고 예측합니다.
        - **지역별 인구 추이 분석**: `population_trends.csv` 데이터를 기반으로 국내 지역별 인구 변화를 탐색하고 시각화합니다.

        좌측 메뉴의 **EDA** 페이지에서 원하는 분석을 선택하여 진행할 수 있습니다.
        """)
        
        st.markdown("---")
        # 데이터셋 출처 소개
        st.subheader("B.D.D (Bike Sharing Demand) 데이터셋")
        st.markdown("""  
        - **제공처**: [Kaggle Bike Sharing Demand Competition](https://www.kaggle.com/c/bike-sharing-demand)  
        - **설명**: 2011–2012년 워싱턴 D.C.의 시간별 자전거 대여량 데이터.
        """)

        st.subheader("지역별 인구 추이 데이터셋")
        st.markdown("""
        - **파일명**: `population_trends.csv`
        - **설명**: 특정 기간 동안의 국내 지역별 인구, 출생아 수, 사망자 수 등의 정보를 담고 있는 데이터.
        """)


# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스 (수정됨)
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 Exploratory Data Analysis")
        
        analysis_type = st.sidebar.selectbox(
            "분석 유형 선택",
            ("자전거 수요 예측 분석", "지역별 인구 추이 분석")
        )

        if analysis_type == "자전거 수요 예측 분석":
            self.bike_sharing_eda()
        else:
            self.population_trends_eda()

    def population_trends_eda(self):
        """지역별 인구 추이 분석 EDA 수행"""
        st.header("📈 지역별 인구 추이 분석")
        uploaded_file = st.file_uploader("인구 데이터 업로드 (population_trends.csv)", type="csv")
        
        if uploaded_file is None:
            st.info("population_trends.csv 파일을 업로드 해주세요.")
            return

        try:
            df = pd.read_csv(uploaded_file)
        except Exception as e:
            st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
            return
            
        # 데이터 전처리
        numeric_cols = ['인구', '출생아수(명)', '사망자수(명)']
        df.loc[df['지역'] == '세종', numeric_cols] = df.loc[df['지역'] == '세종', numeric_cols].replace('-', '0')
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col].str.replace(',', ''), errors='coerce')
        
        df.fillna(0, inplace=True)
        for col in numeric_cols:
             df[col] = df[col].astype(int)

        st.success("데이터가 성공적으로 로드 및 전처리되었습니다.")

        # 분석 탭 생성
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "기초 통계", "연도별 추이", "지역별 분석", "변화량 분석", "시각화"
        ])

        with tab1:
            st.subheader("기초 통계 분석")
            st.markdown("#### 데이터 정보 (Info)")
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())

            st.markdown("#### 데이터 요약 통계 (Describe)")
            st.dataframe(df.describe())
            
            st.markdown("#### 원본 데이터 (상위 10개)")
            st.dataframe(df.head(10))

        with tab2:
            st.subheader("연도별 전체 인구 추이")
            nationwide_df = df[df['지역'] == '전국'].sort_values('연도')

            # 인구 추이 그래프
            fig1, ax1 = plt.subplots(figsize=(12, 6))
            sns.lineplot(x='연도', y='인구', data=nationwide_df, marker='o', ax=ax1, label="Population")
            ax1.set_title("Annual Population Trend (Nationwide)")
            ax1.set_xlabel("Year")
            ax1.set_ylabel("Population (in 10 millions)")
            ax1.grid(True)

            # 2035년 인구 예측
            recent_3_years = nationwide_df.tail(3)
            births_rate = recent_3_years['출생아수(명)'].mean()
            deaths_rate = recent_3_years['사망자수(명)'].mean()
            net_change = births_rate - deaths_rate
            
            last_year = recent_3_years['연도'].iloc[-1]
            last_pop = recent_3_years['인구'].iloc[-1]
            
            years_to_predict = 2035 - last_year
            predicted_pop = last_pop + (net_change * years_to_predict)

            # 예측값 그래프에 표시
            ax1.plot(2035, predicted_pop, 'ro', markersize=10, label='Predicted Population for 2035')
            ax1.legend()
            st.pyplot(fig1)

            st.info(f"""
            #### 인구 예측 결과
            - **최근 3년 평균 출생아 수**: {births_rate:,.0f} 명
            - **최근 3년 평균 사망자 수**: {deaths_rate:,.0f} 명
            - **연평균 순 인구 변화**: {net_change:,.0f} 명
            - **2035년 예측 인구**: **{predicted_pop:,.0f}** 명
            """)

        with tab3:
            st.subheader("지역별 인구 변화량 순위 (최근 5년)")
            
            df_local = df[df['지역'] != '전국']
            
            latest_year = df_local['연도'].max()
            start_year = latest_year - 5
            
            df_recent = df_local[df_local['연도'] == latest_year]
            df_past = df_local[df_local['연도'] == start_year]

            merged_df = pd.merge(df_recent, df_past, on='지역', suffixes=('_latest', '_past'))
            merged_df['pop_change'] = merged_df['인구_latest'] - merged_df['인구_past']
            merged_df['change_rate'] = (merged_df['pop_change'] / merged_df['인구_past']) * 100
            
            # 영문 지역명 매핑
            region_map = {
                '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
                '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
                '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
                '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
                '제주': 'Jeju'
            }
            merged_df['Region_Eng'] = merged_df['지역'].map(region_map)

            # 변화량 기준 정렬
            sorted_by_change = merged_df.sort_values('pop_change', ascending=False)
            
            # 변화량 시각화 (수평 막대 그래프)
            fig2, ax2 = plt.subplots(figsize=(12, 8))
            bars = sns.barplot(x='pop_change', y='Region_Eng', data=sorted_by_change, ax=ax2)
            ax2.set_title(f'Population Change by Region ({start_year} vs {latest_year})')
            ax2.set_xlabel('Population Change (in thousands)')
            ax2.set_ylabel('Region')
            ax2.bar_label(bars, fmt=lambda x: f'{x/1000:,.0f}k')
            st.pyplot(fig2)

            st.markdown("""
            > **그래프 해석:** 경기, 인천, 세종 등 수도권 및 신도시 지역에서 인구가 크게 증가한 반면, 서울, 부산, 대구 등 기존 대도시에서는 인구가 감소하는 경향을 보입니다. 이는 산업 구조 변화와 수도권 집중 현상을 반영합니다.
            """)

            # 변화율 기준 정렬
            sorted_by_rate = merged_df.sort_values('change_rate', ascending=False)
            
            # 변화율 시각화 (수평 막대 그래프)
            fig3, ax3 = plt.subplots(figsize=(12, 8))
            bars_rate = sns.barplot(x='change_rate', y='Region_Eng', data=sorted_by_rate, ax=ax3)
            ax3.set_title(f'Population Change Rate by Region ({start_year} vs {latest_year})')
            ax3.set_xlabel('Change Rate (%)')
            ax3.set_ylabel('Region')
            ax3.bar_label(bars_rate, fmt='%.2f%%')
            st.pyplot(fig3)
            
            st.markdown("""
            > **그래프 해석:** 변화율 측면에서는 세종시의 인구 증가가 압도적으로 높게 나타납니다. 이는 행정수도 이전의 효과로 분석됩니다. 반면, 울산, 부산 등 전통적인 산업 도시의 인구 감소율이 상대적으로 높게 나타납니다.
            """)


        with tab4:
            st.subheader("연도별 인구 증감 상위 100")
            df_local = df[df['지역'] != '전국'].copy()
            df_local.sort_values(['지역', '연도'], inplace=True)
            
            # diff()를 사용하여 연도별 증감 계산
            df_local['증감'] = df_local.groupby('지역')['인구'].diff().fillna(0)
            
            top_100_changes = df_local.sort_values('증감', ascending=False).head(100)
            
            st.dataframe(top_100_changes[['연도', '지역', '인구', '증감']].style.format({
                "인구": "{:,.0f}",
                "증감": "{:,.0f}"
            }).background_gradient(cmap='coolwarm', subset=['증감']))

        with tab5:
            st.subheader("지역별 연도별 인구 누적 영역 그래프")
            df_local = df[df['지역'] != '전국'].copy()
            
            pivot_df = df_local.pivot_table(index='연도', columns='지역', values='인구', aggfunc='sum')
            pivot_df.fillna(0, inplace=True)
            
            # 영문으로 컬럼명 변경
            pivot_df.columns = pivot_df.columns.map(region_map)
            
            fig4, ax4 = plt.subplots(figsize=(15, 10))
            pivot_df.plot(kind='area', stacked=True, ax=ax4, colormap='tab20c')
            
            ax4.set_title('Annual Population by Region (Stacked Area Chart)')
            ax4.set_ylabel('Population (in 10 millions)')
            ax4.set_xlabel('Year')
            ax4.legend(title='Region', bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.tight_layout()
            st.pyplot(fig4)


    def bike_sharing_eda(self):
        """기존의 자전거 수요 예측 EDA 수행"""
        st.header("🚲 Bike Sharing Demand EDA")
        uploaded = st.file_uploader("데이터셋 업로드 (train.csv)", type="csv")
        if not uploaded:
            st.info("train.csv 파일을 업로드 해주세요.")
            return

        df = pd.read_csv(uploaded, parse_dates=['datetime'])

        tabs = st.tabs([
            "1. 목적 & 절차", "2. 데이터셋 설명", "3. 데이터 로드 & 품질 체크", "4. Datetime 특성 추출",
            "5. 시각화", "6. 상관관계 분석", "7. 이상치 제거", "8. 로그 변환"
        ])

        with tabs[0]:
            st.header("🔭 목적 & 분석 절차")
            st.markdown("""
            **목적**: Bike Sharing Demand 데이터셋을 탐색하고,
            다양한 특성이 대여량(count)에 미치는 영향을 파악합니다.
            """)
        
        with tabs[1]:
            st.header("🔍 데이터셋 설명")
            st.markdown(f"총 관측치: {df.shape[0]}개")
            st.subheader("1) 데이터 구조 (`df.info()`)")
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())

        with tabs[2]:
            st.header("📥 데이터 로드 & 품질 체크")
            st.subheader("결측값 개수")
            missing = df.isnull().sum()
            st.bar_chart(missing)

        with tabs[3]:
            st.header("🕒 Datetime 특성 추출")
            df['year'] = df['datetime'].dt.year
            df['month'] = df['datetime'].dt.month
            df['hour'] = df['datetime'].dt.hour
            df['dayofweek'] = df['datetime'].dt.dayofweek
            st.dataframe(df[['datetime', 'year', 'month', 'hour', 'dayofweek']].head())

        with tabs[4]:
            st.header("📈 시각화")
            st.subheader("근무일 여부별 시간대별 평균 대여량")
            fig1, ax1 = plt.subplots()
            sns.pointplot(x='hour', y='count', hue='workingday', data=df, ax=ax1)
            st.pyplot(fig1)

        with tabs[5]:
            st.header("🔗 상관관계 분석")
            features = ['temp', 'atemp', 'humidity', 'windspeed', 'count']
            corr_df = df[features].corr()
            fig, ax = plt.subplots()
            sns.heatmap(corr_df, annot=True, fmt=".2f", cmap="coolwarm", ax=ax)
            st.pyplot(fig)
            
        with tabs[6]:
            st.header("🚫 이상치 제거")
            mean_count = df['count'].mean()
            std_count = df['count'].std()
            upper = mean_count + 3 * std_count
            df_no = df[df['count'] <= upper]
            st.write(f"이상치 제거 전: {df.shape[0]}개, 제거 후: {df_no.shape[0]}개")

        with tabs[7]:
            st.header("🔄 로그 변환")
            df['log_count'] = np.log1p(df['count'])
            fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(12, 4))
            sns.histplot(df['count'], kde=True, ax=axes[0])
            sns.histplot(df['log_count'], kde=True, ax=axes[1])
            st.pyplot(fig)


# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

pg = st.navigation(pages)
pg.run()
