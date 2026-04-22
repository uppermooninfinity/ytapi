import os
import uuid
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
import yt_dlp

app = FastAPI()

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# memory token storage
TOKENS = {}

# 🎯 DOWNLOAD ENDPOINT
@app.get("/download")
async def download(url: str, type: str):
    try:
        ydl_opts = {
            "format": "bestaudio/best" if type == "audio" else "best",
            "outtmpl": f"{DOWNLOAD_DIR}/%(id)s.%(ext)s",
            "quiet": True,
            "geo_bypass": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        video_id = info["id"]
        ext = info["ext"]

        file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.{ext}")

        if not os.path.exists(file_path):
            raise Exception("File not downloaded")

        # 🔑 generate token
        token = str(uuid.uuid4())
        TOKENS[token] = file_path

        return {
            "download_token": token,
            "video_id": video_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 🎯 STREAM ENDPOINT
@app.get("/stream/{video_id}")
async def stream(video_id: str, request: Request, type: str):
    token = request.headers.get("X-Download-Token")

    if not token or token not in TOKENS:
        raise HTTPException(status_code=403, detail="Invalid token")

    file_path = TOKENS[token]

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    def iterfile():
        with open(file_path, "rb") as f:
            while chunk := f.read(1024 * 1024):
                yield chunk

    return StreamingResponse(iterfile(), media_type="audio/mpeg")
