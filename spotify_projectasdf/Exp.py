import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import pprint

client_credentials_manager = SpotifyClientCredentials(client_id='50c1dce6e2ae4559ba7571df9e94890c', client_secret='b02e9181167f430b989e416978676178')
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)


myartist = sp.artist('4QvgGvpgzgyUOo8Yp8LDm9')
pprint.pprint(myartist)