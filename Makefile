
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

test:
	docker run navigator-admin-backend pytest -vvv tests