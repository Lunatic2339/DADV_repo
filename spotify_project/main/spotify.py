from django.db import transaction
from django.contrib.auth.models import User
from django.conf import settings
from collections import Counter
import spotipy
from django.db.models import Count, Q

from .models import Artist, Track # Artist, Track 모델 임포트

# main/spotify.py

from django.db import transaction
from django.contrib.auth.models import User 
import spotipy
# ... (다른 임포트)

@transaction.atomic
def save_top_tracks_data(sp: spotipy.Spotify, django_user: User):
    
    # 1. 기존 데이터 삭제
    Track.objects.filter(user=django_user).delete()
    
    # ⭐⭐ 2. 페이지네이션 로직 (all_tracks 정의 및 채우기) ⭐⭐
    all_tracks = [] # ⭐ all_tracks 리스트 초기화 ⭐
    limit = 50           
    offset = 0           
    max_collect = 500    # 현재 설정된 최대 수집량 (최대 500개)
    
    while offset < max_collect:
        print(offset)
        results = sp.current_user_top_tracks(
            limit=limit, 
            offset=offset, 
            time_range='long_term'
        )
        
        items = results.get('items', [])
        
        if not items:
            break
            
        all_tracks.extend(items) # all_tracks 리스트에 데이터 추가
        
        offset += limit
        
        if results.get('total') and offset >= results['total']:
            break
            
    # ----------------------------------------------------
    # 3. ID 추출 (트랙, 아티스트, 앨범)
    # ----------------------------------------------------
    track_artist_map = {} 
    artist_ids = []
    album_ids = [] 
    
    for track_data in all_tracks:
        if not track_data or not track_data.get('artists'): continue
        main_artist_id = track_data['artists'][0]['id']
        artist_ids.append(main_artist_id)
        
        album_ids.append(track_data['album']['id'])
        track_artist_map[track_data['id']] = main_artist_id 

    # ----------------------------------------------------
    # 4. 아티스트 상세 정보 Bulk 획득 및 DB 저장 (Batching 유지)
    # ----------------------------------------------------
    unique_artist_ids = list(set(artist_ids))
    CHUNK_SIZE = 50 # 안전한 Batch 크기 유지 최대 50
    all_artist_details = []
    
    for i in range(0, len(unique_artist_ids), CHUNK_SIZE):
        chunk_ids = unique_artist_ids[i:i + CHUNK_SIZE] 
        
        try:
            # API 호출 및 결과 획득
            artists_detail_data = sp.artists(chunk_ids) 
            
            if artists_detail_data and artists_detail_data.get('artists'):
                all_artist_details.extend([a for a in artists_detail_data['artists'] if a is not None])

        except Exception as e:
            # API 호출 중 오류 발생 시 (네트워크 등) 해당 Batch만 건너뛰고 계속 진행
            print(f"API Batch 호출 중 오류 발생 ({len(chunk_ids)}개 ID): {e}")
            continue # 오류가 나더라도 다음 Batch로 넘어가서 롤백 방지

    artist_details_dict = {artist['id']: artist for artist in all_artist_details}
    
    for artist_id in unique_artist_ids:
        detail = artist_details_dict.get(artist_id)
        if detail:
            Artist.objects.update_or_create(
                spotify_id=artist_id,
                defaults={
                    'name': detail['name'],
                    'popularity': detail['popularity'],
                    'followers_total': detail['followers']['total'],
                    'genres': ", ".join(detail['genres']),
                }
            )

    # ----------------------------------------------------
    # 5. Album 상세 정보 Bulk 획득 (Batching 유지)
    # ----------------------------------------------------
    unique_album_ids = list(set(album_ids))
    all_album_details = []
    
    for i in range(0, len(unique_album_ids), CHUNK_SIZE):
        chunk_ids = unique_album_ids[i:i + CHUNK_SIZE]
        
        try:
            # API 호출
            albums_detail_data = sp.albums(chunk_ids)
            
            if albums_detail_data and albums_detail_data.get('albums'):
                all_album_details.extend([a for a in albums_detail_data['albums'] if a is not None])
        
        except Exception as e:
            # 앨범 정보 획득 실패 시 해당 청크는 건너뛰고 나머지 데이터는 저장되도록 합니다.
            print(f"앨범 Batch 호출 중 오류 발생 ({len(chunk_ids)}개 ID): {e}")
            continue

    album_details_dict = {album['id']: album for album in all_album_details}


    # ----------------------------------------------------
    # 6. Track 데이터 저장 (최종 로직)
    # ----------------------------------------------------
    for index, track_data in enumerate(all_tracks): # ⭐ 이 all_tracks는 이제 위에서 정의된 리스트입니다.
        ranking = index + 1
        artist_id = track_artist_map.get(track_data['id'])
        
        if not artist_id: continue

        # 앨범 정보 획득 및 연도 추출
        album_id = track_data['album']['id']
        album_detail = album_details_dict.get(album_id, {})
        release_date_str = album_detail.get('release_date', '0000') 
        
        try:
            release_year = int(release_date_str.split('-')[0])
        except:
            release_year = None
            
        try:
            artist_obj = Artist.objects.get(spotify_id=artist_id) 
        except Artist.DoesNotExist:
            continue 
            
        # 장르 추출 (Artist의 첫 번째 장르)
        artist_detail = artist_details_dict.get(artist_id, {})
        genres_list = artist_detail.get('genres', [])
        track_genre_value = genres_list[0] if genres_list else "" 
        
        Track.objects.create(
            spotify_id=track_data['id'],
            name=track_data['name'],
            popularity=track_data['popularity'],
            duration_ms=track_data['duration_ms'],
            
            release_year=release_year, 
            genre=track_genre_value, 
            
            artist=artist_obj, 
            user=django_user,
            ranking=ranking
        )
    
    return True

def calculate_popularity_distribution(django_user, ranking_limit):
    """
    사용자의 상위 N개 트랙에 대한 인기도(Popularity) 분포를 10점 단위 버킷으로 계산합니다.
    (AJAX 동적 갱신용)
    """
    
    # 1. 인기도 버킷 (1-10, 11-20, ...) 정의
    popularity_buckets = [
        (f'{i+1}-{i+10}', (i+1, i+10)) 
        for i in range(0, 100, 10)
    ]
    
    popularity_data = []

    # ⭐ N 값(ranking_limit)에 따라 필터링된 쿼리셋 사용 ⭐
    popularity_queryset = Track.objects.filter(
        user=django_user,
        ranking__lte=ranking_limit # 동적으로 N 값 사용
    )

    for label, (min_pop, max_pop) in popularity_buckets:
        
        # 해당 popularity 범위에 속하는 트랙의 개수를 계산
        count = popularity_queryset.filter(
            popularity__gte=min_pop,
            popularity__lte=max_pop
        ).count()
        
        popularity_data.append({
            'bucket': label,
            'count': count
        })
        
    return popularity_data


def get_all_visual_data(django_user):
    """
    DB에서 필요한 모든 시각화 및 목록 데이터를 추출하여 Dictionary 형태로 반환합니다.
    (visuals_view가 호출하는 최종 분석 함수)
    """
    
    # 1. ⭐ 전체 Track 목록 획득 (왼쪽 목록용) ⭐
    # Artist 객체 이름 접근을 위해 select_related('artist') 사용
    all_tracks_qs = Track.objects.filter(user=django_user).select_related('artist').order_by('ranking')
    

    # ⭐⭐ 여기에 인스턴스 개수 출력 코드를 추가합니다. ⭐⭐
    track_count = all_tracks_qs.count()
    print(f"--- DEBUG INFO ---")
    print(f"DB에서 조회된 총 Track 인스턴스 개수: {track_count}개")
    print(f"------------------")

    # 템플릿 렌더링에 적합한 형태로 List of Dicts로 변환
    all_tracks_list = []
    for track in all_tracks_qs:
        all_tracks_list.append({
            'ranking': track.ranking,
            'name': track.name,
            'genre': track.genre,
            'popularity': track.popularity,
            'release_year': track.release_year,
            # ForeignKey 필드를 통해 아티스트 이름 접근
            'artist_name': track.artist.name, 
        })


    # 2. ⭐ 장르 분석 데이터 획득 (오른쪽 차트용) ⭐
    # Track 모델에서 장르별 빈도수를 집계합니다.
    # Count('genre')를 사용하여 DB에서 효율적으로 계산
    genre_analysis = Track.objects.filter(user=django_user).values('genre').annotate(count=Count('genre')).order_by('-count')[:10]
    
    top_genres = [{'genre': item['genre'], 'count': item['count']} for item in genre_analysis]

    # 3. ⭐ 초기 인기도 분포 데이터 획득 (슬라이더 초기값 N=50 기준) ⭐
    INITIAL_RANKING_LIMIT = 50 
    initial_popularity_data = calculate_popularity_distribution(django_user, INITIAL_RANKING_LIMIT)

    # Artist의 이름(ForeignKey 필드)을 기준으로 Track 개수를 세어 Top 10을 추출
    top_artists_analysis = Track.objects.filter(user=django_user) \
        .values('artist__name') \
        .annotate(count=Count('artist__name')) \
        .order_by('-count')[:10]
        
    # 시각화를 위한 리스트 형태로 변환
    top_artists_focus = [
        {'artist_name': item['artist__name'], 'count': item['count']} 
        for item in top_artists_analysis
    ]
    print("--- DEBUG: TOP ARTISTS FOCUS ---")
    print(f"Top Artist 데이터 개수: {len(top_artists_focus)}개")
    if len(top_artists_focus) == 0:
        # 데이터가 없을 때, 왜 없는지 확인
        print("경고: Top Artist 데이터가 비어 있습니다. DB에 트랙과 연결된 아티스트 정보가 없는지 확인하세요.")
    else:
        print(f"첫 번째 아티스트: {top_artists_focus[0]}")
    print("--------------------------------")
    
    # 4. Context에 전달할 최종 Dictionary 반환
    return {
        'all_tracks': all_tracks_list,
        'top_genres': top_genres,
        'initial_popularity_data': initial_popularity_data, # 초기 인기도 데이터
        'max_ranking': all_tracks_qs.count(), # 슬라이더 최대값 설정
        'top_artists_focus': top_artists_focus,
    }