# Test Approach

In the routers we mock the service to generate the different behaviours.

We then test that these behaviours (such as a db error) result in the correct HTTP response (in the case of a db error it should be a 503).

This ensures we are just unit testing the behaviour of the routers.