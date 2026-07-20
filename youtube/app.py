import streamlit as st
import pandas as pd
import re
from collections import Counter
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from urllib.parse import urlparse, parse_qs
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from textblob import TextBlob

st.set_page_config(page_title="유튜브 댓글 분석기", page_icon="📊", layout="wide")

st.markdown("""
<style>
.stButton > button {
    background:#ff4b4b;
    color:white;
    border-radius:10px;
    border:none;
    height:50px;
    font-size:18px;
    font-weight:bold;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 유튜브 댓글 분석기")
st.caption("영상 정보, 댓글, 키워드, 워드클라우드 분석")

try:
    api_key = st.secrets["YOUTUBE_API_KEY"]
except Exception:
    st.error("Streamlit Secrets에 YOUTUBE_API_KEY를 등록하세요.")
    st.stop()

video_url = st.text_input("유튜브 링크 입력")
max_comments = st.slider("수집할 댓글 수", 100, 5000, 1000, 100)

def get_video_id(url):
    try:
        parsed = urlparse(url)
        if parsed.hostname == "youtu.be":
            return parsed.path[1:]
        if parsed.hostname in ["youtube.com","www.youtube.com"]:
            return parse_qs(parsed.query)["v"][0]
    except Exception:
        return None

def sentiment(text):
    try:
        score = TextBlob(text).sentiment.polarity
        if score > 0.1:
            return "긍정"
        elif score < -0.1:
            return "부정"
        return "중립"
    except Exception:
        return "중립"

def get_video_info(youtube, video_id):
    response = youtube.videos().list(
        part="snippet,statistics",
        id=video_id
    ).execute()

    if not response["items"]:
        return None

    item = response["items"][0]

    return {
        "title": item["snippet"]["title"],
        "channel": item["snippet"]["channelTitle"],
        "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
        "views": int(item["statistics"].get("viewCount", 0)),
        "likes": int(item["statistics"].get("likeCount", 0)),
        "comments": int(item["statistics"].get("commentCount", 0))
    }

def get_comments(youtube, video_id, max_count):
    comments = []

    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=100,
        textFormat="plainText"
    )

    while request and len(comments) < max_count:
        response = request.execute()

        for item in response["items"]:
            snippet = item["snippet"]["topLevelComment"]["snippet"]

            comments.append({
                "댓글": snippet["textDisplay"],
                "작성일": snippet["publishedAt"],
                "좋아요": snippet["likeCount"]
            })

            if len(comments) >= max_count:
                break

        request = youtube.commentThreads().list_next(request, response)

    return pd.DataFrame(comments)

if st.button("🚀 분석 시작"):

    video_id = get_video_id(video_url)

    if not video_id:
        st.error("올바른 유튜브 링크를 입력하세요.")
        st.stop()

    try:
        youtube = build("youtube", "v3", developerKey=api_key)

        video_info = get_video_info(youtube, video_id)

        st.subheader("🎬 영상")
        st.video(video_url)

        if video_info:
            st.markdown(f"### {video_info['title']}")
            st.write(f"채널: {video_info['channel']}")

            c1, c2, c3 = st.columns(3)
            c1.metric("조회수", f"{video_info['views']:,}")
            c2.metric("좋아요", f"{video_info['likes']:,}")
            c3.metric("댓글수", f"{video_info['comments']:,}")

        with st.spinner("댓글 수집 중..."):
            df = get_comments(youtube, video_id, max_comments)

    except HttpError as e:
        st.error(f"API 오류: {e}")
        st.stop()

    if df.empty:
        st.warning("댓글이 없습니다.")
        st.stop()

    st.success(f"{len(df):,}개 댓글 수집 완료")

    df["작성일"] = pd.to_datetime(df["작성일"])
    df["시간"] = df["작성일"].dt.hour

    st.subheader("📈 시간대별 댓글 작성 추이")

    hourly = df.groupby("시간").size().reset_index(name="댓글수")

    fig = px.line(hourly, x="시간", y="댓글수", markers=True)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("😊 댓글 반응도")
    df["감성"] = df["댓글"].apply(sentiment)

    sentiment_df = df["감성"].value_counts().reset_index()
    sentiment_df.columns = ["감성", "개수"]

    fig2 = px.pie(sentiment_df, names="감성", values="개수", hole=0.4)
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("👍 인기 댓글 TOP10")
    st.dataframe(
        df.sort_values("좋아요", ascending=False).head(10),
        use_container_width=True
    )

    st.subheader("☁️ 댓글 워드클라우드")

    all_text = " ".join(df["댓글"].astype(str))

    words = re.findall(r"[가-힣]{2,}", all_text)

    stopwords = {
        "진짜","정말","영상","이번","댓글","유튜브","그냥","너무",
        "오늘","사람","채널","생각","때문","근데","이거","저거",
        "그리고","하지만","대한","있는","입니다","합니다"
    }

    filtered = [w for w in words if w not in stopwords and len(w) >= 2]

    if filtered:
        text_for_cloud = " ".join(filtered)

        try:
            wc = WordCloud(
                font_path="NanumGothic.ttf",
                width=1600,
                height=900,
                background_color="white",
                max_words=200
            ).generate(text_for_cloud)
        except Exception:
            wc = WordCloud(
                width=1600,
                height=900,
                background_color="white",
                max_words=200
            ).generate(text_for_cloud)

        fig3, ax = plt.subplots(figsize=(15, 8))
        ax.imshow(wc)
        ax.axis("off")
        st.pyplot(fig3)

        st.subheader("🔥 댓글 키워드 TOP20")

        top_words = pd.DataFrame(
            Counter(filtered).most_common(20),
            columns=["키워드", "횟수"]
        )

        st.dataframe(top_words, use_container_width=True)

    st.subheader("💬 전체 댓글")
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        "📥 CSV 다운로드",
        csv,
        file_name="youtube_comments.csv",
        mime="text/csv"
    )
