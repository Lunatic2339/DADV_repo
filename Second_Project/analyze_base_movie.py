import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np

# ==============================================================================
# [설정] 경로 및 폰트
# ==============================================================================
BASE_DIR = r"C:\Users\anthony\Desktop\Univ Assingments\2025\DADV\DADV_repo\Second_Project"
INPUT_FILE = "tmdb_global_movies_massive_final.csv"  # 전처리 V2 완료된 파일

# 저장할 폴더 경로 설정 (Result/Base_Analysis)
RESULT_DIR = os.path.join(BASE_DIR, "Result")
SAVE_DIR = os.path.join(RESULT_DIR, "Base_Analysis")

# 폴더가 없으면 생성
if not os.path.exists(RESULT_DIR):
    os.makedirs(RESULT_DIR)
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

# 한글 폰트 설정 (Windows 기준)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 로드
file_path = os.path.join(BASE_DIR, INPUT_FILE)
if not os.path.exists(file_path):
    print("❌ 전처리된 데이터 파일이 없습니다. 'preprocess_tmdb_v2.py'를 먼저 실행하세요.")
    exit()

df = pd.read_csv(file_path)
print(f">>> [Base Analysis] 총 {len(df)}개 영화의 모집단 통계 분석을 시작합니다.")
print(f">>> 저장 위치: {SAVE_DIR}")

# ==============================================================================
# 1. 범주형 데이터 빈도 분석 (Genres, Country, Success_Status)
# ==============================================================================

# (1) Genres (장르) - 중복 장르 분리 후 카운트
print(">>> [1/9] 장르(Genres) 빈도 분석 중...")
df_genres = df.assign(genre_list=df['genres'].str.split(', ')).explode('genre_list')
plt.figure(figsize=(12, 8))
sns.countplot(data=df_genres, y='genre_list', order=df_genres['genre_list'].value_counts().index, palette='viridis')
plt.title('모집단의 장르별 빈도 (Genres Distribution)')
plt.xlabel('영화 편수')
plt.ylabel('장르')
plt.grid(axis='x', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(SAVE_DIR, '1_stat_genres.png'))
plt.close()

# (2) Country (제작 국가) - 상위 15개국만
print(">>> [2/9] 제작 국가(Country) 빈도 분석 중...")
df_country = df.assign(country_list=df['country'].str.split(', ')).explode('country_list')
top_countries = df_country['country_list'].value_counts().head(15).index

plt.figure(figsize=(12, 6))
sns.countplot(data=df_country[df_country['country_list'].isin(top_countries)], 
              x='country_list', order=top_countries, palette='magma')
plt.title('제작 국가 Top 15 빈도 (Country Distribution)')
plt.xlabel('국가 코드')
plt.ylabel('영화 편수')
plt.tight_layout()
plt.savefig(os.path.join(SAVE_DIR, '2_stat_country.png'))
plt.close()

# (3) Success Status (흥행 등급) - 파이차트
print(">>> [3/9] 흥행 등급(Success Status) 빈도 분석 중...")
status_counts = df['success_status'].value_counts()
plt.figure(figsize=(8, 8))
plt.pie(status_counts, labels=status_counts.index, autopct='%1.1f%%', 
        startangle=140, colors=['#ff9999','#66b3ff','#99ff99','#ffcc99'])
plt.title('흥행 등급 비율 (Success Status)')
plt.savefig(os.path.join(SAVE_DIR, '3_stat_success_status.png'))
plt.close()

# ==============================================================================
# 2. 수치형 데이터 빈도(분포) 분석 (Budget, Revenue, ROI, Ratings, etc.)
# ==============================================================================

def plot_histogram(column, title, filename, color='skyblue', log_scale=False, limit_quantile=None):
    """히스토그램 그리는 함수"""
    print(f">>> 분석 중: {column}...")
    plt.figure(figsize=(10, 6))
    
    data_to_plot = df[column]
    
    # 극단치 제외 옵션 (그래프가 너무 찌그러질 경우 사용)
    if limit_quantile:
        limit = data_to_plot.quantile(limit_quantile)
        data_to_plot = data_to_plot[data_to_plot <= limit]
        title += f" (상위 {int((1-limit_quantile)*100)}% 이상치 제외)"

    sns.histplot(data_to_plot, bins=40, kde=True, color=color, log_scale=log_scale)
    plt.title(title)
    plt.xlabel(column)
    plt.ylabel('빈도 (Frequency)')
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(SAVE_DIR, filename))
    plt.close()

# (4) Budget (제작비) - 로그 스케일 적용 (액수 차이가 커서)
plot_histogram('budget', '제작비 분포 (Budget)', '4_stat_budget.png', color='skyblue', log_scale=True)

# (5) Revenue (매출액) - 로그 스케일 적용
plot_histogram('revenue', '매출액 분포 (Revenue)', '5_stat_revenue.png', color='salmon', log_scale=True)

# (6) ROI Ratio (수익률) - 극단적인 이상치(50배 이상 등)가 많아 상위 5% 제외 후 시각화
plot_histogram('roi_ratio', '수익률 분포 (ROI Ratio)', '6_stat_roi_ratio.png', color='purple', limit_quantile=0.95)

# (7) Vote Average (평점)
plot_histogram('vote_average', '평점 분포 (Vote Average)', '7_stat_vote_average.png', color='gold')

# (8) Vote Count (투표 수) - 로그 스케일
plot_histogram('vote_count', '평가 참여 수 분포 (Vote Count)', '8_stat_vote_count.png', color='orange', log_scale=True)

# (9) Popularity (인기도)
plot_histogram('popularity', '인기도 분포 (Popularity)', '9_stat_popularity.png', color='green', log_scale=True)

print("-" * 50)
print(f"✅ [완료] 모든 모집단 통계 이미지가 생성되었습니다.")
print(f"📂 확인 경로: {SAVE_DIR}")