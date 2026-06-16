"""Grader for swe_bench/swe05_ledger_balance. Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.
The broken variant has transactions.post_entries silently DROP every entry with a
negative (debit) amount, so credits post but matching debits are ignored. The
ledger.py facade's validation still passes (it sums the original entries, which
balance), so the fault only surfaces when account balances / trial balance are
inspected — a multi-file fault-localisation symptom that crosses a module
boundary (observed in ledger.py, rooted in transactions.py).

Tests:
  PASS_TO_PASS (>=5) — do not depend on debits posting:
    1. test_add_account_and_zero_balance   — fresh account balance is 0
    2. test_duplicate_account_raises        — duplicate add raises ValueError
    3. test_unbalanced_entries_raise        — non-zero-sum entries raise ValueError
    4. test_missing_account_raises_keyerror — posting to absent account raises KeyError
    5. test_credit_only_account_posts       — a purely-credited account gets its credit
    6. test_balance_missing_account_keyerror — balance() of unknown account raises KeyError

  FAIL_TO_PASS (>=2) — require debits to post (broken variant fails these):
    7. test_transfer_debits_and_credits     — debited account goes negative, trial_balance==0
    8. test_multi_entry_balanced_posting     — multi-entry split, each balance correct, trial==0
    9. test_two_postings_accumulate          — sequential transfers accumulate, trial==0

  Advisory:
   10. test_code_quality_report
"""
from __future__ import annotations

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "swe_bench", "swe05_ledger_balance"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

# Load the facade module and the low-level transactions module separately (>=2 modules).
_ledger_mod = gu.load_module(SOL, "ledger.py", alias="ledger")
_txn_mod = gu.load_module(SOL, "transactions.py", alias="transactions")
_accounts_mod = gu.load_module(SOL, "accounts.py", alias="accounts")

Ledger = getattr(_ledger_mod, "Ledger")
post_entries = getattr(_txn_mod, "post_entries")
Account = getattr(_accounts_mod, "Account")


def _ledger_with(*names: str) -> "Ledger":
    """Build a Ledger with the given account names already added."""
    led = Ledger()
    for n in names:
        led.add_account(n)
    return led


# ===========================================================================
# PASS_TO_PASS tests — independent of debit (negative-amount) posting
# ===========================================================================

def test_add_account_and_zero_balance():
    """A freshly added account starts with a balance of exactly 0 cents."""
    led = _ledger_with("cash")
    assert led.balance("cash") == 0


def test_duplicate_account_raises():
    """Adding an account whose name already exists raises ValueError."""
    led = _ledger_with("cash")
    with pytest.raises(ValueError):
        led.add_account("cash")


def test_unbalanced_entries_raise():
    """Entries whose signed amounts do not sum to zero raise ValueError."""
    led = _ledger_with("A", "B")
    # -100 + 90 == -10 != 0
    with pytest.raises(ValueError):
        led.post([("A", -100), ("B", 90)])


def test_missing_account_raises_keyerror():
    """Posting that references a non-existent account raises KeyError.

    The entries balance (sum == 0) so this isolates the existence check.
    """
    led = _ledger_with("A")  # "B" never added
    with pytest.raises(KeyError):
        led.post([("A", -100), ("B", 100)])


def test_credit_only_account_posts():
    """A balanced posting credits the credited account (positive amount).

    This does not depend on debits posting, so it passes in both variants:
    the credited account must show its credit.
    """
    led = _ledger_with("A", "B")
    led.post([("A", -250), ("B", 250)])
    assert led.balance("B") == 250


def test_balance_missing_account_keyerror():
    """Querying the balance of an unknown account raises KeyError."""
    led = _ledger_with("A")
    with pytest.raises(KeyError):
        led.balance("ghost")


# ===========================================================================
# FAIL_TO_PASS tests — require EVERY entry (incl. debits) to post
# ===========================================================================

def test_transfer_debits_and_credits():
    """A balanced transfer moves BOTH accounts and nets the books to zero.

    Broken variant drops the negative (debit) entry, so balance("A")==0 and
    trial_balance()==100 instead of 0.
    """
    led = _ledger_with("A", "B")
    led.post([("A", -100), ("B", 100)])
    assert led.balance("A") == -100
    assert led.balance("B") == 100
    assert led.trial_balance() == 0


def test_multi_entry_balanced_posting():
    """A multi-entry split (one debit, several credits) lands exactly.

    Debit cash 1000; credit rent 600 and food 400. Every balance must be exact
    and the trial balance must net to 0. The broken variant drops the cash
    debit, leaving cash at 0 and trial_balance at 1000.
    """
    led = _ledger_with("cash", "rent", "food")
    led.post([("cash", -1000), ("rent", 600), ("food", 400)])
    assert led.balance("cash") == -1000
    assert led.balance("rent") == 600
    assert led.balance("food") == 400
    assert led.trial_balance() == 0


def test_two_postings_accumulate():
    """Sequential balanced postings accumulate; the trial balance stays at 0.

    Broken variant ignores both debits, so A stays at 0 (should be -300) and
    trial_balance ends at 300 instead of 0.
    """
    led = _ledger_with("A", "B", "C")
    led.post([("A", -100), ("B", 100)])
    led.post([("A", -200), ("C", 200)])
    assert led.balance("A") == -300
    assert led.balance("B") == 100
    assert led.balance("C") == 200
    assert led.trial_balance() == 0


# ===========================================================================
# Advisory code quality
# ===========================================================================

@pytest.mark.code_quality
def test_code_quality_report():
    """Advisory only — never asserted as pass/fail."""
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)
