"""Identity HTTP routes under /api/v1."""

from typing import Annotated

from fastapi import APIRouter, Depends

from lib_management.core.errors import ERROR_RESPONSES
from lib_management.identity.auth import Principal, authenticated
from lib_management.identity.schemas import AccountView, AuthContext

router = APIRouter(tags=["F16"])


@router.get(
    "/auth/me",
    operation_id="get_auth_me",
    response_model=AuthContext,
    responses={
        401: ERROR_RESPONSES[401],
        403: ERROR_RESPONSES[403],
        503: ERROR_RESPONSES[503],
    },
    openapi_extra={"x-account-guard": "ACTIVE", "x-functions": ["F16"]},
)
def get_auth_me(principal: Annotated[Principal, Depends(authenticated)]) -> AuthContext:
    """Session projection for menus; the API re-checks permissions per request."""
    return AuthContext(
        account=AccountView.model_validate(principal.account),
        permissions=sorted(principal.permissions),
    )
