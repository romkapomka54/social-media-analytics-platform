#!/usr/bin/env python3
"""
Скрипт для ініціалізації бази даних Supabase
Створює необхідні таблиці та виконує миграції
"""

import os
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse

load_dotenv()

# Отримання URL з .env
SUPABASE_URL = os.getenv("SUPABASE_URL")
DATABASE_URL = os.getenv("DATABASE_URL")  # Для прямого з'єднання з PostgreSQL

def get_connection():
    """Створення з'єднання з PostgreSQL через DATABASE_URL"""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL не встановлено в .env")

    return psycopg2.connect(DATABASE_URL)

def execute_sql_file(filepath):
    """Виконує SQL файл"""
    with open(filepath, 'r') as f:
        sql = f.read()

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            conn.commit()
            print(f"✅ Успішно виконано: {filepath}")
    except Exception as e:
        conn.rollback()
        print(f"❌ Помилка при виконанні {filepath}: {e}")
        raise
    finally:
        conn.close()

def create_base_tables():
    """Створення базових таблиць tenants та users"""
    sql = """
    -- Таблиця тенантів (організацій)
    CREATE TABLE IF NOT EXISTS tenants (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );

    -- Таблиця користувачів
    CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
        email TEXT NOT NULL UNIQUE,
        name TEXT,
        role TEXT DEFAULT 'viewer', -- 'admin', 'analyst', 'viewer'
        created_at TIMESTAMP DEFAULT NOW()
    );

    COMMENT ON TABLE tenants IS 'Організації-клінти platform';
    COMMENT ON TABLE users IS 'Користувачі з ролями та привязкою до організацій';
    """

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            conn.commit()
            print("✅ Базові таблиці створено!")
    except Exception as e:
        conn.rollback()
        print(f"❌ Помилка при створенні базових таблиць: {e}")
        raise
    finally:
        conn.close()

def run_migrations():
    """Виконує всі миграції"""
    print("🦀 Починаємо ініціалізацію бази даних...")
    print()

    # Крок 1: Створення базових таблиць
    print("Крок 1/3: Створення базових таблиць...")
    create_base_tables()
    print()

    # Крок 2: Створення AI таблиць
    print("Крок 2/3: Створення AI таблиць...")
    execute_sql_file('supabase/01_ai_tables.sql')
    print()

    # Крок 3: Створення Approval Workflow таблиць
    print("Крок 3/3: Створення Approval Workflow таблиць...")
    execute_sql_file('supabase/02_approval_workflow.sql')
    print()

    print("🎉 База даних успішно ініціалізована!")
    print()
    print("Наступні кроки:")
    print("1. Запустіть FastAPI сервер: uvicorn api.main:app --reload")
    print("2. Відкрийте Swagger UI: http://localhost:8000/docs")
    print("3. Протестуйте ендпоінти Approval Workflow")

if __name__ == "__main__":
    run_migrations()
