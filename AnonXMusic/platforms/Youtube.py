import asyncio
import os
import re
from typing import Union
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython import VideosSearch  # ✅ FIXED
from AnonXMusic.utils.formatters import time_to_seconds
import aiohttp
from AnonXMusic import LOGGER

YOUR_API_URL = None
FALLBACK_API_URL = "https://shrutibots.site"


async def load_api_url():
    global YOUR_API_URL
    logger = LOGGER("Youtube.py")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://pastebin.com/raw/rLsBhAQa",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    YOUR_API_URL = (await response.text()).strip()
                    logger.info("API URL loaded successfully")
                else:
                    YOUR_API_URL = FALLBACK_API_URL
    except Exception:
        YOUR_API_URL = FALLBACK_API_URL


try:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.create_task(load_api_url())
    else:
        loop.run_until_complete(load_api_url())
except RuntimeError:
    pass


# ---------------- DOWNLOAD ---------------- #

async def download_song(link: str) -> str:
    global YOUR_API_URL

    if not YOUR_API_URL:
        await load_api_url()

    video_id = link.split("v=")[-1].split("&")[0] if "v=" in link else link
    if not video_id:
        return None

    os.makedirs("downloads", exist_ok=True)
    file_path = f"downloads/{video_id}.mp3"

    if os.path.exists(file_path):
        return file_path

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{YOUR_API_URL}/download",
                params={"url": video_id, "type": "audio"},
            ) as r:
                data = await r.json()
                token = data.get("download_token")
                if not token:
                    return None

            async with session.get(
                f"{YOUR_API_URL}/stream/{video_id}?type=audio",
                headers={"X-Download-Token": token},
            ) as r:
                with open(file_path, "wb") as f:
                    async for chunk in r.content.iter_chunked(1024):
                        f.write(chunk)

        return file_path
    except:
        return None


async def download_video(link: str) -> str:
    global YOUR_API_URL

    if not YOUR_API_URL:
        await load_api_url()

    video_id = link.split("v=")[-1].split("&")[0] if "v=" in link else link
    if not video_id:
        return None

    os.makedirs("downloads", exist_ok=True)
    file_path = f"downloads/{video_id}.mp4"

    if os.path.exists(file_path):
        return file_path

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{YOUR_API_URL}/download",
                params={"url": video_id, "type": "video"},
            ) as r:
                data = await r.json()
                token = data.get("download_token")
                if not token:
                    return None

            async with session.get(
                f"{YOUR_API_URL}/stream/{video_id}?type=video",
                headers={"X-Download-Token": token},
            ) as r:
                with open(file_path, "wb") as f:
                    async for chunk in r.content.iter_chunked(1024):
                        f.write(chunk)

        return file_path
    except:
        return None


# ---------------- MAIN CLASS ---------------- #

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message: Message):
        if message.entities:
            for e in message.entities:
                if e.type == MessageEntityType.URL:
                    return message.text[e.offset : e.offset + e.length]
        return None

    # -------- SEARCH FUNCTIONS -------- #

    async def details(self, link: str, videoid=False):
        if videoid:
            link = self.base + link

        data = VideosSearch(link, limit=1).result().get("result", [])
        if not data:
            return None, None, 0, None, None

        r = data[0]
        return (
            r["title"],
            r.get("duration"),
            int(time_to_seconds(r.get("duration"))) if r.get("duration") else 0,
            r["thumbnails"][0]["url"],
            r["id"],
        )

    async def title(self, link: str, videoid=False):
        data = VideosSearch(link, limit=1).result().get("result", [])
        return data[0]["title"] if data else None

    async def duration(self, link: str, videoid=False):
        data = VideosSearch(link, limit=1).result().get("result", [])
        return data[0].get("duration") if data else None

    async def thumbnail(self, link: str, videoid=False):
        data = VideosSearch(link, limit=1).result().get("result", [])
        return data[0]["thumbnails"][0]["url"] if data else None

    async def track(self, link: str, videoid=False):
        data = VideosSearch(link, limit=1).result().get("result", [])
        if not data:
            return None, None

        r = data[0]
        return {
            "title": r["title"],
            "link": r["link"],
            "vidid": r["id"],
            "duration_min": r.get("duration"),
            "thumb": r["thumbnails"][0]["url"],
        }, r["id"]

    async def slider(self, link: str, index: int, videoid=False):
        data = VideosSearch(link, limit=10).result().get("result", [])
        if len(data) <= index:
            return None, None, None, None

        r = data[index]
        return r["title"], r.get("duration"), r["thumbnails"][0]["url"], r["id"]

    # -------- DOWNLOAD -------- #

    async def download(self, link: str, mystic, video=False, videoid=False):
        if videoid:
            link = self.base + link

        file = await (download_video(link) if video else download_song(link))
        return (file, True) if file else (None, False)
