
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

st.set_page_config(
    page_title="서울시 공영주차장 검색",
    layout="wide"
)

st.title("🚗 서울시 공영주차장 안내 서비스")

uploaded_file = st.file_uploader(
    "서울시 공영주차장 CSV 업로드",
    type=["csv"]
)

if uploaded_file:

    # CSV 읽기
    encodings = ["cp949", "euc-kr", "utf-8", "utf-8-sig"]

    df = None

    for enc in encodings:
        try:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding=enc)
            st.success(f"파일 로드 성공 ({enc})")
            break
        except:
            continue

    if df is None:
        st.error("파일을 읽을 수 없습니다.")
        st.stop()

    # 위도/경도 없는 데이터 제거
    df = df.dropna(subset=["위도", "경도"])

    # 숫자형 변환
    for col in [
        "기본 주차 요금",
        "월 정기권 금액",
        "일 최대 요금"
    ]:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    st.sidebar.header("검색 조건")

    # 주소 검색
    address_keyword = st.sidebar.text_input(
        "구/동 검색",
        placeholder="예: 성동구"
    )

    # 요금 검색
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

    # 주차장 종류
    parking_type = st.sidebar.selectbox(
        "주차장 종류",
        ["전체"] + sorted(
            df["주차장 종류명"].dropna().unique().tolist()
        )
    )

    # 유무료
    fee_type = st.sidebar.selectbox(
        "유무료",
        ["전체"] + sorted(
            df["유무료구분명"].dropna().unique().tolist()
        )
    )

    filtered_df = df.copy()

    # 주소 필터
    if address_keyword:
        filtered_df = filtered_df[
            filtered_df["주소"]
            .astype(str)
            .str.contains(address_keyword,
                          case=False,
                          na=False)
        ]

    # 요금 필터
    filtered_df = filtered_df[
        (filtered_df["기본 주차 요금"] >= min_fee)
        &
        (filtered_df["기본 주차 요금"] <= max_fee)
    ]

    # 종류 필터
    if parking_type != "전체":
        filtered_df = filtered_df[
            filtered_df["주차장 종류명"] == parking_type
        ]

    # 유무료 필터
    if fee_type != "전체":
        filtered_df = filtered_df[
            filtered_df["유무료구분명"] == fee_type
        ]

    st.subheader(
        f"검색 결과 ({len(filtered_df)}개)"
    )

    st.dataframe(
        filtered_df[
            [
                "주차장명",
                "주소",
                "기본 주차 요금",
                "월 정기권 금액",
                "일 최대 요금",
                "주차장 종류명"
            ]
        ]
    )

    #################################
    # 주소 기반 가장 가까운 주차장
    #################################

    st.subheader("📍 주소 기준 가장 가까운 주차장")

    user_address = st.text_input(
        "주소 입력",
        placeholder="서울특별시 성동구 왕십리로"
    )

    if st.button("가까운 주차장 찾기"):

        geolocator = Nominatim(
            user_agent="parking_app"
        )

        location = geolocator.geocode(user_address)

        if location:

            user_loc = (
                location.latitude,
                location.longitude
            )

            filtered_df["거리"] = filtered_df.apply(
                lambda row: geodesic(
                    user_loc,
                    (row["위도"], row["경도"])
                ).km,
                axis=1
            )

            nearest = filtered_df.loc[
                filtered_df["거리"].idxmin()
            ]

            st.success("가장 가까운 주차장")

            st.write(
                f"주차장명 : {nearest['주차장명']}"
            )
            st.write(
                f"주소 : {nearest['주소']}"
            )
            st.write(
                f"기본요금 : {nearest['기본 주차 요금']}원"
            )
            st.write(
                f"거리 : {nearest['거리']:.2f} km"
            )

    #################################
    # 지도
    #################################

    st.subheader("🗺️ 주차장 지도")

    if len(filtered_df) > 0:

        center = [
            filtered_df["위도"].mean(),
            filtered_df["경도"].mean()
        ]

        m = folium.Map(
            location=center,
            zoom_start=12
        )

        for _, row in filtered_df.iterrows():

            popup = f"""
            <b>{row['주차장명']}</b><br>
            주소 : {row['주소']}<br>
            기본요금 : {row['기본 주차 요금']}원<br>
            일 최대요금 : {row['일 최대 요금']}원<br>
            종류 : {row['주차장 종류명']}
            """

            tooltip = f"""
            {row['주소']}
            <br>
            {row['기본 주차 요금']}원
            """

            folium.Marker(
                location=[
                    row["위도"],
                    row["경도"]
                ],
                popup=popup,
                tooltip=tooltip
            ).add_to(m)

        st_folium(
            m,
            width=1200,
            height=700
        )

    else:
        st.warning(
            "검색 조건에 해당하는 주차장이 없습니다."
        )
```
