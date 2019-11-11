import pytest
from qif2json import __version__

from qif2json.qif2json import (
    USE_DEFAULTS_FOR_ACCOUNTS,
    USE_DEFAULTS_FOR_TRANSACTIONS,
    QIF_FILE_PATH_MAC,
    QIF_FILE_PATH_WIN,
    file_supported,
    convert_date,
    init_transaction,
    init_account,
)

def test_version():
    assert __version__ == '0.1.0'


def test_file_supported():
    result = file_supported(QIF_FILE_PATH_MAC)
    assert result == True

    result = file_supported(QIF_FILE_PATH_WIN)
    assert result == True


def test_init_account_default_false():
    result = init_account(use_defaults=False)

    assert result == {}


def test_init_account_default_true():
    result = init_account(use_defaults=True)

    assert result == {
        "Name": "",
        "Description": "",
        "Type": "",
        "Transaction Count": 0,
        "Transactions": []
    }


def test_init_transaction_default_false():
    result = init_transaction(use_defaults=False)

    assert result == {}


def test_init_transaction_default_true():
    result = init_transaction(use_defaults=True)

    assert result == {
        "Date": "",
        "Payee": "",
        "Amount": "",
        "Category": "",
    }


# -------------------------------------------------------------------------
#   Parsing
# -------------------------------------------------------------------------

# ---------- parse dates -----------------

def test_convert_date_standard_separators():
    test_date = "11/07/13"
    result = convert_date(test_date)
    expected = "2013-11-07"
    assert result == expected


def test_convert_date_weird_separators():
    test_date = "3/ 2' 1"
    result = convert_date(test_date)
    expected = "2001-03-02"
    assert result == expected





