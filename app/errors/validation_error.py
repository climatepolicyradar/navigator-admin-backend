class ValidationError(Exception):
    """Raised when validation fails."""

    @property
    def message(self) -> str:
        """
        Returns the message for the exception.

        :return str: The message string.
        """
        return self.args[0]
