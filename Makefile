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