import requests


def call_musixmatch_api(service, params):
    base_url = "https://api.musixmatch.com/ws/1.1/"
    api_key = "&apikey=41da9710650383c323dc1f32dabd847d"
    format_url = "?format=json&callback=callback"

    api_call = base_url + service + format_url + params + api_key

    print("API Call: ", api_call)
    return requests.get(api_call)


def search_track(track_query):
    service = "track.search"
    params = "&q=" + track_query + \
             "&f_has_lyrics=1" + "&s_track_rating=desc"

    request = call_musixmatch_api(service, params)
    data = request.json()
    data = data['message']['body']

    track_list = [track['track'] for track in data['track_list']]
    # pprint(track_list)
    return track_list


def get_track(track_id):
    service = "track.get"
    params = "&track_id=" + track_id
    request = call_musixmatch_api(service, params)

    data = request.json()
    data = data['message']['body']
    return data['track']


def get_lyrics(track_id):
    service = "track.lyrics.get"
    params = "&track_id=" + track_id
    request = call_musixmatch_api(service, params)
    data = request.json()
    data = data['message']['body']
    lyrics = data['lyrics']['lyrics_body']
    print("Lyrics:", lyrics)
    return lyrics
