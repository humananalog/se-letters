"""Custom exceptions for the SE Letters project."""

from typing import Optional, Any


class SELettersError(Exception):
    """Base exception for all SE Letters errors."""

    def __init__(self, message: str, details: Optional[Any] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class ProcessingError(SELettersError):
    """Raised when document processing fails."""

    pass


class ValidationError(SELettersError):
    """Raised when data validation fails."""

    pass


class APIError(SELettersError):
    """Raised when API calls fail."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Any] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class ConfigurationError(SELettersError):
    """Raised when configuration is invalid."""

    pass


class EmbeddingError(SELettersError):
    """Raised when embedding operations fail."""

    pass


class FileProcessingError(ProcessingError):
    """Raised when file processing operations fail."""

    pass 


class PreviewGenerationError(ProcessingError):
    """Raised when preview generation fails."""

    pass 