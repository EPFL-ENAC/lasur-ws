build:
	poetry build

install:
	poetry install

update:
	poetry lock

test:
	poetry run pytest -s

run:
	poetry run uvicorn api.main:app

redis-up:
	docker compose up -d redis

redis-stop:
	docker compose stop redis

redis-down:
	docker compose down redis
