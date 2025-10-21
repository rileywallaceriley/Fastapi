from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
import yt_dlp
import tempfile
from pathlib import Path

app = FastAPI(title="AAHH YouTube Downloader")

@app.get("/download")
def download_audio(url: str = Query(..., description="YouTube URL")):
    """
    Downloads the audio from a given YouTube URL,
    converts it to MP3 using ffmpeg, and returns the file.
    """
    tmpdir = tempfile.mkdtemp()
    output_path = Path(tmpdir) / "audio.%(ext)s"

    # yt-dlp configuration with ffmpeg location fix
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
        "ffmpeg_location": "/usr/bin",  # helps yt-dlp find ffmpeg in Railway container
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)

        # Find the MP3 file
        mp3_path = next(Path(tmpdir).glob("*.mp3"), None)
        if not mp3_path:
            raise HTTPException(status_code=500, detail="MP3 not found after download.")

        # Return MP3 file
        return FileResponse(
            mp3_path,
            media_type="audio/mpeg",
            filename="audio.mp3"
        )

    except yt_dlp.utils.DownloadError as e:
        raise HTTPException(status_code=400, detail=f"Download error: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
