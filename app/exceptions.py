from fastapi import HTTPException, status


class NotFoundException(HTTPException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Not Found", "message": detail},
        )


class ValidationException(HTTPException):
    def __init__(self, detail: str = "Invalid input data"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Validation failed", "message": detail},
        )


class ExternalAPIException(HTTPException):
    def __init__(self, detail: str = "External API request failed"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "Service Unavailable", "message": detail},
        )
