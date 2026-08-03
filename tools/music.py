import webbrowser
import urllib.parse
import musicLibrary


def play_song(song):

    song = song.lower().strip()

    # First check local library
    link = musicLibrary.music.get(song)

    if link:
        webbrowser.open(link)
        print("Playing from library:", song)
        return

    # Otherwise search YouTube
    print("Song not in library. Searching YouTube...")

    query = urllib.parse.quote(song)

    webbrowser.open(
        f"https://www.youtube.com/results?search_query={query}"
    )