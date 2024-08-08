import requests

import app.service.token as token_service

with open("tests/unit_tests/routers/ingest/test.json", "rb") as f:
    files = {"file": ("file.json", f, "application/json")}
    a_token = token_service.encode("cclw@cpr.org", 1, False, {"is_admin": True})
    headers = {"Authorization": f"Bearer {a_token}"}
    response = requests.post(
        "http://localhost:8888/api/v1/ingest",
        headers=headers,
        data='{"test": "test"}',
    )
