import argparse
import os
import json
from datetime import datetime
from pathlib import Path

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


# ---------------------------------------------------------------------------
#   Preferences
# ---------------------------------------------------------------------------

# Change these to False to prevent always add some fields in the JSON

# if True, JSON will always have
# "Name, Description, Type, Transaction Count, Transaction"
# for accounts. See init_account()
USE_DEFAULTS_FOR_ACCOUNTS = True

# if True, JSON will always have
# "Date, Payee, Amount, Category"
# for transactions. See init_transaction()
USE_DEFAULTS_FOR_TRANSACTIONS = True

# ---------------------------------------------------------------------------
#   Constants
# ---------------------------------------------------------------------------

DEFAULT_JSON_PATH = Path('/data.json')

# supported encoding
MAC_ENCODING = 'utf-8'
WIN_ENCODING = 'cp1252'

# supported qif extension
MAC_EXTENSION = '.qmtf'
WIN_EXTENSION = '.qif'
SUPPORTED_EXTENSIONS = (MAC_EXTENSION, WIN_EXTENSION, )

# qif file tags
QIF_CHUNK_SEPARATOR = '\n^\n'
QIF_LINE_SEPARATOR = '\n'
OPTION_AUTO_SWITCH = '!Option:AutoSwitch'
ACCOUNT_TAG = '!Account'
CLEAR_AUTO_SWITCH = '!Clear:AutoSwitch'
CATEGORY_TAG_MAC = '!TYPE:Cat'
CATEGORY_TAG_WIN = '!Type:Cat'


# ---------------------------------------------------------------------------
#   Utilities
# ---------------------------------------------------------------------------

class Qif2JsonException(Exception):
    pass


def file_supported(qif_file):
    """
    Check that the qif_file is a qif file.
    We accept files with extensions '.qif' and '.qmtf'.
    """
    filename, file_extension = os.path.splitext(qif_file)

    return file_extension.lower() in SUPPORTED_EXTENSIONS


# date conversion
# ---------------

def convert_date_windows(qif_date):
    """
    Convert a date with Quicken strange format to a YYYY-MM-DD.

    Notes:
    qif date format on windows for dates after 1999

    Example of the format we're dealing with: 2/ 1' 3
    here, 2 is the month, 1 is the day and 3 is the year
    """

    # first split we'll get month and rest
    month, rest = qif_date.split('/')
    day, year = rest.split("'")

    # remove whitespace
    month = month.strip()
    day = day.strip()
    year = year.strip()

    # pad with zeros
    if len(month) < 2:
        month = f'0{month}'
    if len(day) < 2:
        day = f'0{day}'

    if len(year) < 2:
        year = f'200{year}'
    elif len(year) < 3:
        year = f'20{year}'

    return datetime(int(year), int(month), int(day)).strftime("%Y-%m-%d")


def convert_date(qif_date):
    """
    Convert a date with format MM/DD/YY to YYYY-MM-DD.
    Our test file dates only have 2 digits for years so we have to
    fix a pivot year for 20th or 21st century. We've choosed 2 years from
    the current date's year as a pivot year.

    Ex: today's year is 2019, pivot year is 2021. So any qif date's year
        between 22 and 99 will be in 20th century (1922)

    Note: this is the format used by Quicken MacOS
    """

    if "'" in qif_date:
        return convert_date_windows(qif_date)

    month, day, year = qif_date.split('/')
    pivot_year = datetime.now().year + 2 - 2000
    if pivot_year < int(year) <= 99:
        year = '19' + year
    else:
        year = '20' + year

    return datetime(int(year), int(month), int(day)).strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
#   Parsing helpers
# ---------------------------------------------------------------------------

def init_account(use_defaults=USE_DEFAULTS_FOR_ACCOUNTS):
    """
    Creates and return an empty account dictionary.

    The parse functions uses this instead of simply
    calling account = {}
    This freezes keys order.
    """

    if not use_defaults:
        return {}

    return {
        "Name": "",
        "Description": "",
        "Type": "",
        "Transaction Count": 0,
        "Transactions": []
    }


def init_transaction(use_defaults=USE_DEFAULTS_FOR_TRANSACTIONS):
    """
    Creates and return an empty transaction dictionary.

    The parse functions uses this instead of simply
    calling transaction = {}
    This freezes keys order.
    """

    if not use_defaults:
        return {}

    return {
        "Date": "",
        "Payee": "",
        "Amount": "",
        "Category": "",
    }


def qif2str(qif_file, encoding):
    """Reads a qif file and returns a Python str"""

    with open(qif_file, mode='r', encoding=encoding) as fp:
        data = fp.read()

    if len(data) == 0:
        raise Qif2JsonException("Data is empty")
    return data


def qif2list(qif_file, encoding):
    """Parse a qif file and returns a list of entries"""

    qif_str = qif2str(qif_file, encoding=encoding)

    qif_list = qif_str.split(QIF_CHUNK_SEPARATOR)

    return qif_list


def find_account_start(qif_list, qif_file_type='MacOS'):
    """Return the index where the list of transactions starts."""

    flag = CLEAR_AUTO_SWITCH
    if qif_file_type == 'MacOS':
        flag = ACCOUNT_TAG

    for index, entry in enumerate(qif_list):
        if entry.startswith(flag):
            return index


def parse_account(account_chunk):
    """
    Parse account infos from a chunk.

    :param account_chunk: string separated by new line character

    A account_chunk contains all informations about a Qif account.
    """

    lines = account_chunk.split(QIF_LINE_SEPARATOR)
    account = init_account()
    for line in lines:
        prefix = line[0]
        data = line[1:]

        if prefix == '!': continue
        elif prefix == 'N': account["Name"] = data
        elif prefix == 'B': account["Balance"] = data
        elif prefix == 'D': account["Description"] = data
        elif prefix == 'T': account["Type"] = data
        elif prefix == 'L': account["Credit Limit"] = data
        elif prefix == 'A': account["Address"] = data
        else:
            raise ValueError(f'Unknown prefix: {prefix}')
    return account


def parse_splits(chunk_lines):
    """
    Parse splits from a chunk_lines (as list) and return
    a list of splits.

    :param chunk_lines: list

    Note:
    -----
    Assume split infos have 3 lines where a line which starts
    with 'S' begin split infos and the next 2 lines begin with '$'
    and 'E' in that order.
    """

    split = {}
    splits = []

    for index, line in enumerate(chunk_lines):
        prefix = line[0]
        data = line[1:]

        if prefix == 'S': split["Category"] = data
        elif prefix == 'E': split["Memo"] = data
        elif prefix == '$':
            split["Amount"] = data
            splits.append(split)
            split = {}
        else:
            continue

    return splits


def parse_transaction(transaction_chunk):
    """
    Parse account infos from a chunk.

    :param transaction_chunk: string separated by new line character

    A transaction_chunk contains all informations about a Qif transaction.
    """
    lines = transaction_chunk.split(QIF_LINE_SEPARATOR)
    transaction = init_transaction()

    for line in lines:
        prefix = line[0]
        data = line[1:]

        if prefix == '!': continue
        elif prefix == 'D': transaction["Date"] = convert_date(data)
        elif prefix == 'P': transaction["Payee"] = data
        elif prefix == 'M': transaction["Memo"] = data
        elif prefix == 'T': transaction["Amount"] = data
        elif prefix == 'U': transaction["Amount2"] = data
        elif prefix == 'C': transaction["Reconciled"] = data
        elif prefix == 'L': transaction["Category"] = data
        elif prefix == 'N': transaction["Transfer"] = data
        elif prefix == 'F': transaction["Reimbursable"] = data
        elif prefix == 'Y': transaction["Security Name"] = data
        elif prefix == 'I': transaction["Security Price"] = data
        elif prefix == 'Q': transaction["Share Qty"] = data
        elif prefix == 'O': transaction["Commission Cost"] = data
        elif prefix == 'A':
            if not transaction.get("Address"):
                transaction["Address"] = data
            else:
                transaction["Address"] += (data + ', ')
        elif prefix == '$' or prefix == 'S' or prefix == 'E':
            transaction["Splits"] = parse_splits(lines)
        else:
            print(transaction_chunk)
            raise ValueError(f'Unknown prefix: {prefix}')

    return transaction


# ---------------------------------------------------------------------------
#   Parsing begin here
# ---------------------------------------------------------------------------

def parse(qif_file, encoding):
    """
    Main parsing function.
    Parse a qif file and returns a python object.
    Use the result to convert the object to json, csv, etc.
    """

    if not file_supported(qif_file):
        raise Qif2JsonException(f'Unsupported file type: {qif_file}')

    # convert qif file to python list
    entry_list = qif2list(qif_file, encoding=encoding)

    # is file mac or windows?
    filename, file_extension = os.path.splitext(qif_file)
    file_type = 'Windows' if file_extension.lower() == WIN_EXTENSION else 'MacOS'

    transaction_start_index = find_account_start(entry_list, file_type)
    transaction_list = entry_list[transaction_start_index:]

    # begin parsing
    account = None
    objects = []
    transactions = []
    processing = None
    for chunk in transaction_list:
        # empty line at the end is our flag
        if not chunk:
            account["Transactions"] = transactions
            account["Transaction Count"] = str(len(transactions))
            objects.append(account)
            break
        if ACCOUNT_TAG in chunk:
            # starting transaction for a new account
            if processing == 'transactions':
                # done parsing transactions for this account
                account["Transactions"] = transactions
                account["Transaction Count"] = str(len(transactions))
                objects.append(account)
                account = init_account()
                transactions = []

            processing = 'account_infos'
            account = parse_account(chunk)
        else:
            processing = 'transactions'
            transaction = parse_transaction(chunk)
            transactions.append(transaction)
    return objects


def convert_qif(qif_path, output_path, encoding=WIN_ENCODING):
    """
    Converts a qif formatted file using the passed encoding to json.

    :params qif_path: full path to qif file
    :params output: full path where the json file will end up
    :params encoding: of the qif file (utf-8 or cp1252) default is cp1252
    """

    qif_path = Path(qif_path)
    output = Path(output_path)

    data = parse(qif_path, encoding=encoding)
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":

    # Exemple call:
    # python qif2json.py D:\data_2019.QIF --output D:\my_data.json

    default_encoding = WIN_ENCODING

    parser = argparse.ArgumentParser(description='Enter the path to the qif file.')
    parser.add_argument('path', type=str, help="full path to a qif file")
    parser.add_argument('output', type=str, help=f"full path of json output file")
    parser.add_argument('--encoding', type=str, help=f"encoding of the qif file, either utf-8 or cp1252 (default to {default_encoding})", default=default_encoding)

    args = parser.parse_args()
    qif_path = Path(args.path)
    output = Path(args.output)
    encoding = args.encoding or default_encoding

    print(f"Converting qif file: {qif_path} encoding: {encoding}")
    convert_qif(qif_path, output, encoding=encoding)
    print(f"JSON file generated: {output}")
