
import re
import subprocess
import librosa
import numpy as np
from youtube_transcript_api import YouTubeTranscriptApi
import spacy
from pathlib import Path


def get_video_file():

    for ext in ["mp4", "webm", "mkv"]:

        files = list(Path(".").glob(f"video*.{ext}"))

        if files:
            return str(files[0])

    raise FileNotFoundError("No video file found")

nlp = spacy.load("en_core_web_sm")


def extract_video_id(url):
    patterns = [
        r"v=([^&]+)",
        r"youtu\.be/([^?]+)",
        r"shorts/([^?]+)"
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    raise ValueError("Invalid YouTube URL")


def get_transcript(video_id):
    ytt_api = YouTubeTranscriptApi()
    fetched_transcript = ytt_api.fetch(video_id)

    transcript = []

    for snippet in fetched_transcript:
        transcript.append({
            "text": snippet.text,
            "start": snippet.start,
            "duration": snippet.duration
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
        "insane"
    ]

    score += sum(text.lower().count(k) for k in keywords) * 3

    return score


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


def download_video(url):

    subprocess.run([
        "yt-dlp",
        "--no-playlist",
        "-f",
        "bv*+ba/b",
        "-o",
        "video.%(ext)s",
        url
    ])

def extract_audio():
    cmd = [
        "ffmpeg",
        "-i",
        get_video_file(),
        "-q:a",
        "0",
        "-map",
        "a",
        "audio.mp3",
        "-y"
    ]

    subprocess.run(cmd)

def calculate_audio_energy(start, end):
    y, sr = librosa.load("audio.mp3")

    start_sample = int(start * sr)
    end_sample = int(end * sr)

    segment = y[start_sample:end_sample]

    energy = np.mean(np.abs(segment))

    return energy

def cut_clip(start, end, index):

    duration = end - start

    output = f"clip_{index}.mp4"

    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        str(start),
        "-i",
        get_video_file(),
        "-t",
        str(duration),
        "-vf",
        "scale=1280:720",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "23",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        "+faststart",
        output
    ]

    subprocess.run(cmd)


def main():
    url = input("Enter YouTube URL: ")

    video_id = extract_video_id(url)

    print("Downloading video...")
    download_video(url)

    print("Extracting audio...")
    extract_audio()

    print("Fetching transcript...")
    transcript = get_transcript(video_id)

    print("Segmenting transcript...")
    segments = segment_transcript(transcript)

    print("Ranking segments...")
    ranked_segments = rank_segments(segments)

    top_segments = ranked_segments[:3]

    for i, segment in enumerate(top_segments):
        print(f"Creating clip {i+1}...")

        cut_clip(
            segment['start'],
            segment['end'],
            i
        )

    print("Done! Clips saved successfully.")


if __name__ == "__main__":
    main()
