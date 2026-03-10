"""
Automated script to set up NVIDIA provider, model, and tenant in Supabase.
"""
import os
from dotenv import load_dotenv
from supabase import create_client
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Load environment variables
load_dotenv()

# Get encryption key
encryption_key_b64 = os.getenv("ENCRYPTION_KEY")
if not encryption_key_b64:
    raise ValueError("ENCRYPTION_KEY not found in .env")

encryption_key = base64.b64decode(encryption_key_b64)

def encrypt(plaintext: str) -> str:
    """Encrypt API key using AES-256-GCM"""
    aesgcm = AESGCM(encryption_key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return base64.b64encode(nonce + ciphertext).decode()

# NVIDIA API key (test key provided by user)
nvidia_key = "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"
encrypted_nvidia = encrypt(nvidia_key)

print(f"🔐 Зашифрований NVIDIA ключ: {encrypted_nvidia[:20]}...")

# Connect to Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

# Add provider
provider_data = {
    "name": "nvidia",
    "display_name": "NVIDIA NIM",
    "base_url": "https://integrate.api.nvidia.com/v1",
    "api_key_encrypted": encrypted_nvidia,
    "is_enabled": True,
    "priority": 10
}

print("➕ Додаємо провайдера NVIDIA...")
result = supabase.table("ai_providers").insert(provider_data).execute()
print(f"✅ Провайдера додано: {result.data[0]['id']}")
provider_id = result.data[0]["id"]

# Add model
model_data = {
    "provider_id": provider_id,
    "model_id": "z-ai/glm4.7",
    "display_name": "GLM-4.7",
    "context_window": 128000,
    "max_tokens": 8192,
    "supports_functions": True,
    "supports_vision": False,
    "input_cost_per_1m": 0.50,
    "output_cost_per_1m": 1.50,
    "is_enabled": True
}

print("➕ Додаємо модель GLM-4.7...")
supabase.table("ai_models").insert(model_data).execute()
print("✅ Модель додано")

# Get or create tenant
print("🔍 Перевіряємо тенанта...")
tenant_check = supabase.table("tenants").select("id").eq("email", "roman@burluka.com").execute()
if tenant_check.data:
    tenant_id = tenant_check.data[0]["id"]
    print(f"✅ Tenant вже існує: {tenant_id}")
else:
    # Create new tenant
    tenant_data = {
        "name": "Roman Burluka",
        "email": "roman@burluka.com",
        "company_name": "Burluka Tech",
        "plan": "starter"
    }
    print("➕ Створюємо тенанта...")
    result = supabase.table("tenants").insert(tenant_data).execute()
    tenant_id = result.data[0]["id"]
    print(f"✅ Tenant створено: {tenant_id}")

# Add tenant AI config
config_data = {
    "tenant_id": tenant_id,
    "task_type": "comment_classification",
    "model_id": model_data["provider_id"],  # We need the model_id from the insert
    "system_prompt": "You are a helpful assistant that analyzes social media comments and classifies them into NPS categories.",
    "temperature": 0.7,
    "max_tokens": 1000,
    "is_active": True
}

# Get the actual model_id
model_result = supabase.table("ai_models").select("id").eq("model_id", "z-ai/glm4.7").eq("provider_id", provider_id).execute()
model_id = model_result.data[0]["id"]

config_data["model_id"] = model_id

print("➕ Налаштовуємо AI конфігурацію для тенанта...")
supabase.table("tenant_ai_configs").insert(config_data).execute()
print("✅ AI конфігурацію налаштовано")

print("\n🎉 Все готово! Інфраструктура повністю налаштована.")
print(f"📊 Провайдер ID: {provider_id}")
print(f"📊 Модель ID: {model_id}")
print(f"📊 Tenant ID: {tenant_id}")
