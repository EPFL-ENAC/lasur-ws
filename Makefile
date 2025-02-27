build:
	poetry build

install:
	poetry install

update:
	poetry lock

test:
	poetry run pytest -s

run:
	poetry run uvicorn limnc_flaked.main:app --reload