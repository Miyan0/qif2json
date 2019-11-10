import pytest
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
    convert_date,
    parse,
)

def test_version():
    assert __version__ == '0.1.0'


def test_file_supported():
    result = file_supported(QIF_FILE_PATH_MAC)
    assert result == True

    result = file_supported(QIF_FILE_PATH_WIN)
    assert result == True


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





