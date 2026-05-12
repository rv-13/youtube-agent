import streamlit as st
import yt_dlp

st.set_page_config(
    page_title="Discovery Agent",
    page_icon="🔥",
    layout="wide"
)

st.title("🔥 YouTube Discovery Agent")

if "videos" not in st.session_state:
    st.session_state.videos = []

with st.form("search_form"):

    topic = st.text_input(
        "Enter Topic",
        placeholder="cricket, boxing, podcasts..."
    )
    if topic.strip() == "":
        st.session_state.videos = []

    submitted = st.form_submit_button(
        "Find Viral Videos"
    )


def search_youtube(topic):

    topic = topic.strip().rstrip("\\")  
    ydl_opts = {

        "quiet": True,

        "noplaylist": True,

        "no_warnings": True,

        
    }

    results = []

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:

        search_query = f"ytsearch10:{topic}"

        search_results = ydl.extract_info(
            search_query,
            download=False,
            process=False
        )

        videos_data = search_results.get(
            "entries",
            []
        )

        for video in videos_data:

            if not video:
                continue

            if not video.get("id"):
                continue

            results.append({

                "title": video.get(
                    "title",
                    "No Title"
                ),

                "url": f"https://youtube.com/watch?v={video.get('id')}",

                "views": video.get(
                    "view_count",
                    0
                ),

                "duration": video.get(
                    "duration",
                    0
                ),

                "channel": video.get(
                    "channel",
                    "Unknown"
                ),

                "thumbnail": video.get(
                    "thumbnail",
                    ""
                ),

                "upload_date": video.get(
                    "upload_date",
                    "Unknown"
                )
            })

        for video in results:

            video["viral_score"] = (
                calculate_viral_score(video)
            )

        results = sorted(
            results,
            key=lambda x: x["viral_score"],
            reverse=True
        )

    return results

def calculate_viral_score(video):

    score = 0

    views = video.get("views") or 0
    duration = video.get("duration") or 0

    title = (
        video.get("title") or ""
    ).lower()

    score += min(views / 100000, 100)

    if duration > 600:
        score += 20

    viral_keywords = [
        "podcast",
        "interview",
        "debate",
        "fight",
        "motivation",
        "shocking",
        "viral",
        "highlights",
        "funny",
        "emotional"
    ]

    for keyword in viral_keywords:

        if keyword in title:
            score += 10

    return score

if submitted:

    if topic.strip() == "":

        st.warning("Please enter a topic")

    else:

        with st.spinner("Searching YouTube..."):

            st.session_state.videos = search_youtube(topic)

        for i, video in enumerate(st.session_state.videos):

            
            if video['thumbnail']:

                st.image(
                    video['thumbnail'],
                    width=300
                )
            else:

                st.write("No thumbnail available")

            st.subheader(f"{i+1}. {video['title']}")

            st.write(f"👀 Views: {video['views']}")

            st.write(
                     f"🔥 Viral Score: {video['viral_score']:.2f}"
                )

            st.write(f"📺 Channel: {video['channel']}")

            st.write(f"⏱ Duration: {video['duration']} sec")

            st.write(f"📅 Upload Date: {video['upload_date']}")

            st.write(video['url'])

            st.code(video['url'])

            clipper_url = (
                    "http://localhost:8502"
                    f"?video={video['url']}"
            )

            st.link_button(
                    "🎬 Generate Clips",
                    clipper_url
            )

            st.divider()