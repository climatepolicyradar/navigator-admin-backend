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
# If you'd like to run more specific, you can run e.g.
# - `make test TEST=tests/integration_tests`
# - `make test TEST=tests/unit_tests`
# - `make test TEST=tests/integration_tests/ingest/test_ingest.py::test_ingest_when_ok`
#
# We've left it specifically unprefixed so autocomplete works in the terminal
override TEST ?=
test:
	TEST=$(TEST) docker-compose -f docker-compose-test.yml run --rm webapp

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
