"""Domain exceptions raised by auth services — mapped to HTTP in endpoints."""


class EmailAlreadyRegisteredError(Exception):
    """Raised when a registration attempt uses an email that already exists."""

    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"Email '{email}' is already registered")
