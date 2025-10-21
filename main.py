from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
import yt_dlp
import tempfile
from pathlib import Path

app = FastAPI(title="AAHH YouTube Downloader API")

@app.get("/download")
def download_audio(url: str = Query(..., description="YouTube URL")):
    """
    Downloads the audio from a YouTube URL as an MP3.
    Uses yt-dlp with ffmpeg and optional cookies.txt for authenticated access.
    """

    tmpdir = tempfile.mkdtemp()
    output_path = Path(tmpdir) / "audio.%(ext)s"
    cookies_path = Path(__file__).parent / "cookies.txt"

    # yt-dlp configuration
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(output_path),
        "quiet": True,
        "noplaylist": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "ffmpeg_location": "/usr/bin",  # Ensures ffmpeg works inside Railway container
    }

    # Use cookies for authenticated or age-restricted videos
    if cookies_path.exists():
        print(f"✅ Using cookies from {cookies_path}")
        ydl_opts["cookiefile"] = str(cookies_path)
    else:
        print("⚠️ No cookies.txt found — YouTube may block or rate-limit some videos.")

    try:
        # Run yt-dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)

        # Locate the generated MP3
        mp3_path = next(Path(tmpdir).glob("*.mp3"), None)
        if not mp3_path:
            raise HTTPException(status_code=500, detail="MP3 not found after download.")

        print(f"🎧 Successfully processed: {url}")
        return FileResponse(
            mp3_path,
            media_type="audio/mpeg",
            filename="audio.mp3"
        )

    except yt_dlp.utils.DownloadError as e:
        msg = str(e)
        if "Sign in to confirm" in msg or "cookies" in msg:
            raise HTTPException(
                status_code=401,
                detail="YouTube requires authentication. Please refresh your cookies.txt file."
            )
        raise HTTPException(status_code=400, detail=f"Download error: {msg}")

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
