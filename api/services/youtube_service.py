import os
import pickle
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from typing import List, Dict, Tuple
import logging
from datetime import datetime

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YouTubeService:
    def __init__(self, supabase_client=None):
        self.service = self._get_authenticated_service()
        self.quota_used = 0
        self.supabase = supabase_client
        
    def _get_authenticated_service(self):
        """Отримує аутентифікований сервіс YouTube"""
        creds = None
        token_path = 'token.pickle'
        client_secrets_path = 'client_secrets.json'

        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = Flow.from_client_secrets_file(
                    client_secrets_path,
                    scopes=['https://www.googleapis.com/auth/youtube.force-ssl']
                )
                flow.redirect_uri = 'http://localhost:8000/auth/google/callback'
                auth_url, _ = flow.authorization_url(prompt='consent')
                print('Перейдіть за цим посиланням для авторизації:', auth_url)
                code = input('Введіть код авторизації: ')
                flow.fetch_token(code=code)
                creds = flow.credentials

            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)

        return build('youtube', 'v3', credentials=creds)
    
    def collect_and_save_all_comments(self, video_id: str, source_id: int) -> Dict:
        """
        Збирає всі коментарі з відео і зберігає в Supabase
        """
        result = {
            'video_id': video_id,
            'source_id': source_id,
            'total_comments': 0,
            'saved_comments': 0,
            'top_level_comments': [],
            'all_comments_flat': [],
            'quota_used': 0
        }
        
        try:
            # Крок 1: Збираємо всі топ-рівневі коментарі
            top_comments, quota1 = self._collect_top_comments(video_id)
            result['quota_used'] += quota1
            logger.info(f"📊 Знайдено топ-коментарів: {len(top_comments)}")
            
            # Крок 2: Для кожного топ-коментаря збираємо відповіді і зберігаємо
            for top_comment in top_comments:
                # Зберігаємо топ-коментар
                saved_top = self._save_comment_to_supabase(top_comment, source_id, video_id, level=1)
                if saved_top:
                    result['saved_comments'] += 1
                    result['top_level_comments'].append(saved_top)
                    logger.info(f"✅ Збережено топ-коментар {top_comment.get('id') or top_comment.get('youtube_comment_id')}")
                
                # Якщо є відповіді, збираємо їх
                reply_count = top_comment.get('reply_count', 0)
                if reply_count > 0:
                    logger.info(f"📊 Збираємо {reply_count} відповідей для коментаря {top_comment.get('id')}")
                    replies, quota2 = self._collect_replies(top_comment['id'], video_id)
                    result['quota_used'] += quota2
                    
                    for reply in replies:
                        saved_reply = self._save_comment_to_supabase(
                            reply, source_id, video_id, 
                            level=2, parent_id=top_comment['id']
                        )
                        if saved_reply:
                            result['saved_comments'] += 1
                            logger.info(f"✅ Збережено відповідь {reply.get('id')}")
            
            result['total_comments'] = result['saved_comments']
            
            logger.info(f"✅✅✅ Зібрано та збережено {result['saved_comments']} коментарів")
            logger.info(f"💰 Використано квоти: {result['quota_used']} одиниць")
            
        except Exception as e:
            logger.error(f"❌ Помилка: {e}")
            result['error'] = str(e)
        
        return result
    
    def _collect_top_comments(self, video_id: str) -> Tuple[List[Dict], int]:
        """Збирає всі топ-рівневі коментарі з пагінацією"""
        comments = []
        quota = 0
        next_page_token = None
        page_count = 0
        
        while True:
            page_count += 1
            request = self.service.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=100,
                pageToken=next_page_token
            )
            response = request.execute()
            quota += 1
            
            for item in response['items']:
                comment = item['snippet']['topLevelComment']['snippet']
                parsed = self._parse_comment_data(
                    item['id'], 
                    comment, 
                    video_id,
                    reply_count=item['snippet']['totalReplyCount']
                )
                comments.append(parsed)
                logger.info(f"📝 Знайдено топ-коментар: {parsed['author_display_name']}")
            
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
        
        logger.info(f"📊 Топ-коментарі: {len(comments)} шт., сторінок: {page_count}")
        return comments, quota
    
    def _collect_replies(self, parent_id: str, video_id: str) -> Tuple[List[Dict], int]:
        """Збирає всі відповіді для конкретного коментаря"""
        replies = []
        quota = 0
        next_page_token = None
        page_count = 0
        
        try:
            while True:
                page_count += 1
                request = self.service.comments().list(
                    part='snippet',
                    parentId=parent_id,
                    maxResults=100,
                    pageToken=next_page_token
                )
                response = request.execute()
                quota += 1
                
                for item in response['items']:
                    comment = item['snippet']
                    parsed = self._parse_comment_data(
                        item['id'], 
                        comment, 
                        video_id,
                        parent_id=parent_id
                    )
                    replies.append(parsed)
                    logger.info(f"📝 Знайдено відповідь: {parsed['author_display_name']}")
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
                    
        except Exception as e:
            logger.error(f"Помилка збору відповідей для {parent_id}: {e}")
        
        logger.info(f"📊 Відповіді: {len(replies)} шт., сторінок: {page_count}")
        return replies, quota
    
    def _parse_comment_data(self, 
                           comment_id: str, 
                           snippet: Dict, 
                           video_id: str, 
                           reply_count: int = 0,
                           parent_id: str = None) -> Dict:
        """Парсить сирі дані з API в структурований формат"""
        author_channel_id = None
        if snippet.get('authorChannelId'):
            if isinstance(snippet['authorChannelId'], dict):
                author_channel_id = snippet['authorChannelId'].get('value')
            else:
                author_channel_id = snippet['authorChannelId']
        
        author_channel_url = None
        if author_channel_id:
            author_channel_url = f"https://www.youtube.com/channel/{author_channel_id}"
        
        return {
            'id': comment_id,
            'youtube_comment_id': comment_id,
            'youtube_video_id': video_id,
            'youtube_channel_id': author_channel_id,
            'youtube_parent_id': parent_id,
            'author_display_name': snippet.get('authorDisplayName'),
            'author_channel_url': author_channel_url,
            'author_profile_image_url': snippet.get('authorProfileImageUrl'),
            'comment_text': snippet.get('textDisplay'),
            'comment_text_original': snippet.get('textOriginal'),
            'published_at': snippet.get('publishedAt'),
            'like_count': snippet.get('likeCount', 0),
            'reply_count': reply_count
        }
    
    def _save_comment_to_supabase(self, 
                                  comment_data: Dict, 
                                  source_id: int, 
                                  video_id: str,
                                  level: int = 1,
                                  parent_id: str = None) -> Dict:
        """
        Зберігає коментар в Supabase з правильним ключем
        """
        if not self.supabase:
            logger.warning("⚠️ Supabase клієнт не підключено")
            return comment_data
        
        try:
            # Визначаємо правильний ID коментаря
            comment_id = comment_data.get('youtube_comment_id') or comment_data.get('id')
            if not comment_id:
                logger.error(f"❌ Немає ID для коментаря: {comment_data}")
                return comment_data
            
            data = {
                'source_id': source_id,
                'youtube_comment_id': comment_id,
                'youtube_video_id': video_id,
                'youtube_channel_id': comment_data.get('youtube_channel_id'),
                'youtube_parent_id': parent_id,
                'author_display_name': comment_data.get('author_display_name'),
                'author_channel_url': comment_data.get('author_channel_url'),
                'author_profile_image_url': comment_data.get('author_profile_image_url'),
                'comment_text': comment_data.get('comment_text'),
                'comment_text_original': comment_data.get('comment_text_original'),
                'published_at': comment_data.get('published_at'),
                'like_count': comment_data.get('like_count', 0),
                'comment_level': level
            }
            
            # Видаляємо None значення
            data = {k: v for k, v in data.items() if v is not None}
            
            result = self.supabase.table('comments').insert(data).execute()
            
            if result.data:
                logger.info(f"✅ Збережено коментар {comment_id} (рівень {level})")
                return result.data[0]
            else:
                logger.warning(f"⚠️ Не вдалося зберегти коментар {comment_id}")
                return comment_data
                
        except Exception as e:
            logger.error(f"❌ Помилка збереження коментаря {comment_id if 'comment_id' in locals() else 'unknown'}: {e}")
            return comment_data
