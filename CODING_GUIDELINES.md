# 10. Модуль 10: Стандарти коду (Coding Guidelines)

Цей документ визначає стандарти кодування для Python-проекту, щоб забезпечити консистентність, читабельність та підтримуваність коду.

## 10.1. Форматування коду

| Правило | Стандарт | Джерело |
|---------|----------|---------|
| Відступи | 4 пробіли (не таби) | PEP 8 |
| Довжина рядка | До 88 символів (як у Black) | Black formatter |
| Імпорти | Групувати: stdlib → third-party → local, алфавітно | PEP 8 |
| Лапки для рядків | Подвійні лапки (") для консистентності | Project convention |

## 10.2. Найменування

| Елемент | Стиль | Приклад |
|---------|-------|---------|
| Класи | CapWords (PascalCase) | `NPSAnalyzer`, `CommentProcessor` |
| Функції/методи | `lower_case_with_underscores` | `calculate_nps()`, `fetch_comments()` |
| Змінні | `lower_case_with_underscores` | `promoter_count`, `detractor_score` |
| Константи | `UPPER_CASE_WITH_UNDERSCORES` | `MAX_RETRY_COUNT`, `API_TIMEOUT` |
| Приватні методи | `_single_leading_underscore` | `_validate_token()` |

## 10.3. Docstrings (Google Style)

```python
def analyze_sentiment(comment_text: str, model: str = "glm-4.7") -> dict:
    """
    Analyze comment sentiment and classify into NPS categories.

    Args:
        comment_text (str): Raw comment text from social media
        model (str, optional): AI model to use. Defaults to "glm-4.7"

    Returns:
        dict: Contains sentiment_score (0-10), category (promoter/neutral/detractor), 
              and confidence level

    Raises:
        ValueError: If comment_text is empty
        APIConnectionError: If NVIDIA API is unreachable

    Examples:
        >>> analyze_sentiment("This product is amazing!")
        {'score': 9, 'category': 'promoter', 'confidence': 0.95}
    """
    # Implementation here
```

## 10.4. Сучасний Python (3.10+)

| Фіча | Рекомендація | Приклад |
|------|--------------|---------|
| f-strings | Для простої інтерполяції | `f"User {user.name} left {comment_count} comments"` |
| Type Hints | Обов'язково для функцій | `def process(user_id: int) -> list[Comment]:` |
| Pattern Matching | Для складних умов | `match comment.category: case "promoter": ...` |
| Unpacking | Використовувати PEP 448 | `{**base_config, **user_config}` |

## 10.5. Специфіка для нашого проекту

### models.py (Fat models)

```python
# models.py (Fat models)
class Comment(models.Model):
    """Model for storing social media comments."""
    
    PLATFORM_CHOICES = {
        "ig": "Instagram",
        "yt": "YouTube",
        "fb": "Facebook",
        "tt": "TikTok",
    }
    
    NPS_CATEGORIES = {
        "promoter": "Promoter (9-10)",
        "neutral": "Neutral (7-8)",
        "detractor": "Detractor (0-6)",
    }

    # Database fields
    platform = models.CharField(max_length=2, choices=PLATFORM_CHOICES)
    text = models.TextField()
    nps_score = models.IntegerField(null=True, blank=True)
    nps_category = models.CharField(max_length=10, choices=NPS_CATEGORIES, null=True)
    sentiment_confidence = models.FloatField(default=0.0)
    
    # For approval workflow
    needs_review = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["platform", "created_at"]),
            models.Index(fields=["nps_category"]),
        ]

    def __str__(self):
        return f"[{self.platform}] {self.text[:50]}..."

    def calculate_nps_score(self):
        """Business logic in model, not view."""
        # Call NVIDIA API via OpenClaw
        result = analyze_with_nvidia(self.text)
        self.nps_score = result["score"]
        self.nps_category = result["category"]
        self.sentiment_confidence = result["confidence"]
        self.save()
        return result
```

### Ключові принципи

1. **Fat models, thin views**: Бізнес-логіка знаходиться в моделях, а не в views
2. **Type safety**: Всі функції мають type hints
3. **Docstrings**: Кожен публічний метод має docstring в Google style
4. **Testing**: Кожна функція має відповідні тест-кейси
5. **Error handling**: Використовувати специфічні винятки, не загальні `Exception`

### Приклад правильної структури файлу

```python
# imports (stdlib → third-party → local)
import os
import logging
from typing import Optional, List, Dict

import requests
from django.db import models

from .utils import analyze_with_nvidia
from .exceptions import APIConnectionError

# Constants
MAX_RETRY_COUNT = 3
API_TIMEOUT = 30

# Models
class Comment(models.Model):
    # ... implementation ...
    pass

# Services (business logic layer)
class NPSAnalyzer:
    def __init__(self, model: str = "glm-4.7"):
        self.model = model
        self.logger = logging.getLogger(__name__)
    
    def analyze(self, text: str) -> Dict:
        """Analyze sentiment of given text."""
        if not text:
            raise ValueError("Text cannot be empty")
        
        try:
            result = analyze_with_nvidia(text, self.model)
            return result
        except requests.RequestException as e:
            self.logger.error(f"API connection failed: {e}")
            raise APIConnectionError(f"Cannot connect to NVIDIA API: {e}")
```

---

**Час — гроші!** Дотримуйтесь цих стандартів, щоб зберегти код чистим, підтримуваним та ефективним. 🦀
