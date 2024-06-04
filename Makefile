bootstrap:
	- pyenv deactivate
	pyenv virtualenv 3.9 admin-backend
	pyenv activate admin-backend
	pip3 install poetry
	poetry install

install_trunk:
	$(eval trunk_installed=$(shell trunk --version > /dev/null 2>&1 ; echo $$? ))
ifneq (${trunk_installed},0)
	$(eval OS_NAME=$(shell uname -s | tr A-Z a-z))
	curl https://get.trunk.io -fsSL | bash
endif

uninstall_trunk:
	sudo rm -if `which trunk`
	rm -ifr ${HOME}/.cache/trunk

git_hooks: install_trunk
	trunk actions run configure-pyright-with-pyenv
	
check:
	trunk fmt
	trunk check

build:
	docker build -t navigator-admin-backend .

build_dev:
	docker compose build

unit_test: build
	docker compose run --rm navigator-admin-backend pytest -vvv tests/unit_tests --cov=app --cov-fail-under=80 --cov-report=term --cov-report=html

integration_test: build_dev
	docker compose run --rm navigator-admin-backend pytest -vvv tests/integration_tests --cov=app --cov-fail-under=80 --cov-report=term --cov-report=html

test: build_dev
	docker compose run --rm navigator-admin-backend -- pytest -vvv tests --cov=app --cov-fail-under=80 --cov-report=term --cov-report=html

run: 
	docker compose -f docker-compose.yml up -d --remove-orphans

start: build_dev run

start_local: build
	# - docker stop navigator-admin-backend
	docker run -p 8888:8888 \
	--name navigator-admin-backend \
	--network=navigator-backend_default \
	-e ADMIN_POSTGRES_HOST=backend_db \
	-e SECRET_KEY="secret_test_key" \
	-d navigator-admin-backend

restart: build
	docker stop navigator-admin-backend && docker rm navigator-admin-backend && make start_local && docker logs -f navigator-admin-backend

show_logs: 
	- docker compose logs -f
