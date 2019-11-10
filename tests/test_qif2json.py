import pytest
from datetime import datetime
from decimal import Decimal
from qif2json import __version__

from qif2json.qif2json import (
    QIF_FILE_PATH_MAC,
    QIF_FILE_PATH_WIN,
    WIN_ENCODING,
    MAC_ENCODING,
    file_supported,
    find_account_start,
    qif2str,
    qif2list,
    parse_amount,
    parse_date,
    parse,
)

# constants specific to our data
ACCOUNT_START_INDEX_MAC = 208
ACCOUNT_START_INDEX_WIN = 292

ENTRY_LIST_LEN_MAC = 21220
ENTRY_LIST_LEN_WIN = 22232

TRANSACTION_LIST_LEN_MAC = 21011
TRANSACTION_LIST_LEN_WIN = 21932


def test_version():
    assert __version__ == '0.1.0'


def test_file_supported():
    result = file_supported(QIF_FILE_PATH_MAC)
    assert result == True

    result = file_supported(QIF_FILE_PATH_WIN)
    assert result == True


def test_qif2str_mac():
    result = qif2str(QIF_FILE_PATH_MAC)
    assert len(result) > 0


def test_qif2str_win():
    result = qif2str(QIF_FILE_PATH_WIN, encoding=WIN_ENCODING)
    assert len(result) > 0


def test_qif2list_mac():
    result = qif2list(QIF_FILE_PATH_MAC)
    assert len(result) == ENTRY_LIST_LEN_MAC


def test_qif2list_win():
    result = qif2list(QIF_FILE_PATH_WIN, encoding=WIN_ENCODING)
    assert len(result) ==  ENTRY_LIST_LEN_WIN


def test_find_account_start_mac():
    list_ = qif2list(QIF_FILE_PATH_MAC)
    result = find_account_start(list_)
    print(list_[result])
    assert result == ACCOUNT_START_INDEX_MAC


def test_find_account_start_win():
    list_ = qif2list(QIF_FILE_PATH_WIN, encoding=WIN_ENCODING)
    result = find_account_start(list_, qif_file_type='Windows')
    print(list_[result])
    assert result == ACCOUNT_START_INDEX_WIN


# -------------------------------------------------------------------------
#   Parsing
# -------------------------------------------------------------------------

# ---------- parse dates -----------------

def test_parse_date_standard_separators():
    test_date = "11/07/13"
    result = parse_date(test_date)
    expected = datetime(2013, 11, 7)
    assert result == expected


def test_parse_date_weird_separators():
    test_date = "3/ 2' 1"
    result = parse_date(test_date)
    expected = datetime(2001, 3, 2)
    assert result == expected


# ---------- parse amount -----------------

def test_parse_amount_with_commas():
    amount = '1,123,123.55'
    result = parse_amount(amount)
    assert result == Decimal("1123123.55")


def test_parse_amount_with_commas_negative():
    amount = '-1,123,123.55'
    result = parse_amount(amount)
    assert result == Decimal("-1123123.55")


def test_parse_amount_no_commas():
    amount = '1123123.55'
    result = parse_amount(amount)
    assert result == Decimal("1123123.55")


def test_parse_amount_no_commas_negative():
    amount = '-1123123.55'
    result = parse_amount(amount)
    assert result == Decimal("-1123123.55")


def test_parse_mac():
    result = parse(QIF_FILE_PATH_MAC)

    assert result == {}

@pytest.mark.skip(reason="not implemented yet")
def test_parse_win():
    result = parse(QIF_FILE_PATH_WIN, encoding=WIN_ENCODING)

    assert result == {}




