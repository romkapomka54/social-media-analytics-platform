import os
from dotenv import load_dotenv
from supabase import create_client

# Завантажуємо змінні з .env
load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

print(f"🔍 Перевіряємо підключення...")
print(f"URL: {url}")
print(f"Key: {key[:20]}... (приховано)")

if not url or not key:
    print("❌ Помилка: SUPABASE_URL або SUPABASE_SERVICE_ROLE_KEY не знайдено в .env")
    exit(1)

try:
    # Створюємо клієнт
    supabase = create_client(url, key)
    
    # Перевіряємо підключення
    response = supabase.table("tenants").select("*").limit(1).execute()
    
    print("✅ Успішно підключено до Supabase!")
    
except Exception as e:
    print(f"❌ Помилка підключення: {e}")
