class Account:
    def __init__(self, name: str) -> None:
        """A named account whose integer-cent balance starts at 0."""
        self.name = name
        self.balance: int = 0

    def apply(self, amount_cents: int) -> None:
        """Add the signed amount_cents to this account's balance.

        A positive amount credits the account; a negative amount debits it.
        Balances are plain Python ints (cents) — no floats anywhere.
        """
        self.balance += amount_cents
