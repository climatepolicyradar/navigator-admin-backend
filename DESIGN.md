# Design

Everything written here follows the "Strong opinions weakly held" principle.

The approach taken is influenced by:

- [The Twelve Factor App](https://12factor.net/)
- [SOLID principles](https://www.baeldung.com/solid-principles)
- [Domain Driven Design (DDD)](https://martinfowler.com/tags/domain%20driven%20design.html) particularly [folder structure](https://dev.to/stevescruz/domain-driven-design-ddd-file-structure-4pja)

## Overview

There are three main layers to the application:

- **Routing Layer** - The responsibility here is to manage the network payloads and any authentication middleware. All business logic is handed off to...
- **Service Layer** - Contains all validation and business logic for the application. This in turn uses the...
- **Repository Layer** - With the sole responsibility of managing how data is stored and retrieved to/from the database.
Note, this split into responsibilities for separate entities, should the need arise to create a transaction (for example creating two separate entities atomically) -
then this is the responsibility of the service layer to manage the transaction.

          Router
             │
             │
             ▼
          Service
             │
             │
     ┌───────┴───────┐
     │               │
     ▼               ▼
Repository ──────► Client
                   (ext)

## Testing Strategy

### Unit tests

- Routing Layer - this is tested my mocking out the required services by each individual route. The tests should alter how the service behaves to test out the routing layer responds.

- Service Layer - the required repositories are mocked out so that the tests can check the service returns/raises what is expected.

- Repository Layer - there are no unit tests.

### Integration tests

The strategy here is to test all the layers behave as expected.
This is done by creating a real test database and populating it with the expected schema (see `blank.sql`).

**NOTE** The database models are copied directly from the `navigator-backend` which has the responsibility for managing the database model and schemas. These model files and the empty schema should be kept in sync with the `navigator-backend`.
