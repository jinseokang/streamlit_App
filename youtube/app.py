import streamlit as st
import pandas as pd
import re
from googleapiclient.discovery import build
from urllib.parse import urlparse, parse_qs

import plotly.express as px

from wordcloud import WordCloud
import matplotlib.pyplot as plt

from konlpy.tag import Okt

from textblob import TextBlob

st.set_page_config(
    page_title="유튜브 댓글 분석기",
    page_icon="📊",
    layout="wide"
)

# -----------------------------
# 제목
# -----------------------------

st.title("📊 유튜브 댓글 분석기")
st.markdown("유튜브 영상의 댓글을 수집하고 분석합니다.")

# -----------------------------
# API KEY
# -----------------------------

api_key = st.text_input(
    "AIzaSyDjVDpNMP-FsJV6uWUcms8kJ3adAiypAyo",
    type="password"
)

# -----------------------------
# URL 입력
# -----------------------------

video_url = st.text_input(
    "유튜브 영상 링크",
    placeholder="https://www.youtube.com/watch?v=..."
)

max_comments = st.slider(
    "수집 댓글 수",
    100,
    5000,
    1000,
    100
)

# -----------------------------
# 함수
# -----------------------------

def get_video_id(url):
    try:
        parsed = urlparse(url)

        if parsed.hostname == "youtu.be":
            return parsed.path[1:]

        if parsed.hostname in (
            "www.youtube.com",
            "youtube.com"
        ):
            return parse_qs(parsed.query)["v"][0]

    except:
        return None

    return None


def sentiment(text):

    try:
        score = TextBlob(text).sentiment.polarity

        if score > 0.1:
            return "긍정"

        elif score < -0.1:
            return "부정"

        else:
            return "중립"

    except:
        return "중립"


def get_comments(youtube, video_id, max_results):

    comments = []

    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=100,
        textFormat="plainText"
    )

    while request and len(comments) < max_results:

        response = request.execute()

        for item in response["items"]:

            comment = item["snippet"]["topLevelComment"]["snippet"]

            comments.append(
                {
                    "text": comment["textDisplay"],
                    "date": comment["publishedAt"]
                }
            )

            if len(comments) >= max_results:
                break

        request = youtube.commentThreads().list_next(
            request,
            response
        )

    return pd.DataFrame(comments)


# -----------------------------
# 분석 시작
# -----------------------------

if st.button("분석 시작"):

    if not api_key:
        st.error("API Key를 입력하세요.")
        st.stop()

    video_id = get_video_id(video_url)

    if not video_id:
        st.error("유튜브 링크를 확인하세요.")
        st.stop()

    youtube = build(
        "youtube",
        "v3",
        developerKey=api_key
    )

    # 영상 표시

    st.subheader("🎬 영상")

    st.video(video_url)

    with st.spinner("댓글 수집 중..."):

        df = get_comments(
            youtube,
            video_id,
            max_comments
        )

    if len(df) == 0:
        st.warning("댓글이 없습니다.")
        st.stop()

    st.success(f"{len(df):,}개 댓글 수집 완료")

    # -------------------------
    # 날짜 처리
    # -------------------------

    df["date"] = pd.to_datetime(df["date"])

    df["hour"] = df["date"].dt.hour

    # -------------------------
    # 댓글 추이
    # -------------------------

    st.subheader("📈 시간대별 댓글 작성 추이")

    hourly = (
        df.groupby("hour")
        .size()
        .reset_index(name="count")
    )

    fig = px.line(
        hourly,
        x="hour",
        y="count",
        markers=True
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # -------------------------
    # 감성 분석
    # -------------------------

    st.subheader("😊 댓글 반응도")

    df["sentiment"] = df["text"].apply(
        sentiment
    )

    sentiment_df = (
        df["sentiment"]
        .value_counts()
        .reset_index()
    )

    sentiment_df.columns = [
        "감성",
        "개수"
    ]

    fig2 = px.pie(
        sentiment_df,
        names="감성",
        values="개수"
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )

    # -------------------------
    # 워드클라우드
    # -------------------------

    st.subheader("☁️ 한글 워드클라우드")

    okt = Okt()

    all_text = " ".join(
        df["text"].astype(str)
    )

    nouns = okt.nouns(all_text)

    nouns = [
        n
        for n in nouns
        if len(n) >= 2
    ]

    text_for_cloud = " ".join(nouns)

    if text_for_cloud:

        wordcloud = WordCloud(
            width=1200,
            height=600,
            background_color="white",
            font_path="malgun.ttf"
        ).generate(text_for_cloud)

        fig3, ax = plt.subplots(
            figsize=(12,6)
        )

        ax.imshow(wordcloud)
        ax.axis("off")

        st.pyplot(fig3)

    # -------------------------
    # 댓글 테이블
    # -------------------------

    st.subheader("💬 댓글 데이터")

    st.dataframe(
        df,
        use_container_width=True
    )

    csv = df.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        "CSV 다운로드",
        csv,
        file_name="youtube_comments.csv",
        mime="text/csv"
    )
