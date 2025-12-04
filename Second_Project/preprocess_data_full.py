import pandas as pd
import os

# ==============================================================================
# [설정] 경로 지정
# ==============================================================================
BASE_DIR = r"C:\Users\anthony\Desktop\Univ Assingments\2025\DADV\DADV_repo\Second_Project"

INPUT_FILE = "tmdb_global_movies_massive.csv"   
OUTPUT_FILE = INPUT_FILE.replace(".csv", "_final.csv")   # 파일명 변경 (Final)

input_path = os.path.join(BASE_DIR, INPUT_FILE)
output_path = os.path.join(BASE_DIR, OUTPUT_FILE)

# ==============================================================================
# 1. 데이터 불러오기 및 정제
# ==============================================================================
print(f">>> [전처리 V2] 하이브리드 등급 분류를 시작합니다.")

if not os.path.exists(input_path):
    print("❌ 원본 파일이 없습니다.")
    exit()

df = pd.read_csv(input_path)

# 재무 데이터가 있는 것만 필터링 (제작비 $10,000 이상)
df_clean = df[(df['budget'] > 10000) & (df['revenue'] > 0)].copy()

# ==============================================================================
# 2. 파생 변수 및 등급 분류 (핵심!)
# ==============================================================================

# 2-1. 수익률 계산 (ROI)
# (매출 - 제작비) / 제작비
df_clean['roi_ratio'] = (df_clean['revenue'] - df_clean['budget']) / df_clean['budget']

# 2-2. 전체 매출 평균 계산 (규모 판단용 기준)
revenue_threshold = df_clean['revenue'].mean()
print(f"   -> Mega-Hit 판별을 위한 매출액 기준(평균): ${revenue_threshold:,.0f}")

# 2-3. 하이브리드 등급 분류 함수
def classify_hybrid(row):
    roi = row['roi_ratio']
    revenue = row['revenue']
    
    # 1. 쪽박 (적자)
    if roi < 0: 
        return 'Flop'
    
    # 2. 초대박 (Mega-Hit)
    # 조건: 제작비 4배 이상 벌고 AND 매출액도 평균 이상이어야 함
    # (작은 독립영화가 우연히 4배 번 것은 그냥 Hit로 처리)
    if roi >= 3.0 and revenue >= revenue_threshold:
        return 'Mega-Hit'
    
    # 3. 흥행 (Hit)
    # 조건: 제작비 2배 이상 (손익분기점 돌파)
    if roi >= 1.0: # roi 1.0은 2배 매출임 ( (200-100)/100 = 1.0 )
        return 'Hit'
        
    # 4. 평타 (Break-even)
    return 'Break-even'

df_clean['success_status'] = df_clean.apply(classify_hybrid, axis=1)

# ==============================================================================
# 3. 저장 및 결과 확인
# ==============================================================================
# 분석에 필요한 컬럼만
final_cols = [
    'id', 'title', 'release_date', 'genres', 'country',
    'budget', 'revenue', 'roi_ratio',
    'vote_average', 'vote_count', 'popularity',
    'success_status'
]

df_clean[final_cols].to_csv(output_path, index=False, encoding='utf-8-sig')

print("-" * 50)
print("📊 [등급 분류 결과]")
print(df_clean['success_status'].value_counts())
print("-" * 50)
print(f"✅ 저장 완료: {output_path}")