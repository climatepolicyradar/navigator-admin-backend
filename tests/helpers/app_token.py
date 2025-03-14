from datetime import datetime
from typing import Optional, cast

from dateutil.relativedelta import relativedelta
from pydantic import AnyUrl

from app.model.app_token import AppTokenCreateDTO

EXPIRE_AFTER_1_YEAR = 1
EXPIRE_AFTER_5_YEARS = 5
EXPIRE_AFTER_DEFAULT_YEARS = 10


def create_custom_app_create_dto(
    corpora_ids: Optional[list[str]] = None,
    theme: str = "TEST",
    hostname: str = "http://example.test.org",
    expiry_years: Optional[int] = EXPIRE_AFTER_DEFAULT_YEARS,
) -> AppTokenCreateDTO:
    if corpora_ids is None:
        corpora_ids = []

    return AppTokenCreateDTO(
        theme=theme,
        corpora_ids=corpora_ids,
        hostname=cast(AnyUrl, hostname),
        expiry_years=expiry_years,
    )


def timedelta_years(years, from_date=None):
    if from_date is None:
        from_date = datetime.now()
    return from_date - relativedelta(years=years)


def has_expected_keys(keys: list[str]) -> bool:
    return bool(
        set(keys)
        ^ {
            "allowed_corpora_ids",
            "exp",
            "iat",
            "aud",
            "iss",
            "sub",
        }
        == set()
    )
