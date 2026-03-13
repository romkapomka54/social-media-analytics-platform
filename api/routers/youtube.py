from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..services.youtube_service import YouTubeService
from ..core.config import settings

router = APIRouter(prefix="/youtube", tags=["youtube"])

class VideoRequest(BaseModel):
    video_id: str
    source_id: Optional[int] = 1  # За замовчуванням ID твого каналу

class VideoResponse(BaseModel):
    status: str
    video_id: str
    source_id: int
    total_comments: int
    saved_comments: int
    quota_used: int
    message: Optional[str] = None

@router.post("/collect-comments", response_model=VideoResponse)
async def collect_comments(request: VideoRequest):
    """
    Збирає всі коментарі з YouTube відео і зберігає в Supabase
    
    - **video_id**: ID YouTube відео (наприклад, "dQw4w9WgXcQ")
    - **source_id**: ID джерела з таблиці sources (за замовчуванням 1)
    
    Повертає статистику збору та використану квоту
    """
    try:
        # Ініціалізуємо сервіс з Supabase клієнтом
        youtube_service = YouTubeService(supabase_client=settings.supabase_client)
        
        # Збираємо та зберігаємо коментарі
        result = youtube_service.collect_and_save_all_comments(
            video_id=request.video_id,
            source_id=request.source_id
        )
        
        return VideoResponse(
            status="success",
            video_id=request.video_id,
            source_id=request.source_id,
            total_comments=result.get('total_comments', 0),
            saved_comments=result.get('saved_comments', 0),
            quota_used=result.get('quota_used', 0),
            message=f"✅ Зібрано та збережено {result.get('saved_comments', 0)} коментарів"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/video-info/{video_id}")
async def get_video_info(video_id: str):
    """
    Отримує базову інформацію про відео (назва, канал, кількість коментарів)
    """
    try:
        youtube_service = YouTubeService()
        
        # Отримуємо інформацію про відео
        request = youtube_service.service.videos().list(
            part='snippet,statistics',
            id=video_id
        )
        response = request.execute()
        
        if not response['items']:
            raise HTTPException(status_code=404, detail="Video not found")
        
        video = response['items'][0]
        snippet = video['snippet']
        stats = video['statistics']
        
        return {
            'video_id': video_id,
            'title': snippet['title'],
            'channel_title': snippet['channelTitle'],
            'channel_id': snippet['channelId'],
            'published_at': snippet['publishedAt'],
            'comment_count': stats.get('commentCount', 0),
            'view_count': stats.get('viewCount', 0),
            'like_count': stats.get('likeCount', 0)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
