PATH  := $(PATH)
SHELL := /bin/bash

black:
	poetry run black .

ruff:
	poetry run ruff check . --fix

lint:
	make black
	make ruff

pre-commit:
	pre-commit run --all-files

test:
	poetry run pytest tests --color=yes
