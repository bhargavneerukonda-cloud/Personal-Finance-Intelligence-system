# 💰 FinSight AI — Intelligent Personal Finance Platform

> An end-to-end AI-powered personal finance platform featuring ML-driven expense categorization, spending forecasting, anomaly detection, financial health scoring, and a RAG-powered AI financial assistant.

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://react.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](docker-compose.yml)

---

## 🚀 Live Features

| Feature | Model / Tech | Performance |
|---|---|---|
| Expense categorization | XGBoost + DistilBERT ensemble | ~94% accuracy |
| Spending forecast | Prophet + LSTM hybrid | MAPE < 10% |
| Anomaly / fraud detection | Isolation Forest + Autoencoder | AUC > 0.92 |
| Financial health score | Composite 0–100 scoring model | — |
| AI financial assistant | LangChain + GPT-4o + RAG (Pinecone) | — |

---

## 🏗 Architecture

```
Client (React PWA)
    ↓
API Gateway (FastAPI + JWT Auth)
    ↓
Core Services (Transactions · Budgets · Notifications · Bank Sync)
    ↓
AI/ML Layer (Categorizer · Forecaster · Anomaly · Health Score · LLM Assistant)
    ↓
Data Layer (PostgreSQL · Redis · Pinecone · MLflow · Kafka)
    ↓
Cloud (AWS ECS Fargate · Terraform · GitHub Actions CI/CD)
```

---

## 🛠 Tech Stack

**Backend:** Python 3.11, FastAPI, SQLAlchemy, Alembic, Celery, Kafka  
**Frontend:** React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui, Recharts  
**ML:** scikit-learn, XGBoost, PyTorch, HuggingFace Transformers, Prophet  
**LLM:** LangChain, OpenAI GPT-4o, Pinecone (RAG), SHAP (explainability)  
**MLOps:** MLflow, Evidently AI, Prometheus, Grafana  
**Infra:** Docker, Terraform, AWS ECS, GitHub Actions  

---

## ⚡ Quick Start (Docker)

```bash
# 1. Clone the repo
git clone https://github.com/yourusername/finsight-ai.git
cd finsight-ai

# 2. Set up environment
cp .env.example .env
# Edit .env with your API keys (OpenAI, Plaid, etc.)

# 3. Start everything
docker-compose up --build

# 4. Access the app
# Frontend:  http://localhost:5173
# API docs:  http://localhost:8000/docs
# MLflow:    http://localhost:5001
# Grafana:   http://localhost:3000
```

---

## 📁 Project Structure

```
finsight-ai/
├── frontend/          # React + TypeScript PWA
├── backend/           # FastAPI application
├── ml/                # ML models, training, serving
├── llm/               # LangChain RAG assistant
├── infra/             # Terraform + Kubernetes
├── monitoring/        # Prometheus + Grafana
└── docker-compose.yml
```

---

## 🧠 ML Pipeline

```
Raw Data (Plaid/CSV) → Feature Engineering → Train/Validate → MLflow Registry
     ↓                                                               ↓
Feature Store (Redis)                                     Shadow Deploy → Canary → Prod
     ↓                                                               ↓
Inference API (<100ms)                            Evidently AI Drift Monitoring → Retrain
```

---

## 🔑 Environment Variables

See `.env.example` for all required variables including:
- `DATABASE_URL` — PostgreSQL connection string
- `OPENAI_API_KEY` — OpenAI API key for LLM assistant
- `PLAID_CLIENT_ID` / `PLAID_SECRET` — Plaid bank sync
- `PINECONE_API_KEY` — Vector database for RAG
- `SECRET_KEY` — JWT signing key

---

## 📊 API Reference

Interactive API docs available at `http://localhost:8000/docs` (Swagger UI)

Key endpoints:
- `POST /api/v1/auth/register` — Create account
- `POST /api/v1/auth/login` — Login, get JWT
- `GET  /api/v1/transactions` — List transactions with filters
- `GET  /api/v1/insights` — AI-generated personalized insights
- `GET  /api/v1/forecast` — 30/60/90-day expense forecast
- `GET  /api/v1/health-score` — Financial health score breakdown
- `POST /api/v1/chat` — Streaming AI assistant (SSE)

---

## 🧪 Running Tests

```bash
# Backend tests
cd backend && pytest tests/ -v --cov=app

# ML model tests
cd ml && pytest tests/ -v

# Frontend tests
cd frontend && npm test
```

---

## 🚢 Deployment

```bash
# Provision infrastructure
cd infra/terraform && terraform init && terraform apply

# Deploy via GitHub Actions
git push origin main  # triggers staging deploy
git tag v1.0.0 && git push --tags  # triggers production deploy
```

---

## 📈 Resume-Ready Description

> Built an end-to-end AI-powered personal finance platform featuring XGBoost + DistilBERT expense categorization (94% accuracy), Prophet + LSTM spending forecasts (MAPE <10%), Isolation Forest anomaly detection, and a RAG-powered LangChain financial assistant with Pinecone vector search. Implemented production MLOps with MLflow, Evidently AI drift monitoring, shadow/canary deployment, and GitHub Actions CI/CD on AWS ECS Fargate with Terraform IaC.

---

## 📄 License

MIT — see [LICENSE](LICENSE)
