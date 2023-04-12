# yta-dlp
Download albums in opus format from youtube with metadata.

## Prerequisites
* [Python 3](https://www.python.org/)
* [yt-dlp](https://github.com/yt-dlp/yt-dlp)
* [ytmusicapi](https://ytmusicapi.readthedocs.io/en/stable/)
* [mutagen](https://pypi.org/project/mutagen/)

## Getting Started

run `python3 -m pip install -r requirements.txt`

## Usage
To run, you can simply execute `python3 yta-dlp.py`.

Example Use:
`python3 yta-dlp.py -o path/to/albums -e opus`

## How It Works
* user searches for an album using ytmusicapi `search()`
* user selects an album, metdata of the album saved from ytmusicapi `get_album()`
* yt-dlp downloads the album, and then applies the metadata

## Known Errors
* Albums that are by "Various Artists" won't have correct metadata generated. The individual artists won't appear in the `artist` metadata field. This is because the only data I was able to get from ytmusicapi had "Various Artists" as the only artist.

## Future Features
I most likely won't continue to work on this program, considering that [RaduTek](https://github.com/RaduTek) has made [YTMusicDL](https://github.com/RaduTek/YTMusicDL). The features detailed below are already in their program. Therefore, I will likely only contribute to [YTMusicDL](https://github.com/RaduTek/YTMusicDL) from now on. 

* Support for other audio formats such as AAC
* Support for downloading individual songs with metadata
* Support for "Various Artists" albums