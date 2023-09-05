class AuthenticationError(Exception):
    """Raised when authentication fails."""

    @property
    def message(self) -> str:
        """
        Returns the message for the exception.

        :return str: The message string.
        """
        return self.args[0]
