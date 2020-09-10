from asyncio import get_event_loop

import youtube_dl
from discord import PCMVolumeTransformer, FFmpegPCMAudio

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''


class DurationError(Exception):
    """Raised when audio file duration is too long."""
    def __init__(self, message="Audio file was too long to download"):
        super().__init__(message)


ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(PCMVolumeTransformer):
    """Make a player object"""
    def __init__(self, source, *, data, volume=0.1):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

    @classmethod
    async def get_info(cls, url):
        info = ytdl.extract_info(url, download=False)
        if 'entries' in info:
            return info['entries'][0]
        elif 'duration' in info:
            return info
        else:
            return {'duration': 0, 'webpage_url': 'Never Gonna Give You Up'}
