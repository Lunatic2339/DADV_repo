from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.add, name='home'),
    path('spotify/login', views.spotify_login, name='spotify_login'),
    path('spotify/callback', views.spotify_callback, name='spotify_callback'),
    path('playlists', views.get_playlists, name='get_playlists'),
    path('dashboard', views.dashboard_view, name='dashboard'),
    path('visuals', views.visuals_view, name='visuals'),
    path('visuals/popularity/', views.get_popularity_data, name='get_popularity_data'),
]
