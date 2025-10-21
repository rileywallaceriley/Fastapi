from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
import yt_dlp
import tempfile
from pathlib import Path

app = FastAPI(title="AAHH YouTube Downloader")

@app.get("/download")
def download_audio(url: str = Query(..., description="YouTube URL")):
    tmpdir = tempfile.mkdtemp()
    output_path = Path(tmpdir) / "audio.%(ext)s"
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(output_path),
        "quiet": True,
        "noplaylist": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192"
        }],
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)
        mp3_path = next(Path(tmpdir).glob("*.mp3"), None)
        if not mp3_path:
            raise HTTPException(status_code=500, detail="MP3 not found.")
        return FileResponse(mp3_path, media_type="audio/mpeg", filename="audio.mp3")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
