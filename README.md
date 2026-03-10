# Social Media Analytics Platform

This project aims to create a platform for analyzing comments and transcribing videos from social media platforms like YouTube, TikTok, and Instagram.

## 📚 Project Documentation

| File | Description |
|------|-------------|
| `ARCHITECTURE.md` | Full architecture of multi-LLM platform with LangChain |
| `INTERNAL_API.md` | Internal REST API documentation |
| `API_PLATFORMS.md` | Detailed analysis of social media platform APIs |
| `PROJECT_PLAN.md` | Development plan and roadmap |
| `CODING_GUIDELINES.md` | Python coding standards |
| `supabase/01_ai_tables.sql` | SQL schema for multi-LLM architecture |
| `examples/ai_orchestrator.py` | Example implementation of orchestrator with failover |

## 🚀 Quick Start

1. Set up Supabase and run SQL scripts from `supabase/`
2. Add `ENCRYPTION_KEY` environment variable for key encryption
3. Configure AI providers via `/api/ai/providers` API
4. Start the worker for comment collection

## 🔐 Security

- All API keys are encrypted with AES-256-GCM before storage
- Strict tenant isolation via `tenant_id` in every table
- Automatic failover when providers fail
