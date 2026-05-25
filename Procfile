web: uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT --workers 2 --proxy-headers --forwarded-allow-ips=*
worker: celery -A workers.celery_app.celery_app worker --loglevel=info --concurrency=2 --max-tasks-per-child=50
release: alembic upgrade head
