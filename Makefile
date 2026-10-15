build:
	uv build

install:
	uv sync

update:
	uv lock --upgrade

test:
	uv run pytest -s

run:
	uv run uvicorn --port 8001 api.main:app

redis-up:
	docker compose up -d redis

redis-stop:
	docker compose stop redis

redis-down:
	docker compose down redis

get-data:
	chmod +x ./scripts/generate_data.sh
	./scripts/generate_data.sh