"""Custom exceptions for economista."""


class EconomistaError(Exception):
    """Base exception for economista."""


class SourceError(EconomistaError):
    """Base exception for external data source errors."""


class CredentialsError(SourceError):
    """Raised when a source requires invalid or missing credentials."""


class RateLimitError(SourceError):
    """Raised when a source rate limit is reached."""


class SourceUnavailableError(SourceError):
    """Raised when an external source is unavailable."""


class IndicatorNotFoundError(SourceError):
    """Raised when an indicator cannot be found."""


class DatasetNotFoundError(SourceError):
    """Raised when a dataset cannot be found."""


class SchemaValidationError(EconomistaError):
    """Raised when data does not match the expected schema."""


class UnsupportedFrequencyError(EconomistaError):
    """Raised when a requested frequency is unsupported."""


class MetadataError(EconomistaError):
    """Raised when metadata is invalid or incomplete."""


class AnalysisError(EconomistaError):
    """Raised when an analysis operation fails."""


class ConfigurationError(EconomistaError):
    """Raised when configuration is invalid."""
