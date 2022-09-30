# -*- coding: utf-8 -*-
import requests
import json
import os
import shutil
import time
from tinytag import TinyTag
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TRCK, TALB, TYER, TCON, TPE2, TPA

""" Normalise (normalize) unicode data in Python to remove umlauts, accents etc. """
import unicodedata


# ID3 info:
# APIC: Cover Art
# TIT2: Title
# TPE1: Artist
# TRCK: Track Number
# TALB: Album
# USLT: Lyrics
# TCON: Genre
# TPA: Disc Number


def album_folder_creator(current_directory, album, file, songs_directory):
    current_directory = current_directory + '/' + album  # changes current directory to the album name
    os.mkdir(current_directory)  # creates the album folder
    os.chdir(current_directory)  # changes into the album folder
    shutil.copy(songs_directory + '/' + file, current_directory)  # copies the song into the album folder
    return "Success!"


def cover_image_fetcher(album_cover_url, album_tag):
    image_url = album_cover_url
    data_image = requests.get(image_url, stream=True)
    album_tag_filtered = album_tag.replace(':', ' -')  # replacing special characters and instances
    album_tag_filtered = album_tag_filtered.replace('(', '-').replace(')', '') \
        .replace('[', '-').replace(']', '') \
        .replace('\'', '').replace(' ', '').lower()
    if '?' in album_tag_filtered:
        album_tag_filtered = album_tag_filtered.replace('?', '')
    local_file = open(f'{album_tag_filtered}.jpg', 'wb')
    data_image.raw.decode_content = True
    shutil.copyfileobj(data_image.raw, local_file)
    del data_image
    if local_file:
        return local_file
    else:
        return 'not found'


def song_sorter():
    # set directories for songs to sort and where to put them
    songs_directory = os.getcwd()
    artists_directory = os.getcwd() + '/' + 'Songs'

    # characters to filter for file/folder names
    special_characters = ['/', '*', '?', '<', '>', '|']

    if not os.path.isdir(artists_directory):  # if Songs folder doesn't exist, create it
        os.mkdir(artists_directory)

    start = time.time()
    for file in os.listdir(songs_directory):
        if '.mp3' in file:
            artist_found = 0  # set artist_found and album_found to 0 for validation when creating these folders
            album_found = 0  # if they were already created, these values will change to 1
            tags = TinyTag.get(songs_directory + '/' + file)
            if tags.album is not None and tags.albumartist is not None:  # if the song read has valid tags
                artist = tags.albumartist
                album = tags.album
                album = album.replace(':', ' -')
                for character in special_characters:
                    if character in album:
                        album = album.replace(character, '')
                year = tags.year
                for artist_folder in os.listdir(artists_directory):
                    if artist_folder.lower() == artist.lower():  # if there is a corresponding artist name to a folder
                        artist_found = 1  # changes this value to 1 so that it will not try to create another folder
                        current_directory = artists_directory + '/' + artist_folder
                        os.chdir(current_directory)  # changes into the current artist folder
                        for album_folder in os.listdir(current_directory):  # tries to read any existing album folders
                            if album_folder.lower() == (album + " " + "(" + year[0:4] + ")").lower():
                                album_found = 1  # sets this value to 1 so that it will not create another folder
                                album += " " + "(" + year[0:4] + ")"
                                current_directory = current_directory + '/' + album
                                os.chdir(current_directory)
                                shutil.copy(songs_directory + '/' +
                                            file, current_directory)
                        if album_found == 0:  # if it wasn't found it will create it
                            album += " " + "(" + year[0:4] + ")"
                            album_folder_creator(
                                current_directory, album, file, songs_directory)
                if artist_found == 0:  # if the artist wasn't found it will create its folder and the album folder
                    current_directory = artists_directory + '/' + artist
                    os.mkdir(current_directory)
                    os.chdir(current_directory)
                    album += " " + "(" + year[0:4] + ")"
                    album_folder_creator(
                        current_directory, album, file, songs_directory)
            else:
                print("Song didn't have valid meta-tags.")
                continue
    end = time.time()
    print(end - start, "Seconds")


def tags_scraper_remastered(music_list, directory):
    automated = False  # automates the process and if various artists are detected, it will apply it to the album artist
    headers = {"Accept-Language": "en-US,en;q=0.5"}  # set these headers to english because of the music genres

    for audio_file in music_list:
        # characters to filter for file/folder names
        special_characters = ['/', '*', '?', '<', '>', '|']

        track_contributors = []
        album_contributors = []
        various_artists = 0
        results = []
        final_result = {}
        genres = []
        genres_for_tag = ''
        feat_album_tag = ''
        final_feat_album_tag = ''
        current_result = {}
        # get the artist and title names to put in url
        print("AUDIO FILE: ", audio_file)
        audio = os.path.basename(audio_file).split(' - ', 1)  # splits the filename into 2 (artist - song)
        print("AUDIO: ", audio)
        artist_for_check = audio[0].strip()  # artist
        print("ARTIST FOR CHECK: ", artist_for_check.upper())  # convert to uppercase for easier comparisons
        artist_for_url = audio[0].strip().replace(' ', '-').lower()  # converts to lowercase for the url request
        if '&' in artist_for_url:  # if there are more than 2 artists, split them into two and use one for validation
            artist_for_url = artist_for_url.replace('&', '-')
            artist_for_check = artist_for_check.split('&')
            artist_for_check = artist_for_check[0]
        artist_for_url = unicodedata.normalize(
            'NFKD', artist_for_url).encode('ASCII', 'ignore').decode()
        print(artist_for_url, " trying to get data")
        title_for_check = audio[1][:-4]  # removes the .mp3 from the filename
        print(title_for_check.upper())
        title_for_url = audio[1][:-4].strip(
            '- ').replace(' ', '-').lower()
        title_for_url = title_for_url.replace('\'', '')
        if '.' in title_for_url:
            title_for_url = title_for_url.replace('.', '')
        title_for_url = unicodedata.normalize(
            'NFKD', title_for_url).encode('ASCII', 'ignore').decode()
        print(title_for_url, " trying to get data")

        response_search = requests.request("GET", f"https://api.deezer.com/search?q={artist_for_url}-{title_for_url}",
                                           headers=headers)  # this seems like the most efficient way
        parse_json = json.loads(response_search.text)

        for n, result in enumerate(parse_json['data']):  # for index and result in the data we just requested
            if artist_for_check.upper() in result['artist']['name'].upper() \
                    and title_for_check.upper() in result['title'].upper() \
                    and 'acoustic' not in result['title'].lower() \
                    and 'live' not in result['title'].lower() \
                    and 'bonus' not in result['title'].lower():  # checks for artist, title and filters unwanted results
                current_result['id'] = result['id']  # song id
                current_result['artist'] = result['artist']['name']  # artist name
                current_result['title'] = result['title']  # song name
                current_result['album_title'] = result['album']['title']  # album name
                current_result['cover_url_medium'] = result['album']['cover_medium']  # cover 250x250
                current_result['cover_url_big'] = result['album']['cover_big']  # cover 500x500
                current_result['cover_url_xl'] = result['album']['cover_xl']  # cover 1000x1000
                current_result['album_id'] = result['album']['id']  # album id
                current_result['title_contributors'] = ''  # creates this to add to at a later time
                results.append(current_result)  # adds all the results to a list so that we can choose the one we want
                current_result = {}

        number_results = len(results)  # calculates the number of results for later
        user_choice = 0  # setting user_choice to 0 so that we can then change it to whatever the user chooses
        total_songs_for_user_choice = 0
        for n, result in enumerate(results):
            if n + 1 < 10:
                print("VERSION: ", n + 1, result)  # shows the results up to 10 in total so that the user can pick one
                total_songs_for_user_choice += 1
            else:
                break

        if automated:
            if number_results > 1:
                if results[0]['title'] == results[0]['album_title']:
                    final_result = results[1]
                elif results[1]['title'] == results[1]['album_title']:
                    final_result = results[0]
                else:
                    final_result = results[0]
            elif number_results == 1:
                final_result = results[0]
            else:
                print("There were no records found.")
                continue  # this code automates the process while trying to avoid singles, not perfect

        elif not automated:
            if number_results > 1:  # if there are multiple results, let the user pick one
                while user_choice <= 0 or user_choice > total_songs_for_user_choice:
                    user_choice = int(input(f"Which version? [1-{total_songs_for_user_choice}]: "))
                    if user_choice <= 0 or user_choice > total_songs_for_user_choice:
                        print("Invalid choice, try again.")
                    else:
                        final_result = results[user_choice - 1]
            elif number_results == 1:  # if not just use the one we got
                final_result = results[0]
            else:
                print("There were no results found.")
                continue

        if not final_result:
            break

        if final_result['artist'] == 'Ghostemane':  # ghostemane is written capitalized in the deezer db
            final_result['artist'] = 'GHOSTEMANE'

        # requests the track data to check the artists
        response_track = requests.request("GET", f"https://api.deezer.com/track/{final_result['id']}", headers=headers)
        parse_json_track = json.loads(response_track.text)
        for contributor in parse_json_track['contributors']:
            track_contributors.append(contributor['name'])  # adds every artist to a list
        final_contributors = []
        if len(track_contributors) > 1:  # if there is more than one artist
            # added this feature due to personal taste, since I want some songs to have all artists in the artist tag
            if '&' in audio[0].strip():  # first check if the artist was already present in the filename
                final_result['artist'] = ''
                for contributor in track_contributors:
                    final_result['artist'] += contributor + ' & '
                final_result['artist'] = final_result['artist'][:-3]
            else:  # if the artist wasn't in the filename
                for contributor in track_contributors:
                    # check if the artist is present in the song name to avoid repeating it
                    if contributor.lower() not in final_result['artist'].lower() \
                            and contributor.lower() not in final_result['title'].lower():
                        final_contributors.append(contributor)
                print("FINAL CONTRIBUTORS: ", final_contributors)
                if len(final_contributors) == 1:  # if there's only one extra artist
                    if 'feat.' not in final_result['title'].lower():  # check if it's already present in the song name
                        final_result['title_contributors'] = final_result['title'] + \
                                                             f' (feat. {final_contributors[0]}' + ')'
                    else:  # if it's not present then add it and change the string to match it
                        final_result['title_contributors'] = final_result['title'][:-1] + \
                                                             ' & ' + final_contributors[0] + ')'
                elif len(final_contributors) > 1:  # if there's more than 1 extra artist
                    final_result['title_contributors'] = final_result['title'] + f' (feat. '
                    for contributor in final_contributors:
                        final_result['title_contributors'] += f'{contributor}' + ' & '  # prepare the string to add
                    final_result['title_contributors'] = final_result['title_contributors'][:-3] + ')'  # add artists
        print("FINAL RESULT TITLE CONTRIBUTORS: ", final_result['title_contributors'])

        # request data from the album to count the number of tracks and to see if it's from various artists or just one
        response_album = requests.request("GET", f"https://api.deezer.com/album/{final_result['album_id']}",
                                          headers=headers)
        parse_json_album = json.loads(response_album.text)
        album_tracks = parse_json_album['tracks']
        track_count = len(album_tracks['data'])  # count the number of tracks on the album
        album_genres = parse_json_album['genres']['data']
        for contributor in parse_json_album['contributors']:
            album_contributors.append(contributor['name'])  # add the album artists to a list
        if 'Various Artists' in album_contributors:  # check if Various Artists is in the list
            print("VARIOUS ARTISTS DETECTED")
            # ask if user wants to set the album artist tag to Various Artists or not
            if automated:
                various_artists = 1
            elif not automated:
                while True:
                    various_artists = input("Do you want to put Album Artist as Various Artists? (Yes = 1 / No = 0): ")
                    if various_artists != "1" and various_artists != "0":
                        print("Please input a valid option.")
                    else:
                        various_artists = int(various_artists)
                        break
        release_date = parse_json_album['release_date'][:4]  # choose the year of the release date

        # check if album title has feat. artists in it, so that the folder won't have them
        if 'feat.' in final_result['album_title']:
            feat_album_tag = final_result['album_title'].replace(')', '(')
            feat_album_tag = feat_album_tag.split('(')
            print("FINAL_FEAT_ALBUM_TAG_BEFORE_REPLACE: ", feat_album_tag)
            # print(feat_album_tag[0])
            # print(feat_album_tag[:-1])
            feat_album_tag_first = feat_album_tag[0]  # this removes the last blank space
            final_feat_album_tag = str(feat_album_tag_first[0:-1] + feat_album_tag.pop())
            print("FINAL FEAT. ALBUM TAG: ", final_feat_album_tag)

        # get the number of the track on the album
        for n, s in enumerate(album_tracks['data']):
            print(n + 1, s)  # show the user the track and corresponding number
            if title_for_check.upper() in s['title'].upper():  # if it finds the song, use the track number
                print("FINAL: ", s['title'])
                final_result['track_number'] = n + 1
                break
        final_result['total_tracks'] = track_count  # add total track count to the object

        if final_result['title'] == final_result['album_title'] and final_result['total_tracks'] == 1:
            final_result['album_title'] += ' - Single'  # if title and album are the same and the album only has 1 song

        for n, genre in enumerate(album_genres):  # change formatting on some genres, personal taste
            if album_genres[n]['name'] == 'Rap/Hip Hop':
                album_genres[n]['name'] = 'Hip-Hop/Rap'
            if album_genres[n]['name'] == 'Pop Indie':
                album_genres[n]['name'] = 'Indie Pop'
            genres.append(album_genres[n]['name'])  # add them all to a list

        length_genres = len(genres)  # get the number of genres
        print("NUMBER OF GENRES: ", length_genres)
        if length_genres > 1:  # if it has more than 1 genre
            for genre in genres:
                genres_for_tag = genres_for_tag + genre + '/'  # put them all together i.e: rock/pop/rap
            genres_for_tag = genres_for_tag[:-1]
        elif length_genres == 1:  # if it only has one genre use it
            genres_for_tag = genres[0]

        print("ALBUM_ID: ", final_result['album_id'])
        print("TRACK_ID: ", final_result['id'])
        print("TRACK: ", final_result['title'])
        print("ARTIST: ", final_result['artist'])
        print("ALBUM: ", final_result['album_title'])
        if not various_artists:
            print("ALBUM ARTIST: ", final_result['artist'])
        else:
            print("ALBUM ARTIST: ", 'Various Artists')
        print("TRACK NUMBER: ", final_result['track_number'])
        print("TRACKS: ", final_result['total_tracks'])
        print("GENRES: ", genres)
        print("GENRES FOR TAG: ", genres_for_tag)
        print("COVER_URL_XL: ", final_result['cover_url_xl'])
        print("RELEASE DATE: ", release_date)
        print("DISC_NUMBER: ", '1/1')

        # format the album tag to remove special characters (for the cover art file)
        album_tag = final_result['album_title']
        album_name_for_cover_art = album_tag.replace(' ', '')
        for character in special_characters:
            if character in album_tag:
                album_name_for_cover_art = album_tag.replace(character, '')

        print("ALBUM TAG: ", album_name_for_cover_art)

        if final_result['cover_url_xl']:  # check if the album has a 1000x1000 cover art picture
            cover_image_fetcher(final_result['cover_url_xl'], album_name_for_cover_art)
        elif final_result['cover_url_big']:  # same as above but for 500x500
            cover_image_fetcher(final_result['cover_url_big'], album_name_for_cover_art)
        else:
            cover_image_fetcher(final_result['cover_url_medium'], album_name_for_cover_art)  # use the 250x250

        pic_file = directory + '/' + album_name_for_cover_art.replace(':', ' -'). \
            replace('(', '-').replace(')', '') \
            .replace('[', '-').replace(']', '') \
            .replace('\'', '').replace(' ', '').lower() + '.jpg'
        for character in special_characters:
            if character in pic_file and character != '/':
                pic_file = pic_file.replace(character, '')
        print(pic_file, " AFTER REPLACE")

        file = MP3(directory + '/' + audio_file, ID3=ID3)  # open the file to change its tags
        file.tags.add(
            APIC(
                encoding=3,  # 3 is for utf-8
                mime='image/jpeg',  # image/png or image/jpeg
                type=3,  # 3 is for the cover art
                desc=u'Cover',
                data=open(pic_file, 'rb').read()
            )
        )
        if final_result['title_contributors']:  # if there are artists that need to be added to the title with feat.
            print("TEST: ", final_result['title_contributors'])
            file.tags.add(TIT2(encoding=3, text=final_result['title_contributors']))
        else:  # if not use the regular title
            file.tags.add(TIT2(encoding=3, text=final_result['title']))
        if final_feat_album_tag:  # if there's an album tag with multiple artists
            file.tags.add(TALB(encoding=3, text=final_feat_album_tag))
        else:
            file.tags.add(TALB(encoding=3, text=final_result['album_title']))
        file.tags.add(TPE1(encoding=3, text=final_result['artist']))
        if not various_artists:
            file.tags.add(TPE2(encoding=3, text=final_result['artist']))  # album artist without various artists
            print("TESTING VARIOUS ARTISTS")
        else:
            file.tags.add(TPE2(encoding=3, text='Various Artists'))  # album artist with various artists
        file.tags.add(TRCK(encoding=3, text=str(str(final_result['track_number']) + '/'
                                                + str(final_result['total_tracks']))))  # track number/total tracks
        file.tags.add(TYER(encoding=3, text=str(release_date)))  # year
        file.tags.add(TCON(encoding=3, text=genres_for_tag))  # genres
        file.tags.add(TPA(encoding=3, text='1/1'))  # disc number
        if 0 < int(final_result['track_number']) < 10:
            track_number_for_name = '0' + str(final_result['track_number'])  # prepend a 0 for the filename (6 -> 06)
        else:
            track_number_for_name = str(final_result['track_number'])
        file.save(v2_version=3)  # save the tags
        if final_result['title_contributors']:  # check if there were featured artists to update the success message
            print('Success!', final_result['artist'], " - ", final_result['title_contributors'])
            os.rename(directory + '/' + audio_file,
                      directory + '/' + track_number_for_name + ' ' + final_result['title_contributors'] + '.mp3')
        else:
            print('Success!', final_result['artist'], " - ", final_result['title'])
            os.rename(directory + '/' + audio_file,
                      directory + '/' + track_number_for_name + ' ' + final_result['title'] + '.mp3')
        time.sleep(2)  # 2s timeout to prevent flooding the api with requests


def main():
    # Songs Directory
    start = time.time()
    directory = os.getcwd()
    music_list = []

    for item in os.listdir(directory):
        if '.mp3' in item:
            music_list.append(item)
    if music_list:
        tags_scraper_remastered(music_list, directory)
    else:
        print('No musics found.')

    # sorting the songs after getting the tags
    try:
        song_sorter()
    # if it runs into an error, I just want to know which song caused it, so the Exception doesn't require specificity
    except Exception as err:
        print(err)
    end = time.time()
    print(f'Total time: {end} - {start}')


if __name__ == '__main__':
    main()
