import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import platform
import json

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
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        st.markdown("---")
        st.header("과제 소개")
        st.markdown("""
        이 웹 애플리케이션은 `population_trends.csv` 데이터를 기반으로
        국내 지역별 인구 변화를 탐색하고 시각화하는 기능을 제공합니다.

        좌측 메뉴의 **EDA** 페이지에서 데이터 분석을 수행할 수 있습니다.
        """)
        
        st.markdown("---")
        st.subheader("지역별 인구 추이 데이터셋")
        st.markdown("""
        - **파일명**: `population_trends.csv`
        - **설명**: 특정 기간 동안의 국내 지역별 인구, 출생아 수, 사망자 수 등의 정보를 담고 있는 데이터입니다.
        """)


# ---------------------
# 로그인 페이지 클래스 (오류 메시지 개선)
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
            except Exception as e:
                try:
                    error_json = e.args[1]
                    error_message = json.loads(error_json)['error']['message']

                    if error_message == "INVALID_LOGIN_CREDENTIALS":
                        st.error("로그인 실패: 이메일 또는 비밀번호가 올바르지 않습니다.")
                    else:
                        st.error(f"로그인 실패: {error_message}")
                except (IndexError, KeyError, json.JSONDecodeError):
                    st.error(f"로그인 실패: 알 수 없는 오류가 발생했습니다. ({e})")

# ---------------------
# 회원가입 페이지 클래스 (오류 메시지 개선)
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
                # 1. Firebase Authentication에 사용자 생성
                auth.create_user_with_email_and_password(email, password)
                
                # 2. Firebase Realtime Database에 사용자 정보 저장
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
            except Exception as e:
                try:
                    error_json = e.args[1] 
                    error_data = json.loads(error_json)
                    error_message = error_data['error']['message']

                    if error_message == "EMAIL_EXISTS":
                        st.error("회원가입 실패: 이미 가입된 이메일 주소입니다.")
                    elif "WEAK_PASSWORD" in error_message:
                        st.error("회원가입 실패: 보안 강도가 약합니다. 비밀번호는 6자 이상이어야 합니다.")
                    elif "Permission denied" in str(e):
                        st.error("회원가입 실패: 데이터베이스 쓰기 권한이 없습니다. Firebase 설정을 확인하세요.")
                    else:
                        st.error(f"회원가입 실패: {error_message}")

                except (IndexError, KeyError, json.JSONDecodeError):
                    st.error(f"회원가입 실패: 알 수 없는 오류가 발생했습니다. ({e})")


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
            except Exception as e:
                st.error(f"이메일 전송 실패: {e}")

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
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        self.population_trends_eda()

    def population_trends_eda(self):
        """지역별 인구 추이 분석 EDA 수행"""
        st.title("📊 지역별 인구 추이 분석")
        
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
        
        # '세종' 지역의 '-'를 '0'으로 대체합니다.
        df.loc[df['지역'] == '세종', numeric_cols] = df.loc[df['지역'] == '세종', numeric_cols].replace('-', '0')

        for col in numeric_cols:
            # 컬럼이 문자열(object) 타입인 경우에만 쉼표(,) 제거를 시도합니다.
            if pd.api.types.is_string_dtype(df[col]):
                df[col] = df[col].str.replace(',', '')
            
            # 숫자형으로 변환합니다. 변환할 수 없는 값은 NaN(Not a Number)으로 처리됩니다.
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # 변환 과정에서 생긴 NaN 값을 0으로 채웁니다.
        df.fillna(0, inplace=True)

        # 최종적으로 모든 숫자 컬럼을 정수형(int)으로 변환합니다.
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
            region_map = {
                '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
                '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
                '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
                '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
                '제주': 'Jeju'
            }
            pivot_df.columns = pivot_df.columns.map(region_map)
            
            fig4, ax4 = plt.subplots(figsize=(15, 10))
            pivot_df.plot(kind='area', stacked=True, ax=ax4, colormap='tab20c')
            
            ax4.set_title('Annual Population by Region (Stacked Area Chart)')
            ax4.set_ylabel('Population (in 10 millions)')
            ax4.set_xlabel('Year')
            ax4.legend(title='Region', bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.tight_layout()
            st.pyplot(fig4)

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
