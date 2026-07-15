import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

st.set_page_config(
    page_title="서울시 공영주차장 안내",
    layout="wide"
)

st.title("🚗 서울시 공영주차장 검색 서비스")

uploaded_file = st.file_uploader(
    "서울시 공영주차장 CSV 업로드",
    type=["csv"]
)

if uploaded_file:

    # CSV 읽기
    df = None

    for enc in ["cp949", "euc-kr", "utf-8-sig", "utf-8"]:
        try:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding=enc)
            st.success(f"파일 로드 성공 ({enc})")
            break
        except:
            pass

    if df is None:
        st.error("CSV 파일을 읽을 수 없습니다.")
        st.stop()

    # 위도 경도 없는 데이터 제거
    df = df.dropna(subset=["위도", "경도"])

    # 숫자형 변환
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

    st.sidebar.header("검색 조건")

    address_keyword = st.sidebar.text_input(
        "지역 검색",
        placeholder="예: 성동구"
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
            .unique()
            .tolist()
        )

    fee_type = st.sidebar.selectbox(
        "유무료",
        fee_types
    )

    search_btn = st.sidebar.button("검색")

    if search_btn:

        filtered_df = df.copy()

        # 지역 검색
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

        # 요금 검색
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

        # 주차장 종류
        if (
            parking_type != "전체"
            and "주차장 종류명" in filtered_df.columns
        ):
            filtered_df = filtered_df[
                filtered_df["주차장 종류명"]
                == parking_type
            ]

        # 유무료
        if (
            fee_type != "전체"
            and "유무료구분명" in filtered_df.columns
        ):
            filtered_df = filtered_df[
                filtered_df["유무료구분명"]
                == fee_type
            ]

        st.subheader(
            f"검색 결과 : {len(filtered_df)}개"
        )

        if len(filtered_df) == 0:
            st.warning("검색 결과가 없습니다.")
            st.stop()

        display_cols = [
            col
            for col in [
                "주차장명",
                "주소",
                "기본 주차 요금",
                "일 최대 요금",
                "주차장 종류명",
                "유무료구분명"
            ]
            if col in filtered_df.columns
        ]

        st.dataframe(
            filtered_df[display_cols]
        )

        # 지도 생성
        center_lat = filtered_df["위도"].mean()
        center_lon = filtered_df["경도"].mean()

        m = folium.Map(
            location=[
                center_lat,
                center_lon
            ],
            zoom_start=14
        )

        for _, row in filtered_df.iterrows():

            popup_html = f"""
            <b>{row['주차장명']}</b><br>
            주소 : {row['주소']}<br>
            기본요금 : {row.get('기본 주차 요금','-')}원<br>
            일최대요금 : {row.get('일 최대 요금','-')}원
            """

            tooltip_html = f"""
            {row['주차장명']}
            """

            folium.Marker(
                location=[
                    row["위도"],
                    row["경도"]
                ],
                popup=popup_html,
                tooltip=tooltip_html
            ).add_to(m)

        st.subheader("🗺️ 검색 결과 지도")

        st_folium(
            m,
            width=1200,
            height=700
        )

        # 가장 가까운 주차장 찾기
        st.subheader("📍 주소 기준 가장 가까운 주차장")

        user_address = st.text_input(
            "주소 입력",
            placeholder="예: 서울특별시 성동구 왕십리로"
        )

        if st.button("가까운 주차장 찾기"):

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

                filtered_df["거리"] = (
                    filtered_df.apply(
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
                )

                nearest = filtered_df.loc[
                    filtered_df["거리"].idxmin()
                ]

                st.success(
                    "가장 가까운 주차장"
                )

                st.write(
                    f"주차장명 : {nearest['주차장명']}"
                )

                st.write(
                    f"주소 : {nearest['주소']}"
                )

                if "기본 주차 요금" in nearest:
                    st.write(
                        f"기본요금 : {nearest['기본 주차 요금']}원"
                    )

                st.write(
                    f"거리 : {nearest['거리']:.2f} km"
                )

            else:
                st.error(
                    "주소를 찾을 수 없습니다."
                )

else:

    st.info(
        "CSV 파일을 업로드한 후 검색을 진행하세요."
    )
