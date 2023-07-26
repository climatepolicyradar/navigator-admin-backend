class RepositoryError(Exception):
    """Raised when something fails in the database."""

    @property
    def message(self) -> str:
        """
        Returns the message for the exception.

        :return str: The message string.
        """
        return self.args[0]
