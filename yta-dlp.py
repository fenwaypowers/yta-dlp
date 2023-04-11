import subprocess
import os
from mutagen.oggopus import OggOpus
from mutagen.flac import Picture
from mutagen.aac import AAC
from mutagen import File
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, ID3NoHeaderError
from html.parser import HTMLParser
from html.entities import name2codepoint
from ytmusicapi import YTMusic
import validators
import yt_dlp

from pydub import AudioSegment


import urllib.request
import os, shutil, argparse, logging, sys, subprocess, requests
from zipfile import ZipFile

logging.basicConfig(format='%(message)s', stream=sys.stdout, level=logging.INFO)

def main():
    global mode
    global link
    global temp_dir
    global yt
    global format

    yt = YTMusic()

    temp_dir = "yta-dlp-temp"
    
    parser = argparse.ArgumentParser(description='Download Albums from Youtube with metadata.')
    parser.add_argument('--link', help='Youtube Music link for an album or a song.', default=None)
    parser.add_argument(
        '--manual', help='Input the metadata for the album manually. Not implemented', action='store_true')
    parser.add_argument(
        '--resume', help='If there was a previous error, but your content was downloaded, you can resume the metadata process. Not implemented.', action='store_true')

    args = parser.parse_args()

    link = args.link
    format = "opus"
    
    if (os.path.isdir(temp_dir)) == False:
        os.mkdir(temp_dir)

    album_data = search_album()

    download_cover(album_data)

    album_metadata = get_album_metadata(album_data)

    with open("album_metadata.txt", "w") as myfile:
        myfile.write(str(album_metadata))

    link = album_metadata['audioPlaylistId']


    print(link)

    download(link, format)

    apply_metadata(album_metadata)

    '''
    album_list, metadata_dict = fetch_metadata()

    album_name = choose_album(album_list)

    global_metadata = gather_global_data(album_name, metadata_dict)

    print(global_metadata)
    '''

def search_album():
    while(True):
        search_term = input("Search (q to exit): ")

        if search_term == "q":
            sys_exit(0)

        search = yt.search(search_term, filter="albums", limit=10)

        albums_list = []
        album_data_list = []

        for i in search:
            if i["resultType"] == "album" and (i["category"] == "Albums" or i["category"] == "Top result"):

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

    with open("test_data2.txt", "w") as myfile:
        myfile.write(str(album_data))

    return album_data

def download_cover(album_data: str):
    try:
        num_imgs = len(album_data['thumbnails'])
        filename = temp_dir + "/" + "folder.jpg"
        urllib.request.urlretrieve(
            album_data['thumbnails'][num_imgs - 1]['url'], filename)
    except:
        print("Failed to download album cover.")

def get_album_metadata(album_data : str):

    print(album_data)

    data = yt.get_album(album_data['browseId'])
    return data

    #print("fail")
    #sys_exit(1)

def download(url : str, format : str):
    format_ids = {"opus" : "251",
                  "ogg" : "251",
                  "webm" : "251",
                  "aac" : "140",
                  "m4a" : "140",
                  "mp4" : "140"}

    if format not in format_ids:
        sys_exit(1)

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
            song_path = temp_dir + "/" + song

            if song.endswith("]"):
                os.rename(song_path, song_path + "." + format)
            if song.endswith(".opus"):
                os.rename(song_path, song_path.split(".opus")[0] + ".ogg")
    
    except:
        sys_exit(1)

def apply_metadata(album_metadata):
    tracks = album_metadata['tracks']

    for i in range(0, len(tracks)):

        file_startswith_val = str(i+1) + "."

        for file in os.listdir(temp_dir):
            if file.startswith(file_startswith_val) or file.startswith("0" + file_startswith_val):
                if format == "aac":
                    f = AAC(temp_dir + "/" + file)
                else:
                    f = OggOpus(temp_dir + "/" + file)

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

def fetch_metadata():

    metadata_dict = {}
    album_list = {}

    print("Getting metadata...")

    for file in os.listdir(temp_dir):

        id = parse_id(file)

        data = yt.search(id)

        '''
        try:
            print(data[0]['videoId'])
        except:
            print("no data found")
        '''

        try:
            album_name = data[0]["album"]["name"]
            if album_name in album_list:
                album_list[album_name] += 1
            else:
                album_list[album_name] = 1
        except:
            pass

        metadata_dict[id] = data

    print(album_list)

    return album_list, metadata_dict

def choose_album(album_list: dict):
    print_list = []
    for i in album_list:
        print(i)
        print_list.append(i)

    return select(print_list, "Albums")
    
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

    print("Selection made: " + inputlist[selection])
    return selection

def gather_global_data(album_name: str, metadata_dict: dict):
    year_list = []
    artists_list = []

    album_data = ""

    for i in metadata_dict:
        data = metadata_dict[i]

        try:
            if data[0]["album"]["name"] == album_name:
                album_data = yt.get_album(data[0]['album']['id'])
                print(data[0]['album']['id'])

                album_year = album_data['year']
                if album_year not in year_list:
                    year_list.append(album_year)

                artist_name = ""
                for j in range(0, len(data[0]["artists"])-1):
                    artist_name += data[0]["artists"][j]["name"] + ", "
                artist_name += data[0]["artists"][len(data[0]["artists"])-1]["name"]

                if artist_name not in artists_list:
                    artists_list.append(artist_name)
        except:
            pass

    year = select(year_list)
    artist = select(artists_list)

    return {"album_name" : album_name,
            "album_year" : year,
            "album_artist" : artist}

def sys_exit(code: int):
    '''
    for file in os.listdir(temp_dir):
        os.remove(temp_dir + "/" + file)

    os.rmdir(temp_dir)
    '''

    sys.exit(code)

'''


yt = YTMusic("oauth.json")

ver = "b0.3"

temp_dir = ".yta-dlp-temp"

if (os.path.isdir(temp_dir)):
    for file in os.listdir(temp_dir):
        os.remove(temp_dir + "/" + file)

if (os.path.isdir(temp_dir)) == False:
    os.mkdir(temp_dir)

def title_from_filename(instr:str):
    return_string = ""
    insplit = instr.split(". ")
    for i in range(1, len(insplit)):
        if i < 2:
            return_string += insplit[i]
        else:
            return_string += ". " + insplit[i]
    return return_string.split("[")[0]


def sys_exit():
    for file in os.listdir(temp_dir):
        os.remove(temp_dir + "/" + file)

    os.rmdir(temp_dir)

    sys.exit(0)


def toValidFileName(input: str):
    input_split = []
    output_dir = input
    for char in ["<", ">", ":", "\"", "/", "\\", "|", "?", "*"]:
        if char in output_dir:
            dir_split = output_dir.split(char)
            output_dir = ""
            for x in dir_split:
                output_dir += x
    return output_dir


def help_message():
    print(
Welcome to yta-dlp beta 0.3!
    
To run, you can simply execute `python3 yta-dlp.py`.

You must supply a playlist link to an album from youtube music.

Example Use:
`python3 yta-dlp.py https://music.youtube.com/playlist?list=OLAK5uy_n0vSV9smWbw8O4q_rHkjWWoE5yshlPJU4`
)
    sys_exit()

mode = "stream"
link = ""

if len(sys.argv) > 1:
    for j in range(1, len(sys.argv)):
        if "." in sys.argv[j]:
            testlink = ""

            if "http://" in sys.argv[j]:
                testlink += "https://" + sys.argv[j][7:]
            elif "https://" not in sys.argv[j]:
                testlink += "https://" + sys.argv[j]
            else:
                testlink += sys.argv[j]

            if validators.url(testlink) and "youtu" in testlink:
                if "&feature=share" in testlink:
                    testlink = testlink.split("&feature=share")[0]
                link = testlink
                search = False
            else:
                print(testlink)
                print("Error! Invalid link provided.")
                sys_exit()
        for m in ["-h", "h", "help", "-help"]:
            if m == sys.argv[j]:
                help_message()
else:
    help_message()

ytdlpcommand = ["yt-dlp", "--extract-audio", "--embed-thumbnail", "-o", temp_dir + "/%(playlist_index)s. %(title)s [%(id)s].ogg", link]

#print(ytdlpcommand)
subprocess.run(ytdlpcommand)

print()

name = ""
folder = temp_dir
data = []
continue_ = True
album_name = "album_name"
artist_name = "artist_name"
artists_list = []

for i in os.listdir(folder):

    continue_ = True

    print(i)

    old_data = data

    data = yt.search(i[-17:-6])

    print("--------------------------------------------------------------------")

    if len(data) == 0:
        print("Song with id " + i[-17:-6] + " will not have metadata generated right now. Sorry about that...\nWill try to retrieve metadata for it later.")
        continue_ = False
    else:
        if data[0]['videoId'] != i[-17:-6]:
            print("ERROR: Innacurate search for song with id " +
                    i[-17:-6] + ", instead got video of id " + data[0]['videoId'] + ".")
            if old_data != []:
                print("Working around this by using the previous song's metadata.")
                data = old_data
                data[0]["title"] = title_from_filename(i)
            else:
                print("Song with id " +
                        i[-17:-6] + " will not have metadata generated right now. Sorry about that...\nWill try to retrieve metadata for it later.")
                continue_ = False
        else:
            print("Valid metadata found!")
    print("--------------------------------------------------------------------")

    if continue_:

        album_data = yt.get_album(data[0]['album']['id'])

        song_date = album_data['year']
        track_num = str(int(i.split(".")[0]))
        album_name = data[0]["album"]["name"]
        song_name = data[0]["title"]

        artist_name = ""
        for j in range(0, len(data[0]["artists"])-1):
            artist_name += data[0]["artists"][j]["name"] + ", "
        artist_name += data[0]["artists"][len(data[0]["artists"])-1]["name"]

        if artist_name not in artists_list:
            artists_list.append(artist_name)

        f = OggOpus(folder + "/" + i)
        f["title"] = song_name
        f["album"] = album_name
        f["artist"] = artist_name
        f["tracknumber"] = track_num
        f["albumartist"] = artist_name
        f["date"] = song_date
        f.save()

    print()

if len(artists_list) == 2:
    artist_name = artists_list[0] + " and " + artists_list[1]
elif len(artists_list) > 2:
    artist_name = "Various Artists"

destination = toValidFileName(artist_name + " - " + album_name)

if (os.path.isdir(destination)) == False:
    os.mkdir(destination)

for song in os.listdir(folder):
    src = os.path.join(folder, song)
    dst = os.path.join(destination, song)
    shutil.move(src, dst)

album_list = []
date_list = []

for j in os.listdir(destination):
    fileopen = OggOpus(destination + "/" + j)
    fileopen["albumartist"] = artist_name

    if "album" in fileopen:
        if fileopen["album"][0] not in album_list:
            album_list.append(fileopen["album"][0])
    
    if "date" in fileopen:
        if fileopen["date"][0] not in date_list:
            date_list.append(fileopen["date"][0])

    if "title" not in fileopen:
        song_name = title_from_filename(j)
        fileopen["title"] = song_name
    
    if "artist" not in fileopen:
        fileopen["artist"] = artist_name
    
    if "tracknumber" not in fileopen:
        fileopen["tracknumber"] = str(int(j.split(".")[0]))
        

    fileopen.save()

if len(album_list) > 1:
    print("ERROR: Have multiple entries for album name! Using the first one in the list.")

if (len(date_list)) > 1:
    print("ERROR: Have multiple entries for album date! Using the first one in the list.")

for j in os.listdir(destination):
    fileopen = OggOpus(destination + "/" + j)
    fileopen["albumartist"] = artist_name

    if len(album_list) > 0:
        fileopen["album"] = album_list[0]

    if len(date_list) > 0:
        fileopen["date"] = date_list[0]

    fileopen.save()

sys_exit()
'''

if __name__ == "__main__":
    main()
