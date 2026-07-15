import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

st.set_page_config(page_title="공영주차장 안내", layout="wide")

st.title("🚗 공영주차장 요금 안내 시스템")

uploaded_file = st.file_uploader(
    "공공데이터 CSV 업로드",
    type=["csv"]
)

if uploaded_file is not None:

    # 여러 인코딩으로 읽기
    encodings = ["utf-8", "utf-8-sig", "cp949", "euc-kr"]

    df = None

    for enc in encodings:
        try:
            uploaded_file.seek(0)
            df = pd.read_csv(
                uploaded_file,
                encoding=enc,
                sep=None,
                engine="python"
            )
            st.success(f"파일을 성공적으로 읽었습니다. ({enc})")
            break
        except Exception:
            continue

    if df is None:
        st.error("CSV 파일을 읽을 수 없습니다.")
        st.stop()

    st.subheader("업로드된 데이터")
    st.dataframe(df)

    # 컬럼 존재 여부 확인
    required_columns = [
        "주차장명",
        "주소",
        "위도",
        "경도",
        "기본요금",
        "추가요금"
    ]

    for col in required_columns:
        if col not in df.columns:
            st.error(f"'{col}' 컬럼이 없습니다.")
            st.write("현재 컬럼명")
            st.write(df.columns.tolist())
            st.stop()

    ###################################
    # 주소 검색
    ###################################

    st.subheader("주소 검색")

    address = st.text_input("주소를 입력하세요.")

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
                    float(row["위도"]),
                    float(row["경도"])
                )

                distance = geodesic(
                    user_location,
                    parking_location
                ).km

                distances.append(distance)

            df["거리"] = distances

            nearest = df.loc[df["거리"].idxmin()]

            st.success("가장 가까운 공영주차장")

            st.write("### 🚗 주차장 정보")
            st.write(f"주차장명 : {nearest['주차장명']}")
            st.write(f"주소 : {nearest['주소']}")
            st.write(f"기본요금 : {nearest['기본요금']}원")
            st.write(f"추가요금 : {nearest['추가요금']}원")
            st.write(f"거리 : {nearest['거리']:.2f} km")

    ###################################
    # 지도
    ###################################

    st.subheader("공영주차장 지도")

    center = [
        df["위도"].astype(float).mean(),
        df["경도"].astype(float).mean()
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
        {row['주소']}<br>
        기본요금 : {row['기본요금']}원
        """

        folium.Marker(
            location=[
                float(row["위도"]),
                float(row["경도"])
            ],
            popup=popup,
            tooltip=tooltip,
            icon=folium.Icon(color="blue")
        ).add_to(m)

    st_folium(
        m,
        width=1000,
        height=600
    )
