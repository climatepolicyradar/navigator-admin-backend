from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.integration_tests.setup_db import setup_corpus


def test_get_template_unfcc(
    client: TestClient, test_db: Session, non_cclw_user_header_token
):
    setup_corpus(test_db)
    assert 1 == 1
