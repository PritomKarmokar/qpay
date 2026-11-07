from rest_framework import status
from rest_framework.response import Response

def error_response(
    code: str,
    message: str | dict,
    status_code: int = status.HTTP_400_BAD_REQUEST,
) -> Response:
    return Response(
        data={
            "error": {
                "code": code,
                "message": message,
            }
        },
        status=status_code,
    )

def success_response(
    data: dict,
    status_code: int = status.HTTP_200_OK,
) -> Response:

    return Response(
        data=data,
        status=status_code,
    )