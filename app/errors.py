class ExceptionWithMessage(Exception):
    """A base class for all errors with a message."""

    @property
    def message(self) -> str:
        """
        Returns the message for the exception.

        Coerces the first argument to ``str`` so HTTP layers never receive
        a non-serialisable object (e.g. a wrapped ``NoResultFound``).

        :return str: The message string.
        """
        if len(self.args) == 0:
            return "<no message>"
        first = self.args[0]
        if isinstance(first, str):
            return first
        return str(first)


class AuthenticationError(ExceptionWithMessage):
    """Raised when authentication fails."""


class RepositoryError(ExceptionWithMessage):
    """Raised when something fails in the database."""


class ConflictError(ExceptionWithMessage):
    """Raised when entity already exists."""


class TokenError(ExceptionWithMessage):
    """Raised when there is an error encoding/decoding the token."""


class ValidationError(ExceptionWithMessage):
    """Raised when validation fails."""


class AuthorisationError(ExceptionWithMessage):
    """Raised when authentication fails."""


class PreSignedUrlError(ExceptionWithMessage):
    """Raised when there is an error generating a pre-signed URL."""
