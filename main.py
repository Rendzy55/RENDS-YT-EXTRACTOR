from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import os
import tempfile
import asyncio

app = FastAPI(
    title="Rends YouTube Extractor API",
    description="Dedicated YouTube Extractor Service powered by yt-dlp & FFmpeg",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

YTDL_BASE_OPTS = {
    'quiet': True,
    'no_warnings': True,
    'extract_flat': False,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'no_color': True,
}

@app.get("/")
def home():
    return {
        "status": "online",
        "service": "Rends YouTube Extractor API",
        "engine": "yt-dlp",
        "endpoints": {
            "extract_info": "/youtube?url=<YOUTUBE_URL>",
            "download_audio": "/download/audio?url=<YOUTUBE_URL>",
            "download_video": "/download/video?url=<YOUTUBE_URL>"
        }
    }

@app.get("/youtube")
async def extract_youtube(url: str = Query(..., description="Link video YouTube")):
    try:
        ydl_opts = {
            **YTDL_BASE_OPTS,
            'format': 'best',
        }
        
        loop = asyncio.get_event_loop()
        def extract():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)
                
        info = await loop.run_in_executor(None, extract)
        
        if not info:
            raise HTTPException(status_code=404, detail="Video tidak ditemukan atau bersifat private.")

        title = info.get('title', 'YouTube Media')
        duration = info.get('duration', 0)
        thumbnail = info.get('thumbnail', '')
        channel = info.get('uploader', info.get('channel', ''))
        view_count = info.get('view_count', 0)
        
        formats = info.get('formats', [])
        audio_url = None
        video_url = None
        
        for f in formats:
            if f.get('acodec') != 'none' and f.get('vcodec') == 'none' and not audio_url:
                audio_url = f.get('url')
            if f.get('acodec') != 'none' and f.get('vcodec') != 'none':
                video_url = f.get('url')

        return {
            "success": True,
            "data": {
                "id": info.get('id'),
                "title": title,
                "duration": duration,
                "thumbnail": thumbnail,
                "channel": channel,
                "views": view_count,
                "audio_stream": audio_url,
                "video_stream": video_url,
                "mp3": f"/download/audio?url={url}",
                "mp4": f"/download/video?url={url}"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/audio")
async def download_audio(url: str = Query(..., description="Link video YouTube")):
    try:
        temp_dir = tempfile.mkdtemp()
        output_template = os.path.join(temp_dir, '%(title)s.%(ext)s')
        
        ydl_opts = {
            **YTDL_BASE_OPTS,
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        
        loop = asyncio.get_event_loop()
        def run_dl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                return filename.rsplit('.', 1)[0] + '.mp3', info.get('title', 'audio')
                
        filepath, song_title = await loop.run_in_executor(None, run_dl)
        
        if not os.path.exists(filepath):
            raise HTTPException(status_code=500, detail="Gagal mengonversi audio ke MP3.")
            
        clean_title = "".join(c for c in song_title if c.isalnum() or c in " ._-").strip()
        
        return FileResponse(
            path=filepath,
            media_type="audio/mpeg",
            filename=f"{clean_title}.mp3"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/video")
async def download_video(url: str = Query(..., description="Link video YouTube")):
    try:
        temp_dir = tempfile.mkdtemp()
        output_template = os.path.join(temp_dir, '%(title)s.%(ext)s')
        
        ydl_opts = {
            **YTDL_BASE_OPTS,
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': output_template,
            'merge_output_format': 'mp4',
        }
        
        loop = asyncio.get_event_loop()
        def run_dl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                if not filename.endswith('.mp4'):
                    filename = filename.rsplit('.', 1)[0] + '.mp4'
                return filename, info.get('title', 'video')
                
        filepath, video_title = await loop.run_in_executor(None, run_dl)
        
        if not os.path.exists(filepath):
            raise HTTPException(status_code=500, detail="Gagal memproses video MP4.")
            
        clean_title = "".join(c for c in video_title if c.isalnum() or c in " ._-").strip()
        
        return FileResponse(
            path=filepath,
            media_type="video/mp4",
            filename=f"{clean_title}.mp4"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
