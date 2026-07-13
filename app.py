import streamlit as st
import random

st.set_page_config(page_title="🍽️ 점메추 · 저메추", page_icon="🍴")

st.title("🍽️ AI 점메추 · 저메추")

# ----------------------------
# 메뉴 데이터
# ----------------------------

menus = [
    {"name":"김치찌개","country":"한식","type":"밥","taste":"매운맛"},
    {"name":"된장찌개","country":"한식","type":"밥","taste":"담백한맛"},
    {"name":"순두부찌개","country":"한식","type":"밥","taste":"매운맛"},
    {"name":"제육볶음","country":"한식","type":"밥","taste":"매운맛"},
    {"name":"불고기","country":"한식","type":"밥","taste":"담백한맛"},
    {"name":"비빔밥","country":"한식","type":"밥","taste":"담백한맛"},
    {"name":"삼겹살","country":"한식","type":"고기","taste":"담백한맛"},
    {"name":"닭갈비","country":"한식","type":"고기","taste":"매운맛"},
    {"name":"냉면","country":"한식","type":"면","taste":"시원한맛"},
    {"name":"칼국수","country":"한식","type":"면","taste":"국물"},
    {"name":"국밥","country":"한식","type":"국물","taste":"얼큰한맛"},
    {"name":"콩나물국밥","country":"한식","type":"국물","taste":"해장"},

    {"name":"짜장면","country":"중식","type":"면","taste":"담백한맛"},
    {"name":"짬뽕","country":"중식","type":"면","taste":"매운맛"},
    {"name":"마라탕","country":"중식","type":"면","taste":"매운맛"},
    {"name":"마라샹궈","country":"중식","type":"고기","taste":"매운맛"},
    {"name":"볶음밥","country":"중식","type":"밥","taste":"담백한맛"},
    {"name":"탕수육","country":"중식","type":"고기","taste":"담백한맛"},
    {"name":"어향가지","country":"중식","type":"샐러드","taste":"담백한맛"},

    {"name":"라멘","country":"일식","type":"면","taste":"국물"},
    {"name":"우동","country":"일식","type":"면","taste":"국물"},
    {"name":"초밥","country":"일식","type":"밥","taste":"담백한맛"},
    {"name":"규동","country":"일식","type":"밥","taste":"담백한맛"},
    {"name":"돈카츠","country":"일식","type":"고기","taste":"담백한맛"},

    {"name":"파스타","country":"양식","type":"면","taste":"담백한맛"},
    {"name":"피자","country":"양식","type":"빵","taste":"담백한맛"},
    {"name":"햄버거","country":"양식","type":"빵","taste":"패스트푸드"},
    {"name":"샌드위치","country":"양식","type":"빵","taste":"가벼운맛"},
    {"name":"스테이크","country":"양식","type":"고기","taste":"담백한맛"},

    {"name":"떡볶이","country":"분식","type":"떡","taste":"매운맛"},
    {"name":"김밥","country":"분식","type":"밥","taste":"담백한맛"},
    {"name":"순대","country":"분식","type":"고기","taste":"담백한맛"},
    {"name":"라볶이","country":"분식","type":"면","taste":"매운맛"},

    {"name":"치킨","country":"야식","type":"고기","taste":"야식"},
    {"name":"족발","country":"야식","type":"고기","taste":"야식"},
    {"name":"보쌈","country":"야식","type":"고기","taste":"야식"},
    {"name":"닭발","country":"야식","type":"고기","taste":"매운맛"},

    {"name":"샐러드","country":"기타","type":"샐러드","taste":"다이어트"},
    {"name":"포케","country":"기타","type":"샐러드","taste":"다이어트"},
    {"name":"그릭요거트","country":"기타","type":"디저트","taste":"다이어트"},
    {"name":"빙수","country":"기타","type":"디저트","taste":"달달한맛"},
    {"name":"케이크","country":"기타","type":"디저트","taste":"달달한맛"},
    {"name":"요아정","country":"기타","type":"디저트","taste":"달달한맛"}
]

# ----------------------------
# 선택
# ----------------------------

meal = st.radio(
    "식사",
    ["🍱 점심", "🌙 저녁"],
    horizontal=True
)

country = st.selectbox(
    "🌍 나라/카테고리",
    ["상관없음","한식","중식","일식","양식","분식","야식","기타"]
)

food_type = st.selectbox(
    "🍽️ 음식 종류",
    ["상관없음","밥","면","빵","고기","국물","샐러드","디저트"]
)

taste = st.selectbox(
    "😋 지금 당기는 맛",
    [
        "상관없음",
        "매운맛",
        "담백한맛",
        "국물",
        "시원한맛",
        "얼큰한맛",
        "달달한맛",
        "해장",
        "다이어트",
        "야식",
        "패스트푸드",
        "가벼운맛"
    ]
)

# ----------------------------
# 추천
# ----------------------------

if st.button("🍀 메뉴 추천받기", use_container_width=True):

    result = menus

    if country != "상관없음":
        result = [m for m in result if m["country"] == country]

    if food_type != "상관없음":
        result = [m for m in result if m["type"] == food_type]

    if taste != "상관없음":
        result = [m for m in result if m["taste"] == taste]

    if result:
        menu = random.choice(result)

        if meal == "🍱 점심":
            st.success(f"## 🍱 오늘의 점메추\n\n# 🍽️ {menu['name']}")
        else:
            st.success(f"## 🌙 오늘의 저메추\n\n# 🍽️ {menu['name']}")

        st.write(f"**나라/카테고리:** {menu['country']}")
        st.write(f"**종류:** {menu['type']}")
        st.write(f"**특징:** {menu['taste']}")

        st.balloons()

    else:
        st.warning("😢 조건에 맞는 메뉴가 없습니다.\n\n'상관없음'을 선택하거나 다른 조건으로 다시 시도해 보세요.")
