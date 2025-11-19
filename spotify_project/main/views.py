from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import login 
from django.contrib.auth.models import User # Django 기본 User 모델
from django.contrib.auth.decorators import login_required

from . import forms
from . import models
from . import spotify 
from .models import SpotifyToken, Track

from datetime import timedelta
import spotipy
from spotipy.oauth2 import SpotifyOAuth

from collections import Counter

# Create your views here.

def home_view(request):
    if request.method == "POST":
        form = forms.ArtistForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    if request.method == "GET":
        artists = models.Artist.objects.all()
        form = forms.ArtistForm()
        return render(request, "home.html", {"form": form, "artists": artists})
    else:
        return HttpResponse("Invalid request method.", status=400)

@login_required
def dashboard_view(request):
    django_user = request.user

    try:
        # 1. 유효한 Spotify 클라이언트 획득 (토큰 갱신 포함)
        token_obj = SpotifyToken.objects.get(user=django_user)
        spotify_user_id = token_obj.spotify_id
        sp = get_user_spotify_client(spotify_user_id)
        
        # 2. API 호출: 사용자 프로필 정보 및 Top 5 트랙 가져오기
        user_profile = sp.me() # 사용자 이름, 이미지 등에 필요

        top_tracks_data = sp.current_user_top_tracks(limit=50, time_range='medium_term')
        
        artist_ids = []
        for track in top_tracks_data['items']:
            # 각 트랙의 첫 번째 아티스트 ID만 추출
            artist_ids.append(track['artists'][0]['id'])

        # 아티스트 ID 리스트에서 중복을 제거합니다 (성능 최적화)
        unique_artist_ids = list(set(artist_ids))
        
        # 2. API 호출: 모든 아티스트의 상세 정보를 한 번에 요청
        # (API는 최대 50개의 ID를 한 번에 처리 가능)
        artists_data = sp.artists(unique_artist_ids)
        
        all_genres = []
        for artist in artists_data['artists']:
            # 각 아티스트의 장르 리스트를 모두 하나의 리스트에 추가
            all_genres.extend(artist['genres'])
            
        # 3. 장르 집계: Counter를 사용하여 각 장르의 빈도를 계산
        genre_counts = Counter(all_genres)
        
        # 4. 템플릿에 전달하기 쉽게 리스트 형식으로 변환
        top_genres = [{'genre': g, 'count': c} for g, c in genre_counts.most_common(5)] # Top 5 장르
        # --------------------------------------------------------

        # 5. 최종 Context 구성
        context = {
            'user_profile': user_profile,
            'top_tracks': top_tracks_data['items'][:5], # HTML에는 다시 Top 5만 표시
            'top_genres': top_genres, # ⭐ 추가된 장르 데이터 ⭐
        }
        
        return render(request, 'dashboard.html', context)

    except Exception as e:
        print(f"대시보드 로딩 중 오류: {e}") 
        render(request, 'home.html', {'error': f'데이터 로딩 오류: {e}'})

@login_required
def visuals_view(request):
    django_user = request.user
    
    try:
        # 1. 토큰 획득 (인증 상태이므로 토큰은 존재한다고 가정)
        token_obj = SpotifyToken.objects.get(user=django_user)
        spotify_user_id = token_obj.spotify_id

        # 2. Spotify 클라이언트 획득 (토큰 갱신 포함)
        # 모든 API 호출에 사용할 sp 객체를 한 번만 획득합니다.
        sp = get_user_spotify_client(spotify_user_id) 
        
        # 3. 데이터 수집/갱신 및 분석 로직 통합 호출
        # (save_top_tracks_data는 DB에 데이터가 없거나 오래되면 갱신합니다.)
        # get_visual_data 함수 내에서 데이터의 유무를 판단하고 필요시 수집합니다.
        print(f"DEBUG: 2. Spotify ID 획득 성공: {spotify_user_id}")
        # ⭐ 핵심 수정: 데이터 수집 여부를 확인하는 로직을 spotify.py로 위임하거나,
        #             여기서 명시적으로 DB에 데이터가 없으면 수집합니다.
        if not Track.objects.filter(user=django_user).exists():
            print("DEBUG: 3. DB에 데이터 없음, 수집 시작...")
            spotify.save_top_tracks_data(sp, django_user)
        
        print("DEBUG: 4. 데이터 수집/확인 완료, 시각화 준비.")
        # 4. API 호출: 프로필 정보 획득 (Header 표시용)
        # sp 객체는 2단계에서 갱신되었거나 유효하므로 바로 사용합니다.
        user_profile = sp.me() 
        
        # 5. 분석 데이터 로드 (DB에서 읽어옴, 분석 및 포맷 변환)
        # spotify.py의 함수는 이제 DB만 조회하여 데이터를 가져와 포맷합니다.
        analysis_data = spotify.get_all_visual_data(django_user)
        
        # 6. Context 구성 및 렌더링
        context = {
            'user_profile': user_profile,
            
            # Python 객체 그대로 전달 (Django가 문자열로 출력)
            'all_tracks': analysis_data['all_tracks'],
            'top_genres': analysis_data['top_genres'],
            'initial_popularity_data': analysis_data['initial_popularity_data'],
            'top_artists_focus': analysis_data['top_artists_focus'],
            
            'max_ranking': analysis_data['max_ranking'], 
            'total_tracks': len(analysis_data['all_tracks']), # 필요한 경우 추가
        }
        
        return render(request, 'visuals.html', context)


    except SpotifyToken.DoesNotExist:
        # DB에 토큰이 없다는 것은 비정상적인 상태 (로그인 했지만 토큰이 삭제됨)
        # 다시 로그인하도록 유도합니다.
        return redirect('spotify_login')
        
    except Exception as e:
        # API 호출 오류 (400, 403 등) 또는 데이터베이스 오류 발생 시
        print(f"!!! 시각화 데이터 로딩 중 치명적인 오류 발생: {e} !!!")
        
        # 오류 발생 시 사용자에게 친절한 화면을 보여주거나 로그인 페이지로 리다이렉트
        return render(request, 'home.html', {'error': f'시각화 데이터 로딩 중 오류 발생: {e}'})

@login_required
def get_popularity_data(request):
    """
    AJAX 요청을 처리하여 특정 순위 범위(N)에 대한 인기도 분포 데이터를 JSON으로 반환합니다.
    """
    # 1. N 값 (순위 제한) 추출. 기본값은 50
    # request.GET.get('n')을 사용하여 URL 쿼리 파라미터 (예: ?n=70)의 'n' 값을 가져옵니다.
    ranking_limit_str = request.GET.get('n', '50')
    
    try:
        # 안전을 위해 문자열을 정수로 변환합니다.
        ranking_limit = int(ranking_limit_str)
    except ValueError:
        ranking_limit = 50 # 잘못된 값이 오면 기본값 50 사용

    # 2. Spotify 로직 함수 호출 (이 함수는 이전에 main/spotify.py에 추가되었습니다)
    popularity_data = spotify.calculate_popularity_distribution(
        request.user, 
        ranking_limit
    )
    
    # 3. JSON 응답 반환 (프론트엔드가 기대하는 JSON 형식)
    return JsonResponse({'popularity_data': popularity_data})

# 헬퍼 함수: SpotifyOAuth 객체 생성
def get_spotify_oauth():
    print(f"Views.py에서 확인한 Client ID: {settings.SPOTIFY_CLIENT_ID}")
    return SpotifyOAuth(
        client_id=settings.SPOTIFY_CLIENT_ID,
        client_secret=settings.SPOTIFY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIFY_REDIRECT_URI,
        scope=settings.SPOTIFY_SCOPE,
        cache_path=None # Django 서버에서는 파일 캐시 대신 DB를 사용
    )

# 1. 로그인 시작 엔드포인트
def spotify_login(request):
    """
    사용자를 Spotify 권한 부여 페이지로 리디렉션합니다.
    """
    sp_oauth = get_spotify_oauth()
    
    # 인증 URL 생성 및 사용자 리디렉션
    auth_url = sp_oauth.get_authorize_url(state=request.session.session_key)
    
    # CSRF 방지를 위해 state 값을 세션에 저장
    # (주의: 실제 프로덕션 환경에서는 세션 키가 아닌 더 안전한 state 생성 및 검증 로직 필요)
    request.session['spotify_auth_state'] = request.session.session_key
    
    return redirect(auth_url)

def spotify_callback(request):
    
    # ... (1, 2, 3단계: Code 획득 및 토큰 교환 로직 - 생략)
    code = request.GET.get('code')
    state = request.GET.get('state')
    error = request.GET.get('error')
    
    sp_oauth = get_spotify_oauth()
    
    try:
        token_info = sp_oauth.get_access_token(code)
    except Exception as e:
        return render(request, 'home.html', {'error': f'토큰 교환 실패: {e}'})

    # Access Token으로 사용자 정보 획득 및 Spotify 클라이언트 생성
    sp = spotipy.Spotify(auth=token_info['access_token'])
    user_data = sp.me()
    user_id = user_data['id']
    
    # 만료 시각 계산
    expires_in_seconds = token_info.get('expires_in', 3600)
    expires_at_datetime = timezone.now() + timedelta(seconds=expires_in_seconds)
    
    
    # ----------------------------------------------------
    # ⭐ 4. 토큰 정보 DB 저장 및 Django User 연동 (동일) ⭐
    # ----------------------------------------------------
    username = user_id
    
    user, created = User.objects.get_or_create(
        username=username, 
        defaults={
            'email': user_data.get('email', f'{user_id}@spotify.com'),
            'first_name': user_data.get('display_name', 'Spotify User'),
        }
    )
    
    SpotifyToken.objects.update_or_create(
        spotify_id=user_id,
        defaults={
            'user': user,
            'access_token': token_info['access_token'],
            'refresh_token': token_info.get('refresh_token'),
            'expires_in': expires_in_seconds,
            'expires_at': expires_at_datetime,
            'token_type': token_info['token_type'],
        }
    )

    # ----------------------------------------------------
    # ⭐ 5. Django 세션에 로그인 처리 (동일) ⭐
    # ----------------------------------------------------
    user.backend = 'django.contrib.auth.backends.ModelBackend' 
    login(request, user)

    if request.user.is_authenticated:
        print(f"⭐ DEBUG: 로그인 성공! Django User ID: {request.user.id}")
    else:
        # 이 메시지가 터미널에 뜨면 로그인 함수가 실패한 것입니다.
        print("❌ DEBUG: login(request, user) 호출 후에도 사용자 인증 실패!")
    # 6. 최종적으로 /dashboard 경로로 리다이렉트 (주소창 변경 목적)
    return redirect('/dashboard')

# 헬퍼 함수: Access Token을 갱신하고 DB를 업데이트
def refresh_spotify_token(token_obj):
    # 1. SpotifyOAuth 객체 생성
    auth_manager = get_spotify_oauth()

    try:
        # 2. Refresh Token을 사용하여 새 Access Token 요청
        # spotipy 라이브러리가 API 호출을 통해 토큰을 갱신합니다.
        new_token_info = auth_manager.refresh_access_token(token_obj.refresh_token)
        
        # 3. 모델 필드 업데이트 및 저장
        token_obj.access_token = new_token_info['access_token']
        
        # 새 만료 시각 계산: 현재 시각 + 새로 받은 유효 시간(초)
        expires_in = new_token_info.get('expires_in', 3600)
        token_obj.expires_at = timezone.now() + timedelta(seconds=expires_in)
        token_obj.expires_in = expires_in # expires_in 필드도 업데이트 (선택 사항)
        token_obj.save()
        
        return token_obj
        
    except Exception as e:
        print(f"Token refresh failed for user {token_obj.user_id}: {e}")
        # 갱신 실패 (Refresh Token 만료, 권한 해지 등) 시 예외 발생
        # 사용자에게 재로그인을 유도해야 함.
        raise Exception("Spotify 인증 만료 또는 오류. 재로그인이 필요합니다.")

# Access Token 상태를 확인하고 유효한 Spotify 클라이언트를 반환하는 메인 함수
def get_user_spotify_client(spotify_id):
    # 1. DB에서 토큰 로드
    try:
        token_obj = SpotifyToken.objects.get(spotify_id=spotify_id)
    except SpotifyToken.DoesNotExist:
        raise Exception(f"User {spotify_id} does not have a Spotify token.")

    # 2. 만료 시각 확인
    # DB에 저장된 만료 시각이 현재 시각(timezone.now())보다 작거나 같으면 만료됨
    is_expired = token_obj.expires_at <= timezone.now()
    
    if is_expired:
        print(f"Token expired for user {spotify_id}. Attempting refresh.")
        # 3. 만료된 경우, 갱신 함수 호출
        token_obj = refresh_spotify_token(token_obj)
    
    # 4. 유효한 토큰(갱신되었거나 원래 유효했던)으로 Spotify 클라이언트 객체 반환
    return spotipy.Spotify(auth=token_obj.access_token)

# 사용자의 재생 목록을 보여주는 뷰 함수 (간단한 예시)
def get_playlists(request):
    django_user = request.user 
    
    try:
        # 2. Django User 객체에 연결된 SpotifyToken 객체를 가져옵니다.
        token_obj = SpotifyToken.objects.get(user=django_user)
        
        # 3. 토큰 객체에서 Spotify ID를 추출하여 클라이언트 함수에 전달
        # Spotify ID가 'spotify_id' 필드에 저장되어 있다고 가정
        spotify_user_id = token_obj.spotify_id 

        # get_user_spotify_client 함수는 이제 토큰 객체를 직접 전달받도록 수정될 수 있습니다.
        # 또는 기존처럼 spotify_user_id를 사용하여 토큰을 DB에서 다시 로드할 수 있습니다.
        
        sp = get_user_spotify_client(spotify_user_id)
        
        # ... (나머지 API 호출 로직은 동일)
        playlists = sp.current_user_playlists(limit=50)

        context = {
            'user_id': spotify_user_id, # HTML에 표시할 Spotify ID
            'playlists_count': playlists['total'],
            'playlists': playlists['items']
        }
        return render(request, 'playlists.html', context)
    except SpotifyToken.DoesNotExist:
        return render(request, 'error.html', {'error': '토큰 없음. 로그인 필요.'})
    except Exception as e:
        return render(request, 'error.html', {'error': f'API 호출 중 오류 발생: {e}'})














