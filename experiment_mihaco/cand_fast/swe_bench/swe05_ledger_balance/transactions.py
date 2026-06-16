"""transactions.py — Entry posting logic for the double-entry ledger.

The root cause of the known bug was here: entries with negative (debit)
amounts were silently dropped instead of being applied. This implementation
correctly applies EVERY entry unconditionally.
"""


def post_entries(entries, accounts) -> None:
    """Apply EVERY entry to its account.

    entries  : a list of (account_name: str, amount_cents: int) pairs with
               signed integer amounts (debit = negative, credit = positive).
    accounts : a dict mapping name -> Account.

    For each (name, amount) pair, call accounts[name].apply(amount).
    EVERY entry must be applied — both debits and credits.
    """
    for name, amount in entries:
        accounts[name].apply(amount)
