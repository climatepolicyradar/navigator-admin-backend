# <!-- please update this list in the Readme "Global dependencies" list if you add others
GLOBAL_DEPENDENCIES = trunk poetry aws docker

# --- Setup --- #
bootstrap: bootstrap_check_dependencies bootstrap_configure_pyright

bootstrap_check_dependencies:
	@for dep in $(GLOBAL_DEPENDENCIES); do \
		if ! command -v $${dep} &> /dev/null; then \
			echo "$${dep} is not installed. See readme for links to instructions."; \
			exit 1; \
		fi \
	done

bootstrap_configure_pyright:
	trunk actions run configure-pyright


# --- Dev ---#
dev: dev_rds_dump
	docker-compose -f docker-compose-dev.yml up

dev_rds_dump:
	[ ! -f ./dumps/navigator.sql ] && aws --profile staging s3 cp s3://cpr-staging-rds/dumps/navigator.sql ./dumps/ || echo 0

# this should only need to be run if there are significant schema changes
# TODO: make this a little more intelligent
dev_rds_dump_update:
	aws --profile staging s3 cp s3://cpr-staging-rds/dumps/navigator.sql ./dumps/navigator.sql


# --- Test --- #
# Run only unit tests (without Docker):
# - `make unit_tests`
# - `make unit_tests UNIT_TEST=tests/unit_tests/routers/ingest/test_bulk_ingest.py`
# - `make unit_tests UNIT_TEST='tests/unit_tests -k bulk_ingest'`
UNIT_TEST ?=tests/unit_tests/

# Run only integration tests (with Docker):
# - `make integration_tests`
# - `make integration_tests INTEGRATION_TEST=tests/integration_tests/collection`
# - `make integration_tests INTEGRATION_TEST='tests/integration_tests -k update'`
INTEGRATION_TEST ?=tests/integration_tests

test:
	$(MAKE) unit_tests UNIT_TEST="$(UNIT_TEST)"
	$(MAKE) integration_tests INTEGRATION_TEST="$(INTEGRATION_TEST)"

unit_tests:
	poetry run pytest --disable-warnings -vvv $(UNIT_TEST)

integration_tests:
	TEST="$(INTEGRATION_TEST)" docker-compose -f docker-compose-test.yml run --rm webapp

# --- CI --- #
build:
	docker build --tag navigator-admin-backend .

build_dev:
	docker compose build


# --- Clean --- #
clean:
	docker-compose -f docker-compose-dev.yml down
	docker-compose -f docker-compose-test.yml down
	rm ./dumps/navigator.sql

run: 
	docker compose -f docker-compose.yml up -d --remove-orphans

start: build_dev run
