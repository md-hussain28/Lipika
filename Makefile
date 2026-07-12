dev:
	uv run uvicorn src.main:app --reload --host 127.0.0.1 --port 8000

prod:
	uv run gunicorn -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000 src.main:app

migrate:
	uv run alembic upgrade head

migrate-down:
	uv run alembic downgrade -1

migration:
	uv run alembic revision --autogenerate -m "$(msg)"
