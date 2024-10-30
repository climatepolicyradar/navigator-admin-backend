import uuid
from unittest.mock import patch

import pytest

from app.repository.helpers import generate_unique_slug


def test_successfully_generates_a_slug_with_a_four_digit_suffix():
    title = "Test title"
    generated_slug = generate_unique_slug(set(), title)

    expected_slugified_title = "test-title_"
    expected_suffix_length = 4

    assert expected_slugified_title in generated_slug
    assert len(expected_slugified_title) + expected_suffix_length == len(generated_slug)


def test_successfully_generates_a_unique_slug_if_one_already_exists():
    title = "Test title"

    existing_slug = generate_unique_slug(set(), title)
    existing_suffix = existing_slug.split("_")[1]

    with patch(
        "app.repository.helpers.uuid4",
        side_effect=[existing_suffix, uuid.uuid4],
    ):
        generated_slug = generate_unique_slug({existing_slug}, title)

    assert existing_slug != generated_slug


def test_raises_error_if_a_unique_slug_cannot_be_created_in_a_specified_number_of_attempts():
    title = "Test title"

    existing_slug = generate_unique_slug(set(), title)
    existing_suffix = existing_slug.split("_")[1]

    with (
        patch(
            "app.repository.helpers.uuid4",
            return_value=existing_suffix,
        ),
        pytest.raises(RuntimeError),
    ):
        generate_unique_slug({existing_slug}, title, 2)
