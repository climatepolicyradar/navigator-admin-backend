# navigator-admin-backend

Backend for the Admin webapp

## Getting started

### Global dependencies

These are global tools and libraries that are required to run the backend:

<!-- trunk-ignore(markdownlint/MD013) -->
<!-- please update this list in the Makefile GLOBAL_DEPENDENCIES if you add others -->

- [trunk](https://docs.trunk.io/cli/install#using-curl)
- [poetry](https://python-poetry.org/docs/#installation)
- [awscli](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- [docker](https://docs.docker.com/desktop/)

If you have not run the bootstrap previously run:

```shell
    make bootstrap
```

### Development

To get a running version of the API on
[http://localhost:8888](http://localhost:8888) run:

```shell
    make dev
```

To run the test suite run:

```shell
    make test
```

To run a specific test suite run:

```shell
    # a specific suite
    make test TEST=tests/unit_tests/

    # a spcific file
    make test TEST=tests/unit_tests/routers/ingest/test_bulk_ingest.py

    # a specific function
    make test TEST=tests/unit_tests/routers/ingest/test_bulk_ingest.py::test_bulk_ingest
```

## Background

This repository along with the [frontend repository](https://github.com/climatepolicyradar/navigator-admin-frontend)
forms the necessary components that make up the Admin Pages/Interface/Service.
These pages will provide the ability to edit Documents, Families, Collections
and Events (DFCE).
At the moment an MVP is being worked on that will have limited functionality,
the specification can be found on the CPR notion pages here:
[MVP Admin Interface](https://www.notion.so/climatepolicyradar/MVP-Admin-Interface-bf253a7ab30b4779a846d4322ca4c3f3).
Also on the notion pages is the [Admin API Specification](https://www.notion.so/climatepolicyradar/Admin-API-Specification-2adecc8411324b8181e05184fc6a5431#8da09a31c3f244e6a5acfacc9dfd9e2f).

## Issues / Progress

See [the linear project](https://linear.app/climate-policy-radar/project/admin-interface-2fbc66adc34c).

## Developers

If you are new to the repository, please ensure you read the [getting starting guide](GETTING_STARTED.md)
and the [design guide](DESIGN.md).

## Bulk Import

For the full procedure on how to do a bulk import of data see this [document](https://github.com/climatepolicyradar/bulk-import/blob/main/STANDARD_BULK_IMPORT_PROCEDURE.md).
