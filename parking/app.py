import streamlit as st
import pandas as pd
import folium

from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

from geopy.geocoders import Nominatim
from geopy.distance import geodesic

st.set_page_config(
    page_title="서울시 공영주차장 검색",
    page_icon="🚗",
    layout="wide"
)

# -----------------------------
# 스타일
# -----------------------------
st.markdown("""
<style>

.stApp {
    background-color: #F5F9FC;
}

h1,h2,h3 {
    color: #0F4C81;
}

[data-testid="stSidebar"] {
    background-color: #EAF3FA;
}

div[data-testid="metric-container"]{
    background:white;
    border-radius:10px;
    padding:10px;
    border-left:5px solid #0F4C81;
}

</style>
""", unsafe_allow_html=True)

st.title("🚗 서울시 공영주차장 검색 서비스")

uploaded_file = st.file_uploader(
    "서울시 공영주차장 CSV 업로드",
    type=["csv"]
)

if uploaded_file is None:

    st.info(
        "서울시 공영주차장 CSV 파일을 업로드하세요."
    )

    st.stop()

# -----------------------------
# CSV 읽기
# -----------------------------
df = None

for enc in ["cp949", "euc-kr", "utf-8-sig", "utf-8"]:
    try:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, encoding=enc)
        break
    except:
        pass

if df is None:
    st.error("CSV 파일을 읽을 수 없습니다.")
    st.stop()

# -----------------------------
# 데이터 정리
# -----------------------------
df = df.dropna(subset=["위도", "경도"])

df["위도"] = pd.to_numeric(
    df["위도"],
    errors="coerce"
)

df["경도"] = pd.to_numeric(
    df["경도"],
    errors="coerce"
)

df = df.dropna(subset=["위도", "경도"])

for col in [
    "기본 주차 요금",
    "월 정기권 금액",
    "일 최대 요금"
]:
    if col in df.columns:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

# -----------------------------
# 사이드바
# -----------------------------
st.sidebar.header("검색 조건")

address_keyword = st.sidebar.text_input(
    "지역/주소 검색",
    placeholder="성동구, 강남구, 잠실..."
)

min_fee = st.sidebar.number_input(
    "최소 기본요금",
    min_value=0,
    value=0,
    step=100
)

max_fee = st.sidebar.number_input(
    "최대 기본요금",
    min_value=0,
    value=10000,
    step=100
)

parking_types = ["전체"]

if "주차장 종류명" in df.columns:
    parking_types += sorted(
        df["주차장 종류명"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

parking_type = st.sidebar.selectbox(
    "주차장 종류",
    parking_types
)

fee_types = ["전체"]

if "유무료구분명" in df.columns:
    fee_types += sorted(
        df["유무료구분명"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

fee_type = st.sidebar.selectbox(
    "유무료",
    fee_types
)

# -----------------------------
# 필터링
# -----------------------------
filtered_df = df.copy()

if address_keyword:

    filtered_df = filtered_df[
        filtered_df["주소"]
        .astype(str)
        .str.contains(
            address_keyword,
            case=False,
            na=False
        )
    ]

if "기본 주차 요금" in filtered_df.columns:

    filtered_df = filtered_df[
        (
            filtered_df["기본 주차 요금"]
            >= min_fee
        )
        &
        (
            filtered_df["기본 주차 요금"]
            <= max_fee
        )
    ]

if (
    parking_type != "전체"
    and "주차장 종류명" in filtered_df.columns
):

    filtered_df = filtered_df[
        filtered_df["주차장 종류명"]
        == parking_type
    ]

if (
    fee_type != "전체"
    and "유무료구분명" in filtered_df.columns
):

    filtered_df = filtered_df[
        filtered_df["유무료구분명"]
        == fee_type
    ]

# -----------------------------
# 결과 개수
# -----------------------------
st.metric(
    "검색된 주차장 수",
    len(filtered_df)
)

if len(filtered_df) == 0:

    st.warning(
        "검색 조건에 맞는 주차장이 없습니다."
    )

    st.stop()

# -----------------------------
# 결과 테이블
# -----------------------------
st.subheader("📋 검색 결과")

display_cols = [
    col for col in [
        "주차장명",
        "주소",
        "주차장 종류명",
        "유무료구분명",
        "기본 주차 요금",
        "일 최대 요금"
    ]
    if col in filtered_df.columns
]

st.dataframe(
    filtered_df[display_cols],
    use_container_width=True
)

# -----------------------------
# 지도
# -----------------------------
st.subheader("🗺️ 검색 결과 지도")

center_lat = filtered_df["위도"].mean()
center_lon = filtered_df["경도"].mean()

m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=14,
    tiles="CartoDB positron"
)

marker_cluster = MarkerCluster().add_to(m)

for _, row in filtered_df.iterrows():

    popup_html = f"""
    <b>{row['주차장명']}</b><br>
    주소 : {row['주소']}<br>
    기본요금 : {row.get('기본 주차 요금','-')}원<br>
    일최대요금 : {row.get('일 최대 요금','-')}원
    """

    folium.Marker(
        location=[
            row["위도"],
            row["경도"]
        ],
        popup=popup_html,
        tooltip=row["주차장명"]
    ).add_to(marker_cluster)

st_folium(
    m,
    width=None,
    height=700
)

# -----------------------------
# 가장 가까운 주차장 찾기
# -----------------------------
st.subheader("📍 주소 기준 가장 가까운 주차장")

user_address = st.text_input(
    "주소 입력",
    placeholder="서울특별시 성동구 왕십리로"
)

if user_address:

    try:

        geolocator = Nominatim(
            user_agent="parking_app"
        )

        location = geolocator.geocode(
            user_address
        )

        if location:

            user_loc = (
                location.latitude,
                location.longitude
            )

            temp_df = filtered_df.copy()

            temp_df["거리"] = temp_df.apply(
                lambda row:
                geodesic(
                    user_loc,
                    (
                        row["위도"],
                        row["경도"]
                    )
                ).km,
                axis=1
            )

            nearest = temp_df.loc[
                temp_df["거리"].idxmin()
            ]

            st.success(
                f"가장 가까운 주차장 : {nearest['주차장명']}"
            )

            st.write(
                f"📍 주소 : {nearest['주소']}"
            )

            if "기본 주차 요금" in nearest.index:
                st.write(
                    f"💰 기본요금 : {nearest['기본 주차 요금']}원"
                )

            st.write(
                f"📏 거리 : {nearest['거리']:.2f} km"
            )

        else:
            st.error(
                "주소를 찾을 수 없습니다."
            )

    except Exception as e:
        st.error(
            f"오류 발생 : {e}"
        )
