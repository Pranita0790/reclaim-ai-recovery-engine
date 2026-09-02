import traceback

from fastapi import Request
from fastapi.responses import JSONResponse


# ==================================================
# BUSINESS VALIDATION ERROR
# ==================================================

class BusinessValidationError(Exception):
    """
    Custom exception for expected business validation errors.
    """

    def __init__(
        self,
        message: str,
        detail: str | None = None,
    ):
        self.message = message
        self.detail = detail

        super().__init__(message)


# ==================================================
# BUSINESS VALIDATION EXCEPTION HANDLER
# ==================================================

async def business_validation_exception_handler(
    request: Request,
    exc: BusinessValidationError,
):
    return JSONResponse(
        status_code=400,
        content={
            "error": "BUSINESS_VALIDATION_ERROR",
            "message": exc.message,
            "detail": exc.detail,
        },
    )


# ==================================================
# INTERNAL SERVER ERROR HANDLER
# ==================================================

async def internal_server_exception_handler(
    request: Request,
    exc: Exception,
):
    """
    Temporary development error handler.

    Prints the complete traceback in the backend terminal
    and returns the real error details in the API response.

    IMPORTANT:
    Do not expose full exception details like this in production.
    """

    # ----------------------------------------------
    # PRINT COMPLETE ERROR TO TERMINAL
    # ----------------------------------------------

    print("\n")
    print("=" * 100)
    print("UNEXPECTED BACKEND ERROR")
    print("=" * 100)

    print("\nREQUEST METHOD:")
    print(request.method)

    print("\nREQUEST URL:")
    print(request.url)

    print("\nEXCEPTION TYPE:")
    print(type(exc).__name__)

    print("\nEXCEPTION MESSAGE:")
    print(str(exc))

    print("\nFULL TRACEBACK:")
    print("-" * 100)

    traceback.print_exception(
        type(exc),
        exc,
        exc.__traceback__,
    )

    print("-" * 100)
    print("=" * 100)
    print("\n")

    # ----------------------------------------------
    # RETURN REAL ERROR TO FRONTEND / SWAGGER
    # ----------------------------------------------

    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": str(exc),
            "detail": {
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "request_method": request.method,
                "request_url": str(request.url),
                "traceback": traceback.format_exc(),
            },
        },
    )