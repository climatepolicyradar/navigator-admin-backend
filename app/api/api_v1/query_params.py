from typing import Union, cast

from fastapi import HTTPException, status


def get_query_params_as_dict(query_params) -> dict[str, Union[str, int]]:
    print(query_params)
    return {k: query_params[k] for k in query_params.keys()}


def set_default_query_params(
    query_params, default_query_term: str = "", default_max_results: int = 500
) -> dict[str, Union[str, int]]:
    query_fields = query_params.keys()

    if len(query_fields) < 1:
        return {"q": default_query_term, "max_results": default_max_results}

    if "max_results" not in query_fields:
        query_params["max_results"] = default_max_results
    return query_params


def validate_query_params(
    query_params, valid_params: list[str] = ["q", "max_results"]
) -> bool:
    query_fields = query_params.keys()
    invalid_params = [x for x in query_fields if x not in valid_params]
    if any(invalid_params):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Search parameters are invalid: {invalid_params}",
        )

    if not isinstance(query_params["max_results"], int):
        try:
            query_params.update({"max_results": cast(int, query_params["max_results"])})
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum results must be an integer value",
            )
    return True


def remove_query_params(
    query_params, params_to_remove: list[str]
) -> dict[str, Union[str, int]]:
    for param in params_to_remove:
        if all(k in query_params.keys() for k in ("q", param)):
            query_params.pop(param)

    return query_params
