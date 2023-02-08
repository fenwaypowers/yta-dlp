# yta-dlp
Download albums in opus format from youtube with metadata.

Yes, I'm aware that this script is extremely scuffed. There are many issues with this script, and they will be talked about later in this README.
If you feel like the script can be improved, please fork this repository and improve it. I know it needs improving.

This was made for albums, not playlists.

## Prerequisites
* [Python 3](https://www.python.org/)
* [yt-dlp](https://github.com/yt-dlp/yt-dlp)
* [mutagen](https://pypi.org/project/mutagen/)
* [html.parser](https://docs.python.org/3/library/html.parser.html#module-html.parser)
* [ytmusicapi](https://ytmusicapi.readthedocs.io/en/stable/)

## Usage
To run, you can simply execute `python3 yta-dlp.py`.

You must supply a playlist link to an album from youtube music.

Example Use:
`python3 yta-dlp.py https://music.youtube.com/playlist?list=OLAK5uy_n0vSV9smWbw8O4q_rHkjWWoE5yshlPJU4`

## How it works
* yt-dlp downloads the album in a temporary folder in opus format.
* Each file is searched in ytmusicapi from its youtube id.
* If metadata is found, it is applied to the file.
* Sometimes ytmusicapi returns an incorrect search, and sometimes it won't even return a search.
* In these cases, metadata from the previous song will be used. The title of the song will be taken from the filename.
* If the first song has no metadata, it will get metadata later at the very end during the final check.
* If there are 2 artists on the album, they will both appear in the `album_artist` field.
* If there are more than 2 artists on the album, the `album_artist` field will be set to "Various Artists".

## Known errors
* For songs that have no metadata available, their `artist` field will automatically be set to whatever the `album_artist` field is. Yes, this means that albums with "Various Artists" as the `album_artist` could potentially have songs with "Various Artists" as their `artist` field. Just the way it is, unfortunately. you can always edit the metadata with a tool such as [mp3tag](https://www.mp3tag.de/en/).
* If you get this error : `mutagen.ogg.error: read b'\xff\xd8\xff\xe0', expected b'OggS', at 0x0`, just try again.
* Obviously if you put in anything other than a playlist link to an album, you will get wonky results. This was made for albums, not playlists.

## Future Features
DISCLAIMER: This program currently does pretty much everything I want it to, leaving me little reason to improve it. These features are things I would like but don't need. You will probably get these features faster if you implemenet them yourself. If a ton of people flock to this repo for some reason, then yeah sure I'll work on it again. I'll probably rewrite the entire thing in that case, since it is very spaghetti as of now.

* Support for other audio formats such as AAC
* Download image album (and also make it an option to put it in the metadata)
