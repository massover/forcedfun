createdb:
	createuser -s forcedfun
	createdb forcedfun

dropdb:
	dropdb --if-exists test_forcedfun
	dropdb --if-exists test_forcedfun_gw0
	dropdb --if-exists test_forcedfun_gw1
	dropdb --if-exists test_forcedfun_gw2
	dropdb --if-exists test_forcedfun_gw3
	dropdb --if-exists test_forcedfun_gw4
	dropdb --if-exists test_forcedfun_gw5
	dropdb --if-exists test_forcedfun_gw6
	dropdb --if-exists test_forcedfun_gw7
	dropdb --if-exists test_forcedfun_gw8
	dropdb --if-exists test_forcedfun_gw9
	dropdb --if-exists forcedfun
	dropuser --if-exists forcedfun

migrate:
	uv run ./manage.py migrate

db: dropdb createdb migrate seeds

install:
	uv sync --all-groups

installci:
	uv sync --group test --group lint

test:
	uv run pytest

testlf:
	uv run pytest --lf

web:
	uv run ./manage.py runserver

fmt:
	uv run ruff format .
	uv run ruff check .

fmtci:
	uv run ruff format . --check
	uv run ruff check .

djade:
	git ls-files -z -- '*.html' | xargs -0 djade

run:
	docker run -it --entrypoint /bin/bash forcedfun:local

cov:
	uv run pytest tests/ --cov=forcedfun -v --durations=25
	uv run coverage report -m
	uv run coverage html
	open htmlcov/index.html

covci:
	uv run pytest tests/ --cov=forcedfun -v --durations=25 --cov-fail-under=100 --cov-report=term

build:
	docker build \
		  --progress=plain \
		  -t forcedfun:local \
		  --no-cache \
		  .
shell:
	uv run ./manage.py shell_plus

seeds:
	uv run ./manage.py seeds



mypy:
	uv run mypy forcedfun --strict

serve:
	uv run ./manage.py runserver