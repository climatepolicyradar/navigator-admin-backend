class ExceptionWithMessage(Exception):
    """A base class for all errors with a message"""

    @property
    def message(self) -> str:
        """
        Returns the message for the exception.

        :return str: The message string.
        """
        return self.args[0] if len(self.args) > 0 else "<no message>"


class AuthenticationError(ExceptionWithMessage):
    """Raised when authentication fails."""

    pass


class RepositoryError(ExceptionWithMessage):
    """Raised when something fails in the database."""

    pass


class TokenError(ExceptionWithMessage):
    """Raised when there is an error encoding/decoding the token."""

    pass


class ValidationError(ExceptionWithMessage):
    """Raised when validation fails."""

    pass


class AuthorisationError(ExceptionWithMessage):
    """Raised when authentication fails."""

    pass
