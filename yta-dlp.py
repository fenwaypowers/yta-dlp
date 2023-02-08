import requests
import subprocess
import validators
import sys
import os, shutil
from mutagen.oggopus import OggOpus
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, ID3NoHeaderError
from html.parser import HTMLParser
from html.entities import name2codepoint
from ytmusicapi import YTMusic

yt = YTMusic()

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
    print('''
Welcome to yta-dlp beta 0.3!
    
To run, you can simply execute `python3 yta-dlp.py`.

You must supply a playlist link to an album from youtube music.

Example Use:
`python3 yta-dlp.py https://music.youtube.com/playlist?list=OLAK5uy_n0vSV9smWbw8O4q_rHkjWWoE5yshlPJU4`
''')
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

ytdlpcommand = ["yt-dlp", "--extract-audio", "-o", temp_dir + "/%(playlist_index)s. %(title)s [%(id)s].ogg", link]

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
