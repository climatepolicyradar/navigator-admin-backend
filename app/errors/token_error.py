class TokenError(Exception):
    """Raised when there is an error encoding/decoding the token."""

    @property
    def message(self) -> str:
        """
        Returns the message for the exception.

        :return str: The message string.
        """
        return self.args[0]
