# 🎬 AI YouTube Shorts Factory

An AI-powered system that discovers viral YouTube videos, detects engaging moments automatically, generates Shorts clips, and creates AI-powered viral metadata — fully locally using open-source tools.

---

# 🚀 Features

## 🔥 Discovery Agent

Search and discover viral YouTube videos by topic.

### Capabilities

* Topic-based YouTube search
* Viral scoring system
* Thumbnail previews
* Video metadata display
* Streamlit UI
* Direct integration with clipping agent

---

## ✂️ Clipping Agent

Automatically extracts engaging moments from YouTube videos and converts them into Shorts-ready vertical clips.

### Capabilities

* YouTube video downloading
* Video caching system
* AI transcript generation
* Viral moment detection
* Multi-duration clip generation
* Vertical Shorts conversion
* Download clips directly from UI

### Supported Clip Durations

* AI Suggested
* 10 seconds
* 20 seconds
* 30 seconds

---

## 🤖 AI Metadata Generator

Powered locally using Ollama + Llama 3.2.

Automatically generates:

* Viral YouTube Shorts titles
* Trending hashtags
* Hook captions

---

# 🛠 Tech Stack

* Python
* Streamlit
* Whisper
* Ollama
* Llama 3.2
* yt-dlp
* ffmpeg
* spaCy
* librosa
* NumPy

---

# 📂 Project Structure

```text
youtube-agent/
│
├── discovery-agent/
│   └── app.py
│
├── clipping-agent/
│   └── app.py
│
├── README.md
└── .gitignore
```

---

# 🚀 Setup

## 1. Clone Repository

```bash
git clone https://github.com/rv-13/youtube-agent.git

cd youtube-agent
```

---

## 2. Install Ollama

Install Ollama:

https://ollama.com

Pull model:

```bash
ollama pull llama3.2
```

---

## 3. Install FFmpeg

### Mac

```bash
brew install ffmpeg
```

---

## 4. Install Python Dependencies

### Discovery Agent

```bash
cd discovery-agent

python3 -m venv venv

source venv/bin/activate

pip install -r requirements.txt
```

---

### Clipping Agent

```bash
cd clipping-agent

python3 -m venv venv

source venv/bin/activate

pip install -r requirements.txt
```

---

# 🚀 Run Discovery Agent

```bash
cd discovery-agent

streamlit run app.py
```

---

# 🚀 Run Clipping Agent

```bash
cd clipping-agent

streamlit run app.py
```

---

# 🔥 Current Capabilities

✅ Viral YouTube discovery
✅ AI clip detection
✅ Shorts generation
✅ Multi-duration clips
✅ AI-generated metadata
✅ Downloadable clips
✅ Local AI inference
✅ Cached video processing

---

# 📌 Future Improvements

* Auto upload to YouTube Shorts
* AI background music generation
* Multi-language captions
* AI retention scoring
* Cloud deployment
* Queue-based processing
* Auto subtitle generation

---

# ⚠️ Disclaimer

This project is intended for educational and research purposes only.

Users are responsible for complying with YouTube copyright policies, platform terms of service, and applicable content usage rights.
