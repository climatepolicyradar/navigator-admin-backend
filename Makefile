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

build:
	docker build -t navigator-admin-backend .

build_dev:
	docker compose build

unit_test:
	docker compose run --rm navigator-admin-backend pytest -vvv unit_tests

integration_test:
	docker compose run --rm navigator-admin-backend pytest -vvv integration_tests

test: unit_test integration_test

run: 
	docker-compose -f docker-compose.yml up -d --remove-orphans

start: build run 

show_logs: 
	- docker-compose logs -f
