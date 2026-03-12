# План Інтеграції NVIDIA AI

## Мета
Інтегрувати реальний AI (NVIDIA API) з `ai_orchestrator` для аналізу тональності коментарів та генерації чернеток відповідей.

## Покроковий Чек-лист:

1.  **Визначення роутів та сервісів**: Переглянути `INTERNAL_API.md` та `PROJECT_PLAN.md` для ідентифікації всіх необхідних API-роутів та бекенд-сервісів, які взаємодіятимуть з NVIDIA API.
    *   **Знайдені роути (з `INTERNAL_API.md`):**
        *   `POST /api/comments/analyze`: Внутрішній виклик методу LangChain `.chatWithTools()`, який аналізує тональність зібраних коментарів і генерує чернетку відповіді, зберігаючи її в БД.
        *   `GET /api/ai/providers`: Отримання списку доступних провайдерів (NVIDIA, Anthropic) з таблиці `ai_providers`.
        *   `GET /api/ai/models`: Отримання списку моделей, які підтримують необхідні функції (наприклад, `supports_tools: true`).
        *   `POST /api/tenant/ai-configs`: Збереження або оновлення унікального системного промпту та вибору моделі для конкретного клієнта (`tenant_id`) та конкретної задачі (`use case`) в таблиці `tenant_ai_configs`.

2.  **Конфігурація провайдерів**: Переконатися, що NVIDIA AI провайдер правильно налаштований у системі (якщо необхідно, додати записи до таблиці `ai_providers` та `tenant_ai_configs`).
    *   `PROJECT_PLAN.md` згадує: "AI Integration: 🟡 Частково (оркестратор готовий, потрібна підключення NVIDIA)".
    *   `README.md` згадує: "Configure AI providers via `/api/ai/providers` API".

3.  **Оновлення `ai_orchestrator.py`**: Модифікувати `social-media-analytics-platform/examples/ai_orchestrator.py` для використання NVIDIA API. Це включає:
    *   Ініціалізацію клієнта NVIDIA API.
    *   Реалізацію логіки для аналізу тональності (`analyze_sentiment`).
    *   Реалізацію логіки для генерації чернеток відповідей (`generate_draft_response`).
    *   Обробку можливих помилок та відмов (failover).
    *   Використання шифрування для API ключів (AES-256-GCM), як зазначено в `PROJECT_PLAN.md` та `README.md`.

4.  **Інтеграція з `api/approval/routes.py`**: Переконатися, що `POST /api/comments/analyze` викликає оновлений `ai_orchestrator.py` для обробки коментарів.

5.  **Тестування**: Створити або оновити тест-кейси для перевірки інтеграції NVIDIA AI, включаючи:
    *   Точність аналізу тональності (Test Case 1 з `API_PLATFORMS.md`).
    *   Генерацію чернеток відповідей (Test Case 3 з `API_PLATFORMS.md`).
    *   Захист від автопублікації (Approval Workflow, Test Case 2 з `API_PLATFORMS.md`).

6.  **Моніторинг та Логування**: Забезпечити адекватне логування викликів до NVIDIA API та відповідей, як зазначено в `PROJECT_PLAN.md` (Моніторинг аномалій).

7.  **Оновлення документації**: Оновити `PROJECT_PLAN.md` та `INTERNAL_API.md` після завершення інтеграції.
