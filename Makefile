PATH  := $(PATH)
SHELL := /bin/bash

black:
	poetry run black .

ruff:
	poetry run ruff check . --fix

isort:
	poetry run isort .


lint:
	make black
	make ruff 

pre-commit:
	pre-commit run --all-files

test:
	poetry run pytest tests --color=yes
