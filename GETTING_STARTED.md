# Getting Started

## Environment

It is assumed that you have installed [`pyenv`](https://github.com/pyenv/pyenv) to manage your python environments locally.

Create a new environment and activate it whenever you work on the admin backend. This make command will use `pyenv` to create a new virtualenv called `admin-backend`:

```shell
make bootstrap
```

This can then be activated in any shell with `pyenv activate admin-backend`.

Also ensure that you have the git commit hooks installed to maintain code quality:

```shell
make git_hooks
```

## Running locally

With your environment correctly setup (see previous section), you can now run the backend locally using:

```shell
python app/main.py
```

**NOTE** if you get the error: `ModuleNotFoundError: No module named 'app'` you may need to add you current working directory to `PYTHONPATH`. You can do this by running `export PYTHONPATH=.` in the root folder of the repo.

This should run the app [locally on port 8888](http://0.0.0.0:8888) and the json logging should appear in the console.

## Building

This backend component is tested and deployed as a docker container. This container can be built and used locally with:

```shell
make build
```

This should generate a container image named `navigator-admin-backend`, this image can be run locally with:

```shell
make start
```

## Testing

### Unit Tests

These tests are designed not to require a database and therefore run quickly. These can be run locally with `pytest -vvv unit_tests` or from within the container using `make unit_test`. The second approach is preferred as this is how the tests run in the Github Actions CI pipeline.

### Integration Tests

These tests are designed to require a database and therefore will pull and run a postgres container. These can be run locally with `pytest -vvv integration_tests` - however this will require that you have spun up a local postgres instance (which can be done using `make setup_test_db`).

The preferred way it to use `make setup_test_db integration_tests` as this is how the tests run in the Github Actions CI pipeline. These commands were split so that the output of the integration tests is easier to read.

## Deploying

Currently the deployment is manual, this required the following steps:

- Create a new tagged release [here](https://github.com/climatepolicyradar/navigator-admin-backend/releases)
- Wait for the `semver` Action to run in github - this creates and pushes the image into ECR
- Log into the AWS console in the environment you wish to deploy.
- In AppRunner - find the running images and hit the `Deploy` button.

## Finally

Before reading or writing any code or submitting a PR, please read [the design guide](DESIGN.md)
