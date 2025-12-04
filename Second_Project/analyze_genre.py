import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

# ==============================================================================
# [설정] 경로 및 폰트 (보내주신 성공 코드 기반)
# ==============================================================================
BASE_DIR = r"C:\Users\anthony\Desktop\Univ Assingments\2025\DADV\DADV_repo\Second_Project"
INPUT_FILE = "tmdb_data_final.csv"

# 결과 저장 경로 설정
RESULT_DIR = os.path.join(BASE_DIR, "Result")
SAVE_DIR = os.path.join(RESULT_DIR, "Genre_Analysis")

if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)
    print(f"📁 폴더 생성: {SAVE_DIR}")

# 폰트 설정 (한글 깨짐 방지)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 로드
file_path = os.path.join(BASE_DIR, INPUT_FILE)

if not os.path.exists(file_path):
    print(f"❌ 오류: 데이터 파일을 찾을 수 없습니다.\n경로: {file_path}")
    exit()

print(f"✅ 데이터 로드 성공: {file_path}")
df = pd.read_csv(file_path)

# ==============================================================================
# 1. 데이터 전처리
# ==============================================================================
print(">>> 데이터 전처리 중...")

# (1) 장르 분리
# 보내주신 코드 참고: 문자열 "Action, Adventure" -> 리스트 ['Action', 'Adventure']
# 만약 데이터가 이미 리스트 형태라면 에러가 날 수 있어 안전장치 추가
try:
    if df['genres'].dtype == object and df['genres'].str.contains(',').any():
        df['genre_list'] = df['genres'].str.split(', ')
    else:
        # 혹시 JSON 형태거나 다른 형태일 경우를 대비해 그대로 사용하거나 처리
        # 여기서는 보내주신 코드가 split을 썼으므로 그 형식을 신뢰합니다.
        df['genre_list'] = df['genres'].str.split(', ')
except Exception as e:
    print("⚠️ 장르 처리 중 경고, 기본 분리 방식 시도:", e)
    df['genre_list'] = df['genres'].str.split(', ')

# (2) 장르별 데이터 폭파 (Explode)
df_exploded = df.explode('genre_list')

# (3) ROI 계산 (수익률 %)
# ROI = (매출 - 예산) / 예산 * 100
# 예산이 0인 경우 무한대가 나오므로 NaN 처리
df_exploded['ROI'] = np.where(df_exploded['budget'] > 0, 
                              (df_exploded['revenue'] - df_exploded['budget']) / df_exploded['budget'] * 100, 
                              np.nan)

# 분석할 장르 선정 (데이터 30개 이상인 장르만)
genre_counts = df_exploded['genre_list'].value_counts()
target_genres = genre_counts[genre_counts >= 30].index

print(f" -> 분석 대상 장르: {len(target_genres)}개")

# ==============================================================================
# 2. 장르별 시각화 및 통계 박스 생성
# ==============================================================================
metrics = ['vote_average', 'popularity', 'budget', 'ROI']
metric_titles = ['평점 (Vote)', '인기도 (Popularity)', '예산 (Budget $)', 'ROI (수익률 %)']
colors = ['#FF9999', '#66B2FF', '#99FF99', '#FFCC99']

print("\n>>> 장르별 이미지 생성 시작...")

for genre in target_genres:
    subset = df_exploded[df_exploded['genre_list'] == genre]
    
    # --------------------------------------------------------------------------
    # [핵심] 이미지 우측 상단에 들어갈 통계 텍스트
    # --------------------------------------------------------------------------
    stats_text = (
        f"GENRE: {genre.upper()}\n"
        f"Total Movies: {len(subset)}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Avg Vote  : {subset['vote_average'].mean():.2f} (Med: {subset['vote_average'].median():.2f})\n"
        f"Avg ROI   : {subset['ROI'].mean():.0f}% (Med: {subset['ROI'].median():.0f}%)\n"
        f"Avg Budget: ${subset['budget'].mean()/1_000_000:.1f}M\n"
        f"Avg Pop   : {subset['popularity'].mean():.1f}"
    )

    # 캔버스 (2x2)
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'Genre Distribution Analysis: {genre}', fontsize=24, fontweight='bold', x=0.05, ha='left')

    for i, metric in enumerate(metrics):
        row, col = i // 2, i % 2
        ax = axes[row, col]
        
        # 데이터 정제 (NaN, 무한대 제거)
        data = subset[metric].replace([np.inf, -np.inf], np.nan).dropna()
        
        # 시각화 퀄리티를 위해 극단적 이상치(상위 1%)만 살짝 제외하고 그림 (통계 텍스트는 전체 기준)
        if len(data) > 0:
            q_high = data.quantile(0.99)
            plot_data = data[data <= q_high]
        else:
            plot_data = data

        if len(plot_data) == 0:
            continue

        # 히스토그램 & KDE
        sns.histplot(plot_data, kde=True, ax=ax, color=colors[i], edgecolor='black', alpha=0.7)
        
        ax.set_title(metric_titles[i], fontsize=14, fontweight='bold')
        ax.set_xlabel('')
        ax.grid(axis='y', linestyle='--', alpha=0.5)

        # 평균/중앙값 선 표시
        mean_val = data.mean()
        median_val = data.median()
        ax.axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.1f}')
        ax.axvline(median_val, color='green', linestyle=':', linewidth=3, label=f'Median: {median_val:.1f}')
        ax.legend(loc='upper right')

    # --------------------------------------------------------------------------
    # 텍스트 박스 삽입 (우측 상단 빈 공간)
    # --------------------------------------------------------------------------
    # 그래프 영역 조절 (오른쪽 공간 확보)
    plt.tight_layout(rect=[0, 0, 0.78, 0.95]) 
    
    # 텍스트 박스 그리기
    fig.text(
        0.80, 0.90,  # x, y 위치 (0~1 기준)
        stats_text, 
        fontsize=15, 
        family='monospace', # 숫자가 가지런히 보이게
        verticalalignment='top', 
        horizontalalignment='left',
        bbox=dict(boxstyle="round,pad=0.8", facecolor="#f8f9fa", edgecolor="black", alpha=1.0)
    )

    # 저장
    save_name = f"{genre}_Analysis.png"
    # 파일명에 특수문자가 있을 경우 처리 (예: Sci-Fi)
    save_name = save_name.replace('/', '_').replace(':', '')
    
    save_path = os.path.join(SAVE_DIR, save_name)
    plt.savefig(save_path)
    plt.close()
    
    print(f" Saved: {save_name}")

print("-" * 50)
print(f"🎉 모든 장르 분석 완료! '{SAVE_DIR}' 폴더를 확인하세요.")