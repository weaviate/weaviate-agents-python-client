class QueryAgentError(Exception):
    """Exception raised for errors returned by the Query Agent API.

    Attributes:
        message: Human-readable error message from the API response.
        code: Machine-readable error code identifying the error type.
        details: Additional error context or details (may be empty).
        status_code: HTTP status code returned by the API.
    """

    def __init__(self, message: str, code: str, details: dict, status_code: int):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details
        self.status_code = status_code
