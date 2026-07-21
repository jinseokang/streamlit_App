import streamlit as st
import pandas as pd
import requests
import random
from datetime import datetime
import folium
from streamlit_folium import st_folium

st.set_page_config(
    page_title="대한민국 축제 탐험대",
    page_icon="🎉",
    layout="wide"
)

SERVICE_KEY = st.secrets["TOUR_API_KEY"]

# 상태 유지
if "recommended_festival" not in st.session_state:
    st.session_state.recommended_festival = None

if "search_keyword" not in st.session_state:
    st.session_state.search_keyword = ""

@st.cache_data(ttl=3600)
def get_festivals():
    url = "https://apis.data.go.kr/B551011/KorService2/searchFestival2"

    params = {
        "serviceKey": SERVICE_KEY,
        "MobileOS": "ETC",
        "MobileApp": "FestivalApp",
        "_type": "json",
        "numOfRows": 100,
        "pageNo": 1,
        "eventStartDate": datetime.now().strftime("%Y%m%d")
    }

    res = requests.get(url, params=params, timeout=30)
    data = res.json()

    items = (
        data["response"]
        ["body"]
        ["items"]
        ["item"]
    )

    return pd.DataFrame(items)

try:
    df = get_festivals()
except Exception as e:
    st.error("API 데이터를 불러올 수 없습니다.")
    st.exception(e)
    st.stop()

st.sidebar.title("🎉 축제 탐험")

keyword = st.sidebar.text_input(
    "축제 검색",
    value=st.session_state.search_keyword
)

st.session_state.search_keyword = keyword

if keyword:
    df = df[
        df["title"]
        .str.contains(keyword, case=False, na=False)
    ]

st.title("🎉 대한민국 축제 탐험대")

st.caption("한국관광공사 TourAPI 기반")

col1, col2, col3 = st.columns(3)

col1.metric("검색된 축제", len(df))

col2.metric(
    "지역 수",
    df["addr1"].nunique() if "addr1" in df.columns else 0
)

col3.metric(
    "오늘 추천",
    random.randint(1, 10)
)

st.subheader("🎲 오늘 뭐 갈까?")

if st.button("축제 추천받기"):
    if len(df) > 0:
        item = df.sample(1).iloc[0]
        st.session_state.recommended_festival = item.to_dict()

if st.session_state.recommended_festival:

    festival = st.session_state.recommended_festival

    st.success(
        f"🎉 오늘의 추천 축제 : {festival['title']}"
    )

    if festival.get("firstimage"):
        st.image(
            festival["firstimage"],
            use_container_width=True
        )

    st.write(
        f"📍 {festival.get('addr1','주소 정보 없음')}"
    )

    st.write(
        f"📅 {festival.get('eventstartdate','')} ~ "
        f"{festival.get('eventenddate','')}"
    )

st.subheader("🗺️ 전국 축제 지도")

m = folium.Map(
    location=[36.35, 127.75],
    zoom_start=7,
    control_scale=True
)

for _, row in df.iterrows():

    mapx = row.get("mapx")
    mapy = row.get("mapy")

    if not mapx or not mapy:
        continue

    try:

        lat = float(mapy)
        lon = float(mapx)

        popup_text = f"""
        <b>{row.get('title','')}</b><br>
        {row.get('addr1','')}
        """

        folium.Marker(
            [lat, lon],
            popup=popup_text,
            tooltip=row.get("title","")
        ).add_to(m)

    except Exception:
        continue

st_folium(
    m,
    key="festival_map",
    use_container_width=True,
    height=650
)
st.subheader("🎪 축제 목록")

for _, row in df.iterrows():

    with st.container():

        col1, col2 = st.columns([1,3])

        with col1:

            if row.get("firstimage"):
                st.image(
                    row["firstimage"],
                    use_container_width=True
                )

        with col2:

            st.markdown(
                f"### {row['title']}"
            )

            st.write(
                row.get("addr1","")
            )

            st.write(
                row.get("eventstartdate","")
            )

        st.divider()
