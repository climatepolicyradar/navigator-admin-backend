#include .env
#include ./makefile-local.defs
#include ./makefile-docker.defs

bootstrap:
	- pyenv deactivate
	pyenv virtualenv 3.9 admin-backend
	pyenv activate admin-backend
	pip3 install poetry
	poetry install

git_hooks:
	# Install git pre-commit hooks
	poetry run pre-commit install --install-hooks
