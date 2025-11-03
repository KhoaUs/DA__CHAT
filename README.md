# DA__CHAT
Data Analysis Chatbot (DA__CHAT)

Short guide to run and debug the Streamlit chatbot with speech-to-text (audiorecorder + SpeechRecognition).

## Contents
- Quick choices: Docker (rebuild) / Docker bind-mount (dev) / Local venv (dev)
- How to test speech-to-text
- Troubleshooting & logs

---

## Prerequisites
- Docker installed (for Docker options)
- Or Python 3.10+ and pip (for local run)
- Internet access (SpeechRecognition uses Google Web Speech API)
- Make sure your browser allows microphone access for `http://localhost:8501`.
- If you run locally and audio libraries require `ffmpeg`, install it on your system (Windows: add ffmpeg to PATH).

---

## 1) Run with Docker (rebuild image)
Use this when you want the container image to include the latest code and dependencies.

Open PowerShell in `DA__CHAT` directory and run:

```powershell
# Stop & remove current container (if exists)
docker stop da_chat_container; docker rm da_chat_container

# Rebuild image from current folder
docker build -t da_chat:latest .

# Run new container
docker run -d -p 8501:8501 --name da_chat_container da_chat:latest
```

Visit: http://localhost:8501

Note: Rebuilding is required if you change dependencies or Dockerfile. For code-only edits, the bind-mount approach below is faster.

---

## 2) Run with Docker + bind-mount (fast dev iteration)
Mount your local folder into the container so edits are reflected immediately without rebuilding. This assumes the Docker image's CMD runs `streamlit run app.py` in `/app`.

```powershell
docker stop da_chat_container; docker rm da_chat_container

# Bind-mount local DA__CHAT into /app in the container
docker run -d -p 8501:8501 --name da_chat_container -v "D:\\Education\\HCMUS\\HKX\\PhanTichDuLieuThongMiinh\\DA__CHAT:/app" da_chat:latest
```

Then open http://localhost:8501 and edit files locally. Reload the page (Streamlit usually hot-reloads).

---

## 3) Run locally (recommended for debugging)
This runs Streamlit directly on your machine; easiest to see errors and logs.

```powershell
cd D:\\Education\\HCMUS\\HKX\\PhanTichDuLieuThongMiinh\\DA__CHAT
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

Open http://localhost:8501

Notes:
- If `pip install` fails, check Python version and install build tools.
- If `ffmpeg` is required by audio libraries (pydub), install ffmpeg and ensure it's on PATH.

---

## How to test speech-to-text in the app
1. Open the app in your browser and allow microphone permission when prompted.
2. The microphone button is located next to the Send/Gửi button in the chat input bar.
3. Click the mic to start recording, click stop when done.
4. After transcription completes, the recognized text should appear (prefill) in the chat input box so you can edit before sending.

If nothing appears:
- Look at the Streamlit UI for any error panels (the app surfaces transcription errors).
- Check container logs or terminal logs (see next section).

---

## Logs & Debugging
- Tail Docker container logs:

```powershell
docker logs -f da_chat_container
```

- If running locally, errors and tracebacks appear in the terminal where you ran `streamlit run`.
- Common problems:
	- No microphone access in browser — allow mic for `localhost` or check browser site settings.
	- `ffmpeg` missing — install system ffmpeg (used by pydub/audiorecorder) and add to PATH.
	- No internet — SpeechRecognition using Google API needs internet for transcription.

---

## Notes about STT behavior
- The app uses the `audiorecorder` component (client-side) and `SpeechRecognition` (server-side) with Google Web Speech API.
- `audiorecorder` can return different types depending on version (pydub AudioSegment or raw bytes); the app attempts to handle common types.
- If transcription raises an error, the app will display it in the Streamlit UI to help debugging.

---

## Quick troubleshooting checklist
- Is the container running and mapped to port 8501?
	- `docker ps --filter "name=da_chat_container"`
- Are there errors in logs?
	- `docker logs --tail 200 da_chat_container`
- Is microphone access allowed in the browser?
- Is `ffmpeg` installed (for pydub) if you see errors about audio processing?
- Is there internet access for Google Speech API?

---

## If you want, I can:
- Restart the container with bind-mount (so your local edits show instantly) and tail logs while you test the mic.
- Or run the app locally in a venv and reproduce any errors here.

If you want me to perform one of those, tell me which option and I'll run the commands for you.

---

Vietnamese (tóm tắt nhanh)

- Để chạy nhanh khi phát triển: dùng lệnh bind-mount Docker ở trên hoặc chạy `streamlit` local.
- Muốn cập nhật image dùng `docker build` rồi chạy lại container.
- Nếu không thấy text sau ghi âm: kiểm tra quyền mic trên trình duyệt, logs của container/terminal, và cài `ffmpeg` nếu cần.

---

File location: `D:\\Education\\HCMUS\\HKX\\PhanTichDuLieuThongMiinh\\DA__CHAT`

Happy testing — tell me which run mode you want me to execute now.
# DA__CHAT