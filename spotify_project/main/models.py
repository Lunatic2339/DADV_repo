from django.db import models
from django.contrib.auth.models import User



class Artist(models.Model):
    """
    Spotify 아티스트 정보를 저장하는 모델.
    Track 모델에서 참조하며, 장르 및 인기도 정보를 제공합니다.
    """
    # ----------------------------------------------------
    # 1. 고유 식별자 및 필수 정보 (Primary Key)
    # ----------------------------------------------------
    # ⭐ Primary Key: 아티스트의 Spotify ID를 기본 키로 설정합니다.
    spotify_id = models.CharField(max_length=50, primary_key=True) 
    
    # 아티스트 이름
    name = models.CharField(max_length=200) 
    
    # ----------------------------------------------------
    # 2. 시각화 및 분석 데이터 (필수)
    # ----------------------------------------------------
    # 아티스트의 공식 인기도 점수 (0-100)
    popularity = models.IntegerField(null=True, blank=True)
    
    # 팔로워 수 (데이터 분석에 유용)
    followers_total = models.IntegerField(null=True, blank=True)
    
    # ⭐ 장르 정보: 국적 추론 및 장르 시각화의 핵심 필드.
    genres = models.TextField(default='', blank=True, help_text="콤마로 구분된 장르 리스트") 
    
    # ----------------------------------------------------
    # (외부 URL 필드는 요구에 따라 제거됨)
    # ----------------------------------------------------

    class Meta:
        verbose_name = "Artist"
        verbose_name_plural = "Artists"

    def __str__(self):
        return self.name
    

class Track(models.Model):
    """
    사용자의 Top Track 데이터와 커스텀 순위를 저장하는 핵심 모델.
    """
    # ----------------------------------------------------
    # 1. Spotify 기본 정보 (사용자 요청 필드 포함)
    # ----------------------------------------------------
    # trackid
    spotify_id = models.CharField(max_length=50, primary_key=True) 
    # track name
    name = models.CharField(max_length=255)
    
    # track popularity
    popularity = models.IntegerField(null=True, blank=True)

    # track release year
    release_year = models.IntegerField(null=True, blank=True, help_text="트랙이 발매된 연도")

    # track duration (길이 정보)
    duration_ms = models.IntegerField(null=True, blank=True)
    
    # ⭐⭐⭐ 새로운 필드: track genre ⭐⭐⭐
    # 단일 장르 또는 콤마로 구분된 여러 장르를 저장하기 위해 TextField 사용
    genre = models.CharField(
        max_length=100,  # ⭐ 100자 정도면 단일 장르 이름을 저장하기에 충분합니다.
        default='', 
        blank=True, 
        help_text="Track의 대표 장르 (Artist의 첫 번째 장르)"
    )

    # ----------------------------------------------------
    # 2. 관계 설정 (ForeignKey)
    # ----------------------------------------------------
    
    # track artist (N:1 관계)
    artist = models.ForeignKey(
        Artist, 
        on_delete=models.CASCADE, 
        related_name='tracks'
    )
    
    # 사용자 연결: 이 Top Track이 어떤 User의 목록인지 식별 (N:1 관계)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='top_tracks'
    )
    
    # ----------------------------------------------------
    # 3. 과제 목표: 커스텀 순위
    # ----------------------------------------------------
    
    # ⭐ track ranking (과제 핵심) ⭐
    ranking = models.IntegerField(help_text="사용자 Top Tracks 목록에서의 순위 (1, 2, 3...)") 

    # ----------------------------------------------------
    # 4. 메타데이터 (순위 중복 방지)
    # ----------------------------------------------------
    class Meta:
        # 한 사용자는 동일한 순위를 두 번 가질 수 없도록 제약 조건 설정
        unique_together = ('user', 'ranking')
        ordering = ['user', 'ranking'] 

    def __str__(self):
        return f"[{self.ranking}] {self.name} ({self.genre})"

class SpotifyToken(models.Model):
    # Django의 사용자 모델과 1:1 연결. 실제 환경에서는 User 모델 사용 권장.
    # ⭐ Django User 모델과의 관계 설정 ⭐
    user = models.OneToOneField(User, on_delete=models.CASCADE,null=True, blank=True) 
    
    # user_id 필드는 이제 필요 없거나, Spotify ID를 별도로 저장할 수 있습니다.
    spotify_id = models.CharField(max_length=50, unique=True)
    
    access_token = models.CharField(max_length=500)
    refresh_token = models.CharField(max_length=500, null=True)
    expires_in = models.DateTimeField() # 토큰 만료 시각 (UTC)
    token_type = models.CharField(max_length=50)

    # ⭐ 이 두 필드를 추가해야 합니다.
    expires_in = models.IntegerField(default=3600)  # 토큰의 유효 시간 (초)
    expires_at = models.DateTimeField(null=True, blank=True) # 토큰 만료 시각 (실제 시각)

    def __str__(self):
        return self.user_id