import streamlit as st
import pandas as pd
import requests
import random
import folium

from datetime import datetime
from streamlit_folium import st_folium

st.set_page_config(
    page_title="대한민국 축제 탐험대",
    page_icon="🎉",
    layout="wide"
)

SERVICE_KEY = st.secrets["TOUR_API_KEY"]

# -------------------------
# 축제 데이터 조회
# -------------------------

@st.cache_data(ttl=3600)
def get_festivals():

    url = "https://apis.data.go.kr/B551011/KorService2/searchFestival2"

    params = {
        "serviceKey": SERVICE_KEY,
        "MobileOS": "ETC",
        "MobileApp": "FestivalExplorer",
        "_type": "json",
        "numOfRows": 100,
        "pageNo": 1,
        "eventStartDate": datetime.now().strftime("%Y%m%d")
    }

    res = requests.get(url, params=params, timeout=30)

    data = res.json()

    header = data.get("response", {}).get("header", {})

    if header.get("resultCode") != "0000":
        raise Exception(
            f"{header.get('resultCode')} : {header.get('resultMsg')}"
        )

    items = (
        data["response"]
        ["body"]
        ["items"]
        ["item"]
    )

    return pd.DataFrame(items)

# -------------------------
# 데이터 로딩
# -------------------------

try:
    df = get_festivals()

except Exception as e:
    st.error("API 오류")
    st.exception(e)
    st.stop()

# -------------------------
# 헤더
# -------------------------

st.title("🎉 대한민국 축제 탐험대")

st.caption(
    "한국관광공사 TourAPI 기반 전국 축제 검색"
)

# -------------------------
# 검색
# -------------------------

keyword = st.text_input(
    "축제 검색"
)

if keyword:

    df = df[
        df["title"]
        .str.contains(
            keyword,
            case=False,
            na=False
        )
    ]

# -------------------------
# 통계
# -------------------------

col1, col2, col3 = st.columns(3)

col1.metric(
    "축제 수",
    len(df)
)

col2.metric(
    "추천 점수",
    random.randint(80, 100)
)

col3.metric(
    "오늘의 운",
    random.randint(1, 100)
)

# -------------------------
# 랜덤 추천
# -------------------------

st.subheader("🎲 오늘 뭐 갈까?")

if st.button("축제 추천받기"):

    if len(df) > 0:

        pick = df.sample(1).iloc[0]

        st.success(
            f"오늘의 추천 축제 : {pick['title']}"
        )

# -------------------------
# 지도
# -------------------------

st.subheader("🗺️ 전국 축제 지도")

m = folium.Map(
    location=[36.5, 127.8],
    zoom_start=7
)

for _, row in df.iterrows():

    try:

        folium.Marker(
            [
                float(row["mapy"]),
                float(row["mapx"])
            ],
            tooltip=row["title"]
        ).add_to(m)

    except:
        pass

st_folium(
    m,
    width=1200,
    height=500
)

# -------------------------
# 축제 카드
# -------------------------

st.subheader("🎪 축제 목록")

for _, row in df.iterrows():

    with st.container():

        col1, col2 = st.columns([1, 3])

        with col1:

            img = row.get("firstimage")

            if img:
                st.image(
                    img,
                    use_container_width=True
                )

        with col2:

            st.markdown(
                f"### {row['title']}"
            )

            st.write(
                row.get("addr1", "")
            )

            st.write(
                f"시작일 : {row.get('eventstartdate','')}"
            )

            st.write(
                f"종료일 : {row.get('eventenddate','')}"
            )

        st.divider()
