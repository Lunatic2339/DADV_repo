import requests
import pandas as pd
import time
import os
import random

# ==============================================================================
# [설정] API 키 및 저장 경로
# ==============================================================================
TMDB_API_KEY = "c0be314b92810021715f2683eb631f79"  # 👈 본인 키 입력 필수!

BASE_DIR = r"C:\Users\anthony\Desktop\Univ Assingments\2025\DADV\DADV_repo\Second_Project"
OUTPUT_FILE = "tmdb_global_movies_massive.csv" # 파일명: massive
SAVE_PATH = os.path.join(BASE_DIR, OUTPUT_FILE)

# ==============================================================================
# [함수] API 호출
# ==============================================================================
def get_movies_from_page(page, sort_by="popularity.desc", min_votes=50):
    """특정 페이지의 영화 목록 20개를 가져옵니다."""
    url = "https://api.themoviedb.org/3/discover/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "language": "ko-KR",
        "sort_by": sort_by,
        "include_adult": "false",
        "vote_count.gte": min_votes, 
        "primary_release_date.gte": "2000-01-01", # 2000년 이후 영화 (너무 옛날 영화는 화폐가치 왜곡 있음)
        "page": page
    }
    try:
        res = requests.get(url, params=params, timeout=5)
        if res.status_code == 200:
            return res.json().get('results', [])
    except:
        pass
    return []

def get_movie_details(movie_id):
    """영화 상세 정보 (예산, 매출 등) 조회"""
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    params = {"api_key": TMDB_API_KEY, "language": "ko-KR"}
    try:
        res = requests.get(url, params=params, timeout=5)
        if res.status_code == 200:
            data = res.json()
            genres = [g['name'] for g in data.get('genres', [])]
            countries = [c['iso_3166_1'] for c in data.get('production_countries', [])]
            return {
                'budget': data.get('budget', 0),
                'revenue': data.get('revenue', 0),
                'runtime': data.get('runtime', 0),
                'genres': ", ".join(genres),
                'country': ", ".join(countries),
                'status': data.get('status', '')
            }
    except:
        pass
    return {}

# ==============================================================================
# [실행] 대규모 수집 로직
# ==============================================================================
if not os.path.exists(BASE_DIR): os.makedirs(BASE_DIR)

print(">>> [Massive Collection] 2,500개 이상의 데이터를 목표로 수집합니다.")
print(">>> (시간이 다소 소요됩니다. 멈추지 말고 기다려주세요!)")

candidate_movies = []
seen_ids = set()

# ------------------------------------------------------------------------------
# 1단계: 확실한 데이터 확보 (Top Tier & Bottom Tier) - 약 800개
# ------------------------------------------------------------------------------
print("\n>>> [1단계] 흥행작 및 유명 영화 수집 (기초 체력 다지기)")

# 매출액 순 20페이지 (400개)
for i in range(1, 21):
    items = get_movies_from_page(i, sort_by="revenue.desc")
    for m in items:
        if m['id'] not in seen_ids:
            m['collection_type'] = 'Top_Revenue'
            candidate_movies.append(m); seen_ids.add(m['id'])
    print(f"\r   -> 흥행작 수집 중... (현재 {len(candidate_movies)}개)", end="")
    time.sleep(0.1)

# 평점 높은 순 10페이지 (200개) - 명작
for i in range(1, 11):
    items = get_movies_from_page(i, sort_by="vote_average.desc", min_votes=500)
    for m in items:
        if m['id'] not in seen_ids:
            m['collection_type'] = 'Top_Rated'
            candidate_movies.append(m); seen_ids.add(m['id'])
    print(f"\r   -> 명작 수집 중... (현재 {len(candidate_movies)}개)", end="")
    time.sleep(0.1)

# 평점 낮은 순 10페이지 (200개) - 망작
for i in range(1, 11):
    items = get_movies_from_page(i, sort_by="vote_average.asc", min_votes=100)
    for m in items:
        if m['id'] not in seen_ids:
            m['collection_type'] = 'Low_Rated'
            candidate_movies.append(m); seen_ids.add(m['id'])
    print(f"\r   -> 망작 수집 중... (현재 {len(candidate_movies)}개)", end="")
    time.sleep(0.1)

# ------------------------------------------------------------------------------
# 2단계: 무작위 랜덤 수집 (The Wild West) - 목표 2,000개 채울 때까지
# ------------------------------------------------------------------------------
print("\n\n>>> [2단계] 광활한 데이터 바다에서 랜덤 낚시 (Random Sampling)...")
print("   -> 인기순위 50위~500위 페이지 사이를 무작위로 찌릅니다.")

# 50페이지부터 500페이지 사이에서 랜덤으로 100개의 페이지 번호를 뽑음
random_pages = random.sample(range(50, 501), 100) 

for idx, page in enumerate(random_pages):
    items = get_movies_from_page(page, sort_by="popularity.desc")
    for m in items:
        if m['id'] not in seen_ids:
            m['collection_type'] = 'Random_Pick'
            candidate_movies.append(m); seen_ids.add(m['id'])
    
    print(f"\r   -> 랜덤 페이지({page}) 탐색 중... [누적 후보: {len(candidate_movies)}개]", end="")
    time.sleep(0.1)

# ------------------------------------------------------------------------------
# 3단계: 상세 정보 조회 및 필터링 (가장 오래 걸림)
# ------------------------------------------------------------------------------
print(f"\n\n>>> [3단계] 후보 영화 {len(candidate_movies)}개의 재무제표(Budget/Revenue) 전수 조사 시작!")
print("   -> 예산 정보가 없는 영화는 과감히 버려서 데이터 품질을 높입니다.")

final_data = []
valid_count = 0

for idx, movie in enumerate(candidate_movies):
    # 진행률 표시
    if idx % 50 == 0:
        print(f"[{idx}/{len(candidate_movies)}] 처리 중... (유효 데이터: {valid_count}개 확보)")

    details = get_movie_details(movie['id'])
    
    # [중요 필터] 제작비(Budget)가 0인 데이터는 ROI 분석이 불가능하므로 제외
    # 단, 표본 확보를 위해 기준을 조금 낮춤 ($1,000 이상이면 수집)
    if details.get('budget', 0) > 1000: 
        row = {
            'id': movie['id'],
            'title': movie['title'],
            'release_date': movie['release_date'],
            'vote_average': movie['vote_average'],
            'vote_count': movie['vote_count'],
            'popularity': movie['popularity'],
            'collection_type': movie.get('collection_type')
        }
        row.update(details)
        final_data.append(row)
        valid_count += 1
    
    time.sleep(0.05) # API 호출 제한 방지

# ------------------------------------------------------------------------------
# 저장
# ------------------------------------------------------------------------------
df = pd.DataFrame(final_data)
df.to_csv(SAVE_PATH, index=False, encoding='utf-8-sig')

print("\n" + "="*60)
print(f"🎉 대규모 수집 완료!")
print(f"✅ 총 수집 시도: {len(candidate_movies)}개")
print(f"✅ 최종 유효 데이터(예산 정보 있음): {len(df)}개")
print(f"📂 파일 위치: {SAVE_PATH}")
print("="*60)
print("👉 이제 'preprocess_tmdb_v2.py'에서 파일명을 'tmdb_global_movies_massive.csv'로 바꿔주세요!")