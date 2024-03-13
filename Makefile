bootstrap:
	- pyenv deactivate
	pyenv virtualenv 3.9 admin-backend
	pyenv activate admin-backend
	pip3 install poetry
	poetry install

install_trunk:
	$(eval trunk_installed=$(shell trunk --version > /dev/null 2>&1 ; echo $$? ))
ifneq ($(trunk_installed),0)
	$(eval OS_NAME=$(shell uname -s | tr A-Z a-z))
ifeq ($(OS_NAME),linux)
	curl https://get.trunk.io -fsSL | bash
endif
ifeq ($(OS_NAME),darwin)
	brew install trunk-io
endif
endif

git_hooks: install_trunk
	trunk fmt
	trunk check

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
	docker compose -f docker-compose.yml up -d --remove-orphans

start: build_dev run

restart:
	docker stop navigator-admin-backend && docker rm navigator-admin-backend && make start && docker logs -f navigator-admin-backend


show_logs: 
	- docker compose logs -f
