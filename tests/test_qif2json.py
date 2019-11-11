'''
LICENCE-MIT

Copyright (c) 2019-2020 André Massé (Miyan0)

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
'''

'''
Project hosted at https://github.com/Miyan0/qif2json
'''


import pytest
from pathlib import Path

from qif2json import __version__

from qif2json.qif2json import (
    USE_DEFAULTS_FOR_ACCOUNTS,
    USE_DEFAULTS_FOR_TRANSACTIONS,
    file_supported,
    convert_date,
    init_transaction,
    init_account,
)

# test files
data_dir = 'data'
parent_dir = Path().resolve()
mac_qif_filename = 'quicken_mac_export.qmtf'
win_qif_filename = 'data_2019.QIF'

QIF_FILE_PATH_MAC = parent_dir / data_dir / mac_qif_filename
QIF_FILE_PATH_WIN = parent_dir / data_dir / win_qif_filename

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





