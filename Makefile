.PHONY: dev test train deploy lint format

dev:
	docker-compose up --build

dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

test:
	cd backend && pytest tests/ -v --cov=app --cov-report=html
	cd frontend && npm test -- --run

test-ml:
	cd ml && pytest tests/ -v

lint:
	cd backend && ruff check app/ && mypy app/
	cd frontend && npm run lint

format:
	cd backend && ruff format app/
	cd frontend && npm run format

train:
	cd ml && python src/training/train_categorizer.py
	cd ml && python src/training/train_forecaster.py
	cd ml && python src/training/train_anomaly.py

migrate:
	cd backend && alembic upgrade head

migrate-create:
	cd backend && alembic revision --autogenerate -m "$(MSG)"

deploy-staging:
	./scripts/deploy.sh staging

deploy-prod:
	./scripts/deploy.sh production

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -name "*.pyc" -delete 2>/dev/null; true
