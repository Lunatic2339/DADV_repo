import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import pprint

redirect_uri = 'https://127.0.0.1:8080/'

client_credentials_manager = SpotifyClientCredentials(client_id='50c1dce6e2ae4559ba7571df9e94890c', client_secret='b02e9181167f430b989e416978676178')
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

my_top_tracks = sp.current_user_top_tracks(limit=50, offset=0)
print(my_top_tracks['tracks'][0])

# artist_followers = []
# artist_id = []
# artist_popularity = []
# artist_genres = []
# artist_name = []
# artist_externalurls = []
# for i in range(0,50,10):
#     artist_results = sp.search(q="genre:j-pop", type="artist", limit=10, offset=i)
#     for i, t in enumerate(artist_results['artists']['items']):
#         artist_followers.append(t['followers']['total'])
#         artist_genres.append(t['genres'])
#         artist_id.append(t['id'])
#         artist_name.append(t['name'])
#         artist_popularity.append(t['popularity'])
#         artist_externalurls.append(t['external_urls']['spotify'])
        


# artist_df = pd.DataFrame({'artist_id': artist_id, 
#                            'artist_name': artist_name, 
#                            'artist_genres': artist_genres, 
#                            'artist_followers': artist_followers, 
#                            'artist_popularity': artist_popularity})

# artist_df = artist_df.assign(artist_externalurls = artist_externalurls)

# sample_artist_id = artist_df['artist_id'][0]
# sample_track_id = sp.artist_top_tracks(sample_artist_id, country='JP')['tracks'][0]['id']

# artist_top_tracks = {}
# for a_id in artist_df['artist_id']:
#     top_tracks = sp.artist_top_tracks(a_id, country='JP')
#     artist_top_tracks[a_id] = top_tracks['tracks']

# artist_top_tracks_features = {}




# print(track_df.head())

# track_df.to_excel(excel_writer='sample.xlsx')