# Rends YouTube Extractor Service 🚀
Dedicated, self-hosted YouTube downloader service powered by **yt-dlp** and **FFmpeg** on Docker.

## Endpoints:
- `GET /` : Health check & service info
- `GET /youtube?url=<URL>` : Metadata & stream info
- `GET /download/audio?url=<URL>` : Download directly converted MP3 file
- `GET /download/video?url=<URL>` : Download directly merged MP4 file

## Deploy to Render:
1. Connect this GitHub repo to [Render.com](https://render.com).
2. Create a new **Web Service** with Docker environment.
3. Done!
