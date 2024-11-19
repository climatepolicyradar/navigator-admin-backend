install_trunk:
	$(eval trunk_installed=$(shell trunk --version > /dev/null 2>&1 ; echo $$? ))
ifneq (${trunk_installed},0)
	$(eval OS_NAME=$(shell uname -s | tr A-Z a-z))
	curl https://get.trunk.io -fsSL | bash
endif

uninstall_trunk:
	sudo rm -if `which trunk`
	rm -ifr ${HOME}/.cache/trunk

create_env:
	# Copy .env
	cp .env.example .env

configure_pyright:
	trunk actions run configure-pyright

setup_with_pyenv: install_trunk create_env ## Sets up a local dev environment using Pyenv
	$(eval venv_name=$(shell  grep 'venv =' pyproject.toml | cut -d '"' -f 2 ))
	if [ -n "$(venv_name)" ] && ! pyenv versions --bare | grep -q "^$(venv_name)$$"; then \
		$(eval python_version=$(shell grep 'python =' pyproject.toml | cut -d '"' -f 2 | sed 's/^\^//')) \
		$(eval pyenv_version=$(shell pyenv versions --bare | grep$(python_version) )) \
		pyenv virtualenv $(pyenv_version) $(venv_name); \
	fi
	@eval "$$(pyenv init -)" && \
	pyenv activate $(venv_name) && \
	poetry install

	make configure_pyright
	
check:
	trunk fmt
	trunk check

build:
	docker build -t navigator-admin-backend .

build_dev:
	docker compose build

unit_test: build
	docker compose run --rm navigator-admin-backend pytest -vvv tests/unit_tests

integration_test: build_dev
	docker compose run --rm navigator-admin-backend pytest -vvv tests/integration_tests

test: build_dev
	docker compose run --rm navigator-admin-backend pytest -vvv tests

test_local:
	poetry run pytest  -vvv tests/integration_tests

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
