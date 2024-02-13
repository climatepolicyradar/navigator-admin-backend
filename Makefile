
bootstrap:
	- pyenv deactivate
	pyenv virtualenv 3.9 admin-backend
	pyenv activate admin-backend
	pip3 install poetry
	poetry install

git_hooks:
	# Install & run git pre-commit hooks
	poetry run pre-commit install --install-hooks
	pre-commit run --all-files

build_bats:
	docker build bats -t bats-with-helpers:latest

test_bashscripts: build_bats
	docker run --rm -v "${PWD}/.github:/code" bats-with-helpers:latest /code/tests/test_retag_and_push.bats

build:
	docker compose build

unit_test: build
	docker run --rm \
	-e SECRET_KEY="secret_test_key" \
	navigator-admin-backend pytest -vvv unit_tests

setup_test_db:
	@echo Setting up...
	-docker network create test-network
	-docker stop test_db
	@echo Starting Postgres...
	docker pull postgres:14
	docker run --rm -d -p 5432:5432 \
		--name test_db \
		--network=test-network \
		-v ${PWD}/integration_tests:/data-load \
		-e POSTGRES_PASSWORD=password \
		-e POSTGRES_USER=navigator \
		postgres:14 
	sleep 3

integration_test: build 
	@echo Assuming setup_test_db has already run.
	@echo Running tests...
	- docker stop admin
	docker run --rm \
		--name admin \
		--network=test-network \
		-e ADMIN_POSTGRES_HOST=test_db \
		-e SECRET_KEY="secret_test_key" \
		navigator-admin-backend \
		pytest -vvv integration_tests
	docker stop test_db

test: unit_test setup_test_db integration_test

migrations:
	- docker compose run --rm admin_backend python3 app/initial_data.py

run: 
	- docker-compose -f docker-compose.yml up -d --remove-orphans

start: build run migrations

start_local: build
	# - docker stop navigator-admin-backend
	docker run -p 8888:8888 \
	--name navigator-admin-backend \
	--network=navigator-backend_default \
	-e ADMIN_POSTGRES_HOST=backend_db \
	-e SECRET_KEY="secret_test_key" \
	-d navigator-admin-backend

restart:
	docker stop navigator-admin-backend && docker rm navigator-admin-backend && make start_local && docker logs -f navigator-admin-backend
