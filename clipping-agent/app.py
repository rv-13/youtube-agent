import time
import streamlit as st
import re
import subprocess
import librosa
import numpy as np
import spacy
import whisper
import random
import os
import ollama

from pathlib import Path
from datetime import datetime

st.set_page_config(
    page_title="YouTube Agent",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

nlp = spacy.load("en_core_web_sm")



def get_video_file():

    for ext in ["mp4", "webm", "mkv"]:

        files = list(Path(".").glob(f"video*.{ext}"))

        if files:
            return str(sorted(files)[-1])

    raise FileNotFoundError("No video file found")

def get_video_duration(video_path):

    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        video_path
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    return float(result.stdout.strip())

def clean_youtube_url(url):

    if "watch?v=" in url:
        return url.split("&")[0]

    if "?list=" in url:
        return url.split("?")[0]

    return url

def extract_video_id(url):

    patterns = [
        r"v=([^&]+)",
        r"youtu\\.be/([^?]+)",
        r"shorts/([^?]+)"
    ]

    for pattern in patterns:

        match = re.search(pattern, url)

        if match:
            return match.group(1)

    raise ValueError("Invalid YouTube URL")

def get_transcript(whisper_model):

    result = whisper_model.transcribe(
        "audio.mp3",
        task="transcribe"
    )

    transcript = []

    for segment in result["segments"]:

        transcript.append({
            "text": segment["text"],
            "start": segment["start"],
            "duration": segment["end"] - segment["start"]
        })

    return transcript



def segment_transcript(transcript, window=30):

    segments = []

    current_text = []
    start_time = transcript[0]['start']

    for entry in transcript:

        current_text.append(entry['text'])

        if entry['start'] - start_time >= window:

            segments.append({
                "text": " ".join(current_text),
                "start": start_time,
                "end": entry['start'] + entry['duration']
            })

            current_text = []
            start_time = entry['start']

    return segments



def score_segment(text):

    doc = nlp(text)

    score = 0

    score += len(doc.ents) * 2
    score += len(list(doc.sents))

    keywords = [
        "amazing",
        "shocking",
        "crazy",
        "secret",
        "insane",
        "truth",
        "viral",
        "money",
        "motivation"
    ]

    score += sum(text.lower().count(k) for k in keywords) * 3

    return score

def generate_ai_metadata(text):

    prompt = f"""
    You are an English YouTube Shorts strategist.

    Based on this transcript:

    {text}

    Generate:

    1. Viral YouTube Shorts title
    2. 10 viral hashtags
    3. Hook caption

    Rules:
    - emotional
    - curiosity-driven
    - optimized for clicks
    - optimized for YouTube Shorts
    - keep title under 70 chars

    IMPORTANT:
    Generate EVERYTHING ONLY in English.
    Do NOT use Spanish, Hindi, Telugu, or any other language.

    Return format:

    TITLE:
    ...

    HASHTAGS:
    ...

    CAPTION:
    ...
    """

    response = ollama.chat(

        model='llama3.2',

        messages=[
            {
                'role': 'user',
                'content': prompt
            }
        ]
    )

    return response['message']['content']

def download_video(url):

    url = clean_youtube_url(url)

    if os.path.exists("audio.mp3"):
        os.remove("audio.mp3")

    video_id = extract_video_id(url)

    os.makedirs("cache", exist_ok=True)

    existing_files = list(
        Path("cache").glob(f"{video_id}.*")
    )

    if existing_files:

        st.write("⚡ Using cached video")

        return str(existing_files[0])

    output_name = f"cache/{video_id}.%(ext)s"

    subprocess.run([
        "yt-dlp",
        "--no-playlist",

        "-f",
        "best[height<=720][fps<=30]",

        "--merge-output-format",
        "mp4",

        "-o",
        output_name,

        url
    ])

    downloaded_files = list(
        Path("cache").glob(f"{video_id}.*")
    )

    return str(downloaded_files[0])

    

def extract_audio(video_path, processing_limit):

    duration_seconds = None

    if processing_limit == "3 min":
        duration_seconds = "180"

    elif processing_limit == "5 min":
        duration_seconds = "300"

    elif processing_limit == "10 min":
        duration_seconds = "600"

    cmd = [
        "ffmpeg",
        "-i",
        video_path,
    ]

    if duration_seconds:

        cmd.extend([
            "-t",
            duration_seconds
        ])

    cmd.extend([

        "-vn",

        "-acodec",
        "mp3",

        "-ab",
        "64k",

        "audio.mp3",

        "-y"
    ])

    subprocess.run(cmd)

def calculate_audio_energy(start, end):

    y, sr = librosa.load("audio.mp3")

    start_sample = int(start * sr)
    end_sample = int(end * sr)

    segment = y[start_sample:end_sample]

    if len(segment) == 0:
        return 0

    energy = np.mean(np.abs(segment))

    return energy



def rank_segments(segments):

    for segment in segments:

        transcript_score = score_segment(segment['text'])

        audio_score = calculate_audio_energy(
            segment['start'],
            segment['end']
        ) * 100

        final_score = transcript_score + audio_score

        segment['score'] = final_score

    return sorted(
        segments,
        key=lambda x: x['score'],
        reverse=True
    )



def cut_clip(video_path,start,end,index,output_quality):

    duration = end - start

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    start_label = f"{int(start//60):02d}m{int(start%60):02d}s"

    end_label = f"{int(end//60):02d}m{int(end%60):02d}s"

    output = f"clip_{start_label}_{end_label}_{timestamp}.mp4"

    preset = "ultrafast"
    bitrate = "3M"

    if output_quality == "Balanced":

        preset = "medium"
        bitrate = "5M"

    elif output_quality == "High":

        preset = "slow"
        bitrate = "8M"

    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        str(start),
        "-i",
        video_path,
        "-t",
        str(duration),

        "-vf",
        "split=2[bg][fg];"
        "[bg]scale=720:1280:force_original_aspect_ratio=increase,"
        "boxblur=5:1,crop=720:1280[bg];"
        "[fg]scale=720:-2[fg];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2",

        "-c:v",
        "h264_videotoolbox",

        "-preset",
        preset,

        "-b:v",
        bitrate,

        "-c:a",
        "aac",

        "-b:a",
        "192k",

        "-movflags",
        "+faststart",

        output
    ]

    subprocess.run(cmd)

    return output


st.title(
    "🎬 AI YouTube Shorts Factory"
)

st.caption(
    "Discovering viral moments and generate Shorts automatically"
)
st.sidebar.title("⚙️ Settings")

max_clips = st.sidebar.slider(
    "🎬 Number of Clips",
    min_value=1,
    max_value=5,
    value=1
)
processing_limit = st.sidebar.selectbox(
    "⏱ Processing Duration",
    [
        "3 min",
        "5 min",
        "10 min",
        "Full Video"
    ],
    index=1
)
whisper_choice = st.sidebar.selectbox(
    "🧠 Whisper Model",
    [
        "tiny",
        "base"
    ],
    index=0
)
output_quality = st.sidebar.selectbox(
    "🎥 Output Quality",
    [
        "Fast",
        "Balanced",
        "High"
    ],
    index=0
)

query_params = st.query_params

default_video = query_params.get(
    "video",
    ""
)

url = st.text_input(
    "Paste YouTube URL",
    value=default_video
)

duration_options = st.multiselect(

    "🎬 Select Clip Durations",
    [
        "AI Suggested",
        "10 sec",
        "20 sec",
        "30 sec"
    ],

    default=["AI Suggested"]
)

if st.button("Generate Clips"):

    if not url.strip():

        st.warning("Please paste a YouTube URL")

        st.stop()

    with st.spinner("Processing video..."):

        progress_bar = st.progress(0)

        status_text = st.empty()

        timer_text = st.empty()

        status_text.write(
            f"🧠 Loading Whisper model: {whisper_choice}"
        )

        whisper_model = whisper.load_model(
            whisper_choice
        )

        status_text.write("📥 Downloading video...")

        progress_bar.progress(15)

        video_path = download_video(url)

        video_duration = get_video_duration(video_path)

        estimated_seconds = int(video_duration * 0.15)
        start_time = time.time()

        status_text.write("🎵 Extracting audio...")

        progress_bar.progress(35)

        extract_audio(video_path, processing_limit)

        elapsed = int(time.time() - start_time)

        remaining = max(
            estimated_seconds - elapsed,
            0
        )

        mins = remaining // 60
        secs = remaining % 60

        status_text.write(
            "🧠 AI transcribing video..."
        )

        timer_text.info(
            f"⏳ Estimated time left: {mins}m {secs}s"
        )

        progress_bar.progress(55)
        
        for remaining in range(
            estimated_seconds,
            0,
            -1
        ):

            mins = remaining // 60
            secs = remaining % 60

            timer_text.info(
                f"⏳ Estimated time left: {mins}m {secs}s"
            )

            time.sleep(1)

            if remaining <= estimated_seconds - 5:
                break

        transcript = get_transcript(whisper_model)

        if not transcript:
            st.error(
                "Transcript generation failed"
            )

            st.stop()

        status_text.write(
            "🔥 Detecting viral moments..."
        )

        progress_bar.progress(75)

        segments = segment_transcript(transcript)

        ranked_segments = rank_segments(segments)
    
        if not ranked_segments:
            st.error(
                "No engaging clips found"
            )

            st.stop()

        top_segments = random.sample(
            ranked_segments[:max_clips],
            min(max_clips, len(ranked_segments))
        )   
        status_text.write(
            "✂️ Generating clips..."
        )

        progress_bar.progress(90)

        for i, segment in enumerate(top_segments):

            metadata = generate_ai_metadata(
                segment['text']
            )

            for duration_option in duration_options:

                clip_start = segment['start']

                clip_end = segment['end']

                duration_label = "ai"

                if duration_option == "10 sec":

                    clip_end = clip_start + 10
                    duration_label = "10s"

                elif duration_option == "20 sec":

                    clip_end = clip_start + 20
                    duration_label = "20s"

                elif duration_option == "30 sec":

                    clip_end = clip_start + 30
                    duration_label = "30s"

                clip_name = cut_clip(
                    video_path,
                    clip_start,
                    clip_end,
                    f"{i}_{duration_label}",
                    output_quality
                )

                st.markdown("---")

                st.subheader(
                        f"🎬 Viral Clip {i+1} • {duration_option}"
                    )

                st.video(clip_name)

                with open(clip_name, "rb") as file:

                    st.download_button(
                        label=f"⬇️ Download {duration_option}",
                        data=file,
                        file_name=clip_name,
                        mime="video/mp4"
                    )

            st.subheader(f"Clip {i+1}")

            st.write(f"Score: {segment['score']:.2f}")

            st.markdown("### 🚀 AI Viral Metadata")

            st.code(metadata)

            st.write(segment['text'])

            st.video(clip_name)

            with open(clip_name, "rb") as file:

                st.download_button(
                    label="⬇️ Download Clip",
                    data=file,
                    file_name=clip_name,
                    mime="video/mp4"
                )

    progress_bar.progress(100)

    timer_text.empty()

    status_text.write(
        "✅ Clips generated successfully!"
    )
    st.success("Done!")
