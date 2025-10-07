# Copyright (C) 2025 by Alexa_Help @ Github, < https://github.com/TheTeamAlexa >
# Subscribe On YT < Jankari Ki Duniya >. All rights reserved. © Alexa © Yukki.

"""
TheTeamAlexa is a project of Telegram bots with variety of purposes.
Copyright (c) 2021 ~ Present Team Alexa <https://github.com/TheTeamAlexa>

This program is free software: you can redistribute it and can modify
as you want or you can collabe if you have new ideas.
"""

import asyncio
import os
import re
import json
import aiohttp
from typing import Union

from pyrogram.enums import MessageEntityType
from pyrogram.types import Message

import config
from AlexaMusic.utils.formatters import time_to_seconds


def extract_video_id(url):
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/|v\/|youtu\.be\/)([0-9A-Za-z_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.api_key = config.CUSTOM_API_KEY
        self.api_base = config.CUSTOM_API_BASE_URL  # Your API base URL
        self.listbase = "https://youtube.com/playlist?list="

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        text = ""
        offset = None
        length = None
        for message in messages:
            if offset:
                break
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        offset, length = entity.offset, entity.length
                        break
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None if offset in (None,) else text[offset : offset + length]

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            video_id = link
        else:
            video_id = extract_video_id(link)
        
        async with aiohttp.ClientSession() as session:
            # Adjust endpoint and params for your API
            url = f"{self.api_base}/video-info"  # Your API endpoint
            headers = {'Authorization': f'Bearer {self.api_key}'}  # Your auth method
            params = {'video_id': video_id}  # Your API params
            
            async with session.get(url, params=params, headers=headers) as resp:
                data = await resp.json()
                
        # Adjust response parsing for your API format
        if not data.get('success'):
            return None, None, 0, None, None
            
        title = data['title']
        duration_sec = data['duration']
        thumbnail = data['thumbnail']
        duration_min = f"{duration_sec // 60}:{duration_sec % 60:02d}"
        
        return title, duration_min, duration_sec, thumbnail, video_id

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
        return title

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            duration = result["duration"]
        return duration

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        return thumbnail

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            video_id = link
        else:
            video_id = extract_video_id(link)
            
        async with aiohttp.ClientSession() as session:
            url = f"{self.api_base}/stream-url"  # Your streaming endpoint
            headers = {'Authorization': f'Bearer {self.api_key}'}
            params = {'video_id': video_id, 'quality': '720p'}
            
            async with session.get(url, params=params, headers=headers) as resp:
                data = await resp.json()
                
        if data.get('success'):
            return (1, data['stream_url'])  # Your API's streaming URL
        return (0, "Failed to get stream URL")

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            playlist_id = link
        else:
            playlist_id = re.search(r'list=([^&]+)', link)
            if playlist_id:
                playlist_id = playlist_id.group(1)
            else:
                return []
        
        async with aiohttp.ClientSession() as session:
            url = f"{self.api_base}/playlist"  # Your playlist endpoint
            headers = {'Authorization': f'Bearer {self.api_key}'}
            params = {
                'playlist_id': playlist_id,
                'limit': min(limit, 50)
            }
            async with session.get(url, params=params, headers=headers) as resp:
                data = await resp.json()
        
        result = []
        if data.get('videos'):
            for video in data['videos']:
                result.append(video['id'])  # Adjust field name for your API
        return result

    async def track(self, link: str, videoid: Union[bool, str] = None):
        title, duration_min, duration_sec, thumbnail, vidid = await self.details(link, videoid)
        if not title:
            return None, None
            
        yturl = self.base + vidid if videoid else link
        track_details = {
            "title": title,
            "link": yturl,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumbnail,
        }
        return track_details, vidid

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        # Return basic format info (API doesn't provide direct download URLs)
        formats_available = [
            {
                "format": "best",
                "filesize": None,
                "format_id": "best",
                "ext": "mp4",
                "format_note": "Best available",
                "yturl": link,
            }
        ]
        return formats_available, link

    async def slider(
        self,
        link: str,
        query_type: int,
        videoid: Union[bool, str] = None,
    ):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        a = VideosSearch(link, limit=10)
        result = (await a.next()).get("result")
        title = result[query_type]["title"]
        duration_min = result[query_type]["duration"]
        vidid = result[query_type]["id"]
        thumbnail = result[query_type]["thumbnails"][0]["url"].split("?")[0]
        return title, duration_min, thumbnail, vidid

    def _parse_duration(self, duration):
        """Convert ISO 8601 duration to seconds"""
        import re
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        if not match:
            return 0
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        return hours * 3600 + minutes * 60 + seconds

    async def download(self, link: str, mystic, **kwargs) -> str:
        if kwargs.get('videoid'):
            video_id = link
        else:
            video_id = extract_video_id(link)
            
        async with aiohttp.ClientSession() as session:
            url = f"{self.api_base}/download"  # Your download endpoint
            headers = {'Authorization': f'Bearer {self.api_key}'}
            params = {
                'video_id': video_id,
                'format': 'audio' if not kwargs.get('video') else 'video'
            }
            
            async with session.get(url, params=params, headers=headers) as resp:
                data = await resp.json()
                
        if data.get('success'):
            return data['download_url'], True  # Your API's download URL
        return None, False
