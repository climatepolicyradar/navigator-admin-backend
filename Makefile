
bootstrap:
	- pyenv deactivate
	pyenv virtualenv 3.9 admin-backend
	pyenv activate admin-backend
	pip3 install poetry
	poetry install

git_hooks:
	# Install git pre-commit hooks
	poetry run pre-commit install --install-hooks

build_bats:
	docker build bats -t bats-with-helpers:latest

test_bashscripts: build_bats
	docker run --rm -v "${PWD}/.github:/code" bats-with-helpers:latest /code/tests/test_retag_and_push.bats

build:
	docker build -t navigator-admin-backend .

unit_test: build
	docker run --rm navigator-admin-backend pytest -vvv unit_tests

integration_test: build
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
	@echo Loading schema...
	docker exec test_db psql -U navigator -f /data-load/blank.sql > load_blank.txt
	docker exec test_db psql -U navigator -f /data-load/default-data.sql > load_default.txt
	@echo Running tests...
	docker run --rm \
		--network=test-network \
		-e ADMIN_POSTGRES_HOST=test_db \
		navigator-admin-backend \
		pytest -vvv integration_tests
	docker stop test_db

run: build
	docker run -p 8888:8888 -d navigator-admin-backend
