import urllib.request
import os
import shutil
import argparse
import logging
import sys
import yt_dlp
import string
import tempfile
from mutagen.oggopus import OggOpus
from mutagen.aac import AAC
from ytmusicapi import YTMusic

logging.basicConfig(format='%(message)s', stream=sys.stdout, level=logging.INFO)

def main():
    global mode
    global link
    global temp_dir
    global yt
    global format
    global extension
    global output_dir

    yt = YTMusic()

    temp_dir = tempfile.mkdtemp()
    
    parser = argparse.ArgumentParser(description='Download Albums from Youtube with metadata.')
    parser.add_argument('-o', '--output-path', help="specify a path where you want your files to go.", default="")
    parser.add_argument('-e', '--extension', help="specify the output extension of the files.", choices = ["ogg", "opus"], default="ogg")

    args = parser.parse_args()

    format = "opus"
    output_dir = os.path.abspath(args.output_path)  # Convert to an absolute path

    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    extension = args.extension

    album_data = search_album()

    download_cover(album_data)

    album_metadata = get_album_metadata(album_data)

    link = album_metadata['audioPlaylistId']

    download(link, format)

    apply_metadata(album_metadata)

    finish(album_metadata)

def search_album():
    while(True):
        search_term = input("Search (q to exit): ")

        if search_term == "q":
            sys_exit(0)

        search = yt.search(search_term, filter="albums")

        albums_list = []
        album_data_list = []

        for i in search:
            if i["resultType"] == "album" and i["category"] == "Albums":

                temp_album = "album unknown"
                temp_artist = "artist unknown"
                temp_type = "Album"
                temp_year = "year unknown"
                
                try:
                    temp_album = i['title']
                    temp_type = i["artists"][0]["name"]
                    temp_artist = i["artists"][1]["name"]
                    temp_year = i['year']

                except:
                    pass
                
                albums_list.append(f'{temp_album} [{temp_type}], {temp_artist}, {temp_year}')
                album_data_list.append(i)

        album_selected = select(albums_list, "Albums")

        if album_selected != "q":
            break

    album_data = album_data_list[album_selected]

    return album_data

def download_cover(album_data: str):
    try:
        num_imgs = len(album_data['thumbnails'])
        filename = os.path.join(temp_dir, "folder.jpg")
        urllib.request.urlretrieve(
            album_data['thumbnails'][num_imgs - 1]['url'], filename)
    except:
        logging.info("Failed to download album cover.")

def get_album_metadata(album_data : str):

    data = yt.get_album(album_data['browseId'])
    return data

def download(url : str, format : str):
    format_ids = {"opus" : "251",
                  "ogg" : "251",
                  "webm" : "251",
                  "aac" : "140",
                  "m4a" : "140",
                  "mp4" : "140"}

    if format not in format_ids:
        sys_exit(1, f"Cannot account for format: {format}")

    ydl_opts = {
        'format': format_ids[format],
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
        }, {
            'key': 'EmbedThumbnail'
        }],
        'outtmpl': temp_dir + '/%(playlist_index)s. %(title)s [%(id)s]'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if format_ids[format] == "140":
            format = "m4a"

        for song in os.listdir(temp_dir):
            song_path = os.path.join(temp_dir, song)
            

            if song.endswith("]"):
                os.rename(song_path, song_path + "." + format)
            if song.endswith(".opus"):
                os.rename(song_path, song_path.split("opus")[0] + extension)
    
    except:
        sys_exit(1, f"Problem occured downloading from url: {url}")

def apply_metadata(album_metadata):
    tracks = album_metadata['tracks']

    for i in range(0, len(tracks)):

        file_startswith_val = str(i+1) + "."

        for file in os.listdir(temp_dir):
            if file.startswith(file_startswith_val) or file.startswith("0" + file_startswith_val):
                if format == "aac":
                    f = AAC(os.path.join(temp_dir, file))
                else:
                    f = OggOpus(os.path.join(temp_dir, file))

                f["title"] = tracks[i]['title']
                f["album"] = tracks[i]['album']
                f["artist"] = artists_name(tracks[i]['artists'], purpose="song")
                f["tracknumber"] = str(i + 1)
                f["albumartist"] = artists_name(tracks[i]['artists'])
                f["date"] = album_metadata['year']
                f.save()

def artists_name(input_artists: list, purpose="album"):
    if len(input_artists) == 1:
        return input_artists[0]['name']

    if purpose == "album":
        if len(input_artists) > 2:
            return "Various Artists"
        else:
            return input_artists[0]['name'] + ", " + input_artists[1]['name']
    else:
        names = []
        for artist in input_artists:
            names.append(artist['name'])
        return ", ".join(names[:-1]) + " & " + names[-1]

def select(inputlist : list, selectiontype: str):
    for j, name in enumerate(inputlist):
        print(f"[{j + 1}] {name}")

    while (True):
        selection = input(f"Make a selection of {selectiontype} [1-{len(inputlist)}] (q to exit): ")

        if selection.isdigit():
            if int(selection) in range(1, len(inputlist) + 1):
                break
        
        if selection == "q":
            break

    if selection == "q":
        return selection

    selection = int(selection) - 1

    logging.info("Selection made: " + inputlist[selection])
    return selection

def finish(album_metadata):
    output_folder = artists_name(album_metadata['artists']) + " - " + album_metadata['title'] + " (" + album_metadata['year'] + ")"
    output_folder = sanitize_filename(output_folder)

    if not os.path.exists(os.path.join(output_dir, output_folder)):
        os.mkdir(os.path.join(output_dir, output_folder))

    for i in os.listdir(temp_dir):
        shutil.copy(os.path.join(temp_dir, i), os.path.join(output_dir, output_folder, i))

    for file in os.listdir(temp_dir):
        os.remove(os.path.join(temp_dir, file))
    os.rmdir(temp_dir)

def sanitize_filename(filename):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    cleaned_filename = ''.join(c for c in filename if c in valid_chars)
    return cleaned_filename

def sys_exit(code: int, message=""):
    if message != "":
        logging.info(message)
    sys.exit(code)

if __name__ == "__main__":
    main()
