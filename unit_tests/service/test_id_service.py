import pytest
from db_client.errors import ValidationError
from app.service import id


@pytest.mark.parametrize(
    "import_id",
    [
        "A.B.C.D",
        "A012345.B012345.C012345.D012345",
        "A-1.B-1.C-1.D-1",
        "A_1.B_2.C_2.D_2",
    ],
)
def test_valid_ids(import_id: str):
    assert id.validate(import_id) is None


@pytest.mark.parametrize(
    "import_id",
    [
        "A.B.C",
        "A.B",
        "anything",
        "a#1.b.c.d",
    ],
)
def test_invalid_ids(import_id: str):
    with pytest.raises(ValidationError) as e:
        id.validate(import_id)
    expected_msg = f"The import id {import_id} is invalid!"
    assert e.value.message == expected_msg
