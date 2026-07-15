import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

st.set_page_config(
    page_title="공영주차장 안내",
    layout="wide"
)

st.title("🚗 공영주차장 요금 안내 시스템")

uploaded_file = st.file_uploader(
    "CSV 파일 업로드",
    type=["csv"]
)

if uploaded_file is not None:

    df = pd.read_csv(uploaded_file)

    st.success("CSV 업로드 완료!")

    st.dataframe(df)

    ###################################
    # 주소 검색
    ###################################

    address = st.text_input("주소를 입력하세요")

    if st.button("검색"):

        geolocator = Nominatim(user_agent="parking_app")

        location = geolocator.geocode(address)

        if location is None:
            st.error("주소를 찾을 수 없습니다.")

        else:

            user_location = (
                location.latitude,
                location.longitude
            )

            distances = []

            for _, row in df.iterrows():

                parking_location = (
                    row["위도"],
                    row["경도"]
                )

                distance = geodesic(
                    user_location,
                    parking_location
                ).km

                distances.append(distance)

            df["거리"] = distances

            nearest = df.loc[df["거리"].idxmin()]

            st.subheader("가장 가까운 공영주차장")

            st.write(f"**주차장명:** {nearest['주차장명']}")
            st.write(f"**주소:** {nearest['주소']}")
            st.write(f"**기본요금:** {nearest['기본요금']}원")
            st.write(f"**추가요금:** {nearest['추가요금']}원")
            st.write(f"**거리:** {nearest['거리']:.2f} km")

    ###################################
    # 지도
    ###################################

    st.subheader("공영주차장 지도")

    center = [
        df["위도"].mean(),
        df["경도"].mean()
    ]

    m = folium.Map(
        location=center,
        zoom_start=12
    )

    for _, row in df.iterrows():

        popup = f"""
        <b>{row['주차장명']}</b><br>
        주소 : {row['주소']}<br>
        기본요금 : {row['기본요금']}원<br>
        추가요금 : {row['추가요금']}원
        """

        tooltip = f"""
        {row['주소']}
        <br>
        {row['기본요금']}원
        """

        folium.Marker(
            location=[
                row["위도"],
                row["경도"]
            ],
            popup=popup,
            tooltip=tooltip,
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(m)

    st_folium(
        m,
        width=900,
        height=600
    )
