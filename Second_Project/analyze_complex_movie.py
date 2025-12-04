import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np
from scipy import stats

# ==============================================================================
# [설정] 경로 및 폰트
# ==============================================================================
BASE_DIR = r"C:\Users\anthony\Desktop\Univ Assingments\2025\DADV\DADV_repo\Second_Project"
INPUT_FILE = "tmdb_data_final.csv"

# ✅ 평점 컬럼명 설정 (데이터에 따라 'vote_average' 또는 'rating' 등으로 수정 필요)
RATING_COL = 'vote_average' 

RESULT_DIR = os.path.join(BASE_DIR, "Result")
SAVE_DIR = os.path.join(RESULT_DIR, "Complex_Analysis")

if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 로드
file_path = os.path.join(BASE_DIR, INPUT_FILE)
if not os.path.exists(file_path):
    print("❌ 데이터 파일이 없습니다.")
    exit()

df = pd.read_csv(file_path)

# ==============================================================================
# 1. 데이터 가공 (로그 변환)
# ==============================================================================
print(">>> [Complex Analysis] 분석 시작...")

# 로그 변환 (그래프를 예쁘게 펴기 위해)
df_log = df[(df['budget'] > 10000) & (df['revenue'] > 10000)].copy()
df_log['log_budget'] = np.log10(df_log['budget'])
df_log['log_revenue'] = np.log10(df_log['revenue'])

print(f"   -> 유효 표본: {len(df_log)}개")

# ==============================================================================
# 2. [분석 1] Joint Plot (색상 복구 & P-value 추가)
# ==============================================================================
print("\n>>> [시각화 1] Joint Plot 생성 중 (P-value 포함)...")

g = sns.jointplot(
    data=df_log, 
    x='log_budget', 
    y='log_revenue', 
    kind='reg',
    height=9,
    scatter_kws={'alpha': 0.3, 's': 20, 'color': 'steelblue'}, 
    line_kws={'color': 'red'} 
)

g.set_axis_labels('제작비 (Log10 Budget)', '매출액 (Log10 Revenue)', fontsize=12)
g.fig.suptitle('제작비와 매출액의 상관관계 (Joint Plot)', y=1.02, fontsize=15)

r, p = stats.pearsonr(df_log['log_budget'], df_log['log_revenue'])
p_text = "< 0.001" if p < 0.001 else f"{p:.4f}"

g.ax_joint.text(
    df_log['log_budget'].min(), 
    df_log['log_revenue'].max(), 
    f'Pearson r = {r:.2f}\nP-value = {p_text}', 
    fontweight='bold', fontsize=13, 
    bbox=dict(facecolor='white', alpha=0.9, edgecolor='gray', boxstyle='round')
)

save_path1 = os.path.join(SAVE_DIR, '1_budget_revenue_joint.png')
plt.savefig(save_path1)
print(f"   ✅ Joint Plot 저장 완료: {save_path1}")

# ==============================================================================
# 3. [분석 2] 등급별 상세 산점도 (Mega-Hit vs Flop 구분)
# ==============================================================================
print(">>> [시각화 2] 등급별 상세 산점도 생성 중...")

plt.figure(figsize=(12, 9))

status_order = ['Flop', 'Break-even', 'Hit', 'Mega-Hit']
palette = {
    'Flop': '#FF4500',       # 빨강 (실패)
    'Break-even': '#808080', # 회색 (본전)
    'Hit': '#1E90FF',        # 파랑 (성공)
    'Mega-Hit': '#FFD700'    # 금색 (초대박)
}

sns.scatterplot(
    data=df_log, 
    x='log_budget', 
    y='log_revenue', 
    hue='success_status', 
    hue_order=status_order,
    palette=palette,
    alpha=0.7, 
    s=60,
    edgecolor='w'
)

lims = [np.min([plt.xlim(), plt.ylim()]), np.max([plt.xlim(), plt.ylim()])]
plt.plot(lims, lims, 'k--', linewidth=1.5, label='본전 라인 (ROI 0%)')

plt.text(4.5, 9.0, "💰 저예산 초대박", color='goldenrod', fontweight='bold', fontsize=12)
plt.text(8.0, 5.0, "💸 고예산 대참사", color='red', fontweight='bold', fontsize=12)

plt.title('제작비 투입 대비 흥행 성과 분포 (Success Tier Analysis)', fontsize=16)
plt.xlabel('제작비 (Log Scale)', fontsize=12)
plt.ylabel('매출액 (Log Scale)', fontsize=12)
plt.legend(title='흥행 등급', loc='upper left')
plt.grid(True, alpha=0.3)

save_path2 = os.path.join(SAVE_DIR, '2_budget_revenue_scatter_status.png')
plt.savefig(save_path2)
print(f"   ✅ 등급별 산점도 저장 완료: {save_path2}")

# ==============================================================================
# [공통 전처리] 장르 데이터 분리 (Explode)
# ==============================================================================
print("\n>>> [장르 분석] 데이터 전처리 중...")

# 1. 장르 쪼개기
df_genres = df.assign(genre_list=df['genres'].str.split(', ')).explode('genre_list')

# 2. 표본이 적은 장르 제거 (50개 미만은 노이즈로 간주)
genre_counts = df_genres['genre_list'].value_counts()
major_genres = genre_counts[genre_counts >= 50].index
df_major = df_genres[df_genres['genre_list'].isin(major_genres)]

print(f"   -> 분석 대상 장르: {len(major_genres)}개")

# ==============================================================================
# 4. [분석 3] 장르별 평균 제작비 (Average Budget)
# ==============================================================================
print(">>> [시각화 3] 장르별 평균 제작비...")

avg_budget = df_major.groupby('genre_list')['budget'].mean().sort_values(ascending=False)

plt.figure(figsize=(14, 7))
sns.barplot(x=avg_budget.values, y=avg_budget.index, palette='Reds_r')

plt.title('장르별 평균 제작비 순위 (Average Budget)', fontsize=15)
plt.xlabel('평균 제작비 ($)')
plt.ylabel('장르')
plt.grid(axis='x', alpha=0.3)

for i, v in enumerate(avg_budget.values):
    plt.text(v, i, f" ${v/1000000:.1f}M", va='center', fontsize=10)

save_path3 = os.path.join(SAVE_DIR, '3_genre_avg_budget.png')
plt.savefig(save_path3)
plt.close()

# ==============================================================================
# 5. [분석 4] 장르별 평균 수익률 (Average ROI)
# ==============================================================================
print(">>> [시각화 4] 장르별 평균 수익률...")

avg_roi = df_major.groupby('genre_list')['roi_ratio'].mean().sort_values(ascending=False)

plt.figure(figsize=(14, 7))
sns.barplot(x=avg_roi.values, y=avg_roi.index, palette='Greens_r')

plt.axvline(0, color='black', linestyle='--', linewidth=1, label='손익분기점')
plt.title('장르별 평균 투자 수익률 순위 (Average ROI)', fontsize=15)
plt.xlabel('평균 수익률 (배수, 1.0 = 100% 이익)')
plt.ylabel('장르')
plt.grid(axis='x', alpha=0.3)

for i, v in enumerate(avg_roi.values):
    plt.text(v, i, f" {v*100:.0f}%", va='center', fontsize=10, fontweight='bold')

save_path4 = os.path.join(SAVE_DIR, '4_genre_avg_roi.png')
plt.savefig(save_path4)
plt.close()

# ==============================================================================
# 6. [분석 5] 장르별 평균 매출액 (Revenue)
# ==============================================================================
print(">>> [시각화 5] 장르별 평균 매출액...")

avg_revenue = df_major.groupby('genre_list')['revenue'].mean().sort_values(ascending=False)

plt.figure(figsize=(14, 7))
sns.barplot(x=avg_revenue.values, y=avg_revenue.index, palette='Blues_r')

plt.title('장르별 평균 매출액 순위 (Average Revenue)', fontsize=15)
plt.xlabel('평균 매출액 ($)')
plt.ylabel('장르')
plt.grid(axis='x', alpha=0.3)

for i, v in enumerate(avg_revenue.values):
    plt.text(v, i, f" ${v/1000000:.1f}M", va='center', fontsize=10, fontweight='bold')

plt.savefig(os.path.join(SAVE_DIR, '5_genre_avg_revenue.png'))
plt.close()

# ==============================================================================
# 7. [분석 6] 장르별 평균 평점 (Average Rating) - NEW!
# ==============================================================================
print(">>> [시각화 6] 장르별 평균 평점(Rating) 분석 중...")

# 평점 높은 순 정렬
avg_rating = df_major.groupby('genre_list')[RATING_COL].mean().sort_values(ascending=False)

plt.figure(figsize=(14, 7))
# 보라색 계열(Purples_r) 사용
sns.barplot(x=avg_rating.values, y=avg_rating.index, palette='Purples_r')

plt.title(f'장르별 평균 평점 순위 ({RATING_COL})', fontsize=15)
plt.xlabel('평균 평점 (0~10)')
plt.ylabel('장르')
plt.grid(axis='x', alpha=0.3)

# 평점의 차이가 미세하므로 5.0부터 시작하도록 설정 (차이를 잘 보이게 하기 위함)
# 필요시 아래 줄을 주석 처리하면 0부터 시작합니다.
plt.xlim(5.0, 8.0) 

# 값 표시
for i, v in enumerate(avg_rating.values):
    plt.text(v, i, f" {v:.2f}", va='center', fontsize=10, fontweight='bold')

save_path6 = os.path.join(SAVE_DIR, '6_genre_avg_rating.png')
plt.savefig(save_path6)
plt.close()
print(f"   ✅ 평균 평점 그래프 저장 완료: {save_path6}")

# ==============================================================================
# 8. [심화 분석] 장르 포지셔닝 맵 (ROI vs 평점 정규화)
# ==============================================================================
print("\n>>> [심화 분석] 장르별 ROI와 평점의 관계 분석 (Positioning Map)...")

# 1. 장르별 데이터 집계
genre_metrics = df_major.groupby('genre_list').agg({
    'roi_ratio': 'mean',
    RATING_COL: 'mean'  # 위에서 설정한 vote_average
}).reset_index()

# 2. 정규화 (Standardization / Z-score)
# (값 - 평균) / 표준편차 => 0이면 딱 평균, 1이면 평균보다 1표준편차만큼 높음
genre_metrics['norm_roi'] = (genre_metrics['roi_ratio'] - genre_metrics['roi_ratio'].mean()) / genre_metrics['roi_ratio'].std()
genre_metrics['norm_rating'] = (genre_metrics[RATING_COL] - genre_metrics[RATING_COL].mean()) / genre_metrics[RATING_COL].std()

# 3. 시각화
plt.figure(figsize=(12, 10))

# 산점도 그리기
sns.scatterplot(
    data=genre_metrics, 
    x='norm_rating', 
    y='norm_roi', 
    s=150, 
    color='purple',
    alpha=0.7,
    edgecolor='w'
)

# 4. 4분면 기준선 (평균 = 0)
plt.axvline(0, color='gray', linestyle='--', linewidth=1)
plt.axhline(0, color='gray', linestyle='--', linewidth=1)

# 5. 각 포인트에 장르 이름 달기
# 겹침 방지를 위해 약간의 오프셋을 줌
for i in range(genre_metrics.shape[0]):
    plt.text(
        genre_metrics.norm_rating[i] + 0.02, 
        genre_metrics.norm_roi[i] + 0.02, 
        genre_metrics.genre_list[i], 
        fontsize=11, 
        fontweight='bold',
        color='black'
    )

# 6. 4분면 해석 텍스트 추가
plt.text(1.5, 1.5, "💎 흥행 & 비평 성공\n(Masterpieces)", fontsize=12, color='blue', ha='center', bbox=dict(facecolor='white', alpha=0.7))
plt.text(-1.5, 1.5, "💸 가성비 킹\n(Cash Cows)", fontsize=12, color='green', ha='center', bbox=dict(facecolor='white', alpha=0.7))
plt.text(1.5, -1.5, "🎨 비평적 성공\n(Critically Acclaimed)", fontsize=12, color='orange', ha='center', bbox=dict(facecolor='white', alpha=0.7))
plt.text(-1.5, -1.5, "💣 위험군\n(High Risk)", fontsize=12, color='red', ha='center', bbox=dict(facecolor='white', alpha=0.7))

plt.title('장르 포지셔닝 맵: 평점(Quality) vs 수익률(Profitability)', fontsize=16)
plt.xlabel(f'표준화된 평점 (Z-Score Rating) \n ← 평균 이하 | 평균 이상 →', fontsize=12)
plt.ylabel(f'표준화된 수익률 (Z-Score ROI) \n ← 평균 이하 | 평균 이상 →', fontsize=12)
plt.grid(True, alpha=0.3)

save_path7 = os.path.join(SAVE_DIR, '7_genre_positioning_map.png')
plt.savefig(save_path7)
print(f"   ✅ 포지셔닝 맵 저장 완료: {save_path7}")

# ==============================================================================
# 9. [검증 분석] 평점 효과를 제거한 장르별 '순수 흥행력' (잔차 분석)
# ==============================================================================
print(">>> [검증 분석] 평점(Rating) 영향력을 제거한 순수 ROI 효율성 분석 중...")

# 1. 데이터 준비 (유효한 데이터만 필터링)
df_clean = df.dropna(subset=[RATING_COL, 'roi_ratio'])
df_clean = df_clean[df_clean['roi_ratio'] < 50] # 극단적인 이상치(50배 수익 등) 일부 제외하여 추세선 안정화

# 2. 회귀분석 수행 (전체 영화 대상)
# "평점이 오르면 ROI도 오른다"는 전반적인 경향성을 계산
slope, intercept, r_value, p_value, std_err = stats.linregress(df_clean[RATING_COL], df_clean['roi_ratio'])

print(f"   -> 전체 추세: 평점 1점 오를 때마다 ROI는 약 {slope:.2f}배 증가하는 경향이 있음.")

# 3. '예측된 ROI'와 '실제 ROI'의 차이(잔차) 계산
# 잔차(Residual) = 실제 ROI - (평점 기반 예측 ROI)
# 양수면: 평점 대비 돈을 더 잘 번 것 (Over-performer)
# 음수면: 평점 대비 돈을 못 번 것 (Under-performer)
df_clean['predicted_roi'] = df_clean[RATING_COL] * slope + intercept
df_clean['roi_residual'] = df_clean['roi_ratio'] - df_clean['predicted_roi']

# 4. 장르별로 잔차 평균 내기
# (장르 분리 작업)
df_res_genres = df_clean.assign(genre_list=df_clean['genres'].str.split(', ')).explode('genre_list')

# 표본 적은 장르 제거
genre_counts = df_res_genres['genre_list'].value_counts()
major_genres = genre_counts[genre_counts >= 50].index
df_res_major = df_res_genres[df_res_genres['genre_list'].isin(major_genres)]

# 잔차 평균 계산 및 정렬
avg_residual = df_res_major.groupby('genre_list')['roi_residual'].mean().sort_values(ascending=False)

# 5. 시각화 (Diverging Bar Chart)
plt.figure(figsize=(14, 8))

# 색상 설정: 0보다 크면 빨강(흥행력 굿), 작으면 파랑(흥행력 배드)
colors = ['#ff4d4d' if x > 0 else '#4da6ff' for x in avg_residual.values]

sns.barplot(x=avg_residual.values, y=avg_residual.index, palette=colors)

# 기준선
plt.axvline(0, color='black', linewidth=1.5)

plt.title('평점 효과를 제거한 장르별 "순수 흥행 효율" (Residual Analysis)\n(0 = 평점만큼 벌었다 / 양수 = 평점보다 더 벌었다)', fontsize=16)
plt.xlabel('평균 잔차 (Actual ROI - Predicted ROI based on Rating)', fontsize=12)
plt.ylabel('장르')
plt.grid(axis='x', alpha=0.3, linestyle='--')

# 값 표시
for i, v in enumerate(avg_residual.values):
    offset = 0.1 if v >= 0 else -0.1
    ha = 'left' if v >= 0 else 'right'
    plt.text(v + offset, i, f"{v:.2f}", va='center', ha=ha, fontsize=10, fontweight='bold')

# 설명 박스
plt.text(max(avg_residual.values)*0.7, len(avg_residual)*0.8, 
         "🟥 오른쪽: 평점이 낮아도 수익이 잘 나는 장르\n(가성비/상업성 높음)\n\n🟦 왼쪽: 평점은 높지만 수익은 그만큼 안 나는 장르\n(작품성 위주/상업성 낮음)", 
         bbox=dict(facecolor='white', alpha=0.9, edgecolor='gray'))

save_path8 = os.path.join(SAVE_DIR, '8_genre_residual_efficiency.png')
plt.savefig(save_path8)
print(f"   ✅ 순수 흥행 효율 그래프 저장 완료: {save_path8}")
print("-" * 50)
# ==============================================================================
# [분석] 평점 vs ROI 추세선 시각화
# ==============================================================================
print(">>> [시각화] 평점과 ROI의 상관관계 및 추세선 그리는 중...")

# 1. 데이터 전처리
# - 평점과 ROI가 있는 데이터만 추출
# - 시각화의 왜곡을 막기 위해 ROI 극단값(50배 이상)은 제외 (필요에 따라 조절 가능)
df_clean = df.dropna(subset=[RATING_COL, 'roi_ratio'])
df_viz = df_clean[df_clean['roi_ratio'] < 50].copy()

# 2. 선형 회귀 분석 (추세선 계산)
slope, intercept, r_value, p_value, std_err = stats.linregress(df_viz[RATING_COL], df_viz['roi_ratio'])

# 회귀식 문자열 생성 (y = ax + b)
line_eq = f"Trend Line: y = {slope:.2f}x {intercept:+.2f}"
r_sq_text = f"R² = {r_value**2:.3f}"

print(f"   -> 회귀 분석 결과: {line_eq}, {r_sq_text}")

# 3. 시각화
plt.figure(figsize=(12, 8))

# (1) 산점도 그리기 (데이터 분포)
sns.scatterplot(
    data=df_viz,
    x=RATING_COL,
    y='roi_ratio',
    alpha=0.2,       # 점을 투명하게 해서 밀집도 표현
    color='steelblue',
    s=30,
    label='개별 영화'
)

# (2) 추세선 그리기
x_vals = np.array(plt.xlim()) # 현재 x축 범위 가져오기
y_vals = intercept + slope * x_vals
plt.plot(x_vals, y_vals, color='red', linewidth=2, label='추세선 (Trend Line)')

# (3) 그래프 꾸미기
plt.title(f'영화 평점과 흥행 수익률(ROI)의 관계\n({line_eq})', fontsize=16)
plt.xlabel('평점 (Vote Average)', fontsize=12)
plt.ylabel('투자 수익률 (ROI Ratio)', fontsize=12)

# 추세선 정보 텍스트 박스 추가
plt.text(
    x=df_viz[RATING_COL].min(), 
    y=df_viz['roi_ratio'].max() * 0.9, 
    s=f"{line_eq}\n{r_sq_text}\n(P-value: {p_value:.4f})",
    fontsize=12,
    bbox=dict(facecolor='white', alpha=0.9, edgecolor='red', boxstyle='round')
)

plt.legend()
plt.grid(True, alpha=0.3)

# 4. 저장
save_path = os.path.join(SAVE_DIR, '9_rating_roi_trendline.png')
plt.savefig(save_path)
print(f"   ✅ 추세선 그래프 저장 완료: {save_path}")