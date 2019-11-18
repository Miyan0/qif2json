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
#   Constants
# ---------------------------------------------------------------------------

DEFAULT_JSON_PATH = Path('/data.json')

# supported encoding
ENCODING_UTF8 = 'utf-8'
ENCODING_CP1252 = 'cp1252'

# supported qif extension
MAC_EXTENSION = '.qmtf'
WIN_EXTENSION = '.qif'

# qif file tags
QIF_CHUNK_SEPARATOR = '\n^\n'
QIF_LINE_SEPARATOR = '\n'
OPTION_AUTO_SWITCH = '!Option:AutoSwitch'
ACCOUNT_TAG = '!Account'
CLEAR_AUTO_SWITCH = '!Clear:AutoSwitch'
CATEGORY_TAG_MAC = '!TYPE:Cat'
CATEGORY_TAG_WIN = '!Type:Cat'

# platforms
MACOS = 'MacOS'
WINDOWS = 'Windows'

# ---------------------------------------------------------------------------
#   Utilities
# ---------------------------------------------------------------------------

class Qif2JsonException(Exception):
    pass


def get_platform(qif_file):
    """
    Check that the qif_file is a qif file.
    We accept files with extensions '.qif' and '.qmtf'.
    """
    filename, file_extension = os.path.splitext(qif_file)
    file_extension = file_extension.lower()

    if file_extension == WIN_EXTENSION:
        return WINDOWS

    if file_extension == MAC_EXTENSION:
        return MACOS

    raise ValueError('Unsupported file type!')



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

# def init_account(use_defaults=USE_DEFAULTS_FOR_ACCOUNTS):
#     """
#     Creates and return an empty account dictionary.

#     The parse functions uses this instead of simply
#     calling account = {}
#     This freezes keys order.
#     """

#     if not use_defaults:
#         return {}

#     return {
#         "Name": "",
#         "Description": "",
#         "Type": "",
#         "Transaction Count": 0,
#         "Transactions": []
#     }


# def init_transaction(use_defaults=USE_DEFAULTS_FOR_TRANSACTIONS):
#     """
#     Creates and return an empty transaction dictionary.

#     The parse functions uses this instead of simply
#     calling transaction = {}
#     This freezes keys order.
#     """

#     if not use_defaults:
#         return {}

#     return {
#         "Date": "",
#         "Payee": "",
#         "Amount": "",
#         "Category": "",
#     }

def chunk_to_list(chunk):
    """Converts a chunk to a list"""
    return chunk.split(QIF_LINE_SEPARATOR)


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



def get_sections_ranges(qif_list, platform=WINDOWS):
    """
    Passing a list of qif file entries, return a dictionary with
    three keys: categories, account_list, transactions
    where each value is a tupple (start, end)

    :param qif_list: list of an already parsed qif file
    :return dictionary

    return value example:

    {
        "categories": (0, 2245, ),
        "account_list": (2246, 22254, ),
        "transactions": (22255, 1231123)
    }

    Purpose:
    Helps parsing categories, account list and transactions
    """

    result = {
        "categories": None,
        "account_list": None,
        "transactions": None
    }
    first_category_index = None
    first_account_index = None
    first_transaction_index = None

    # remove last element if its empty
    last_index = len(qif_list) - 1
    if qif_list[last_index] == '':
        last_index -= 1

    # assumes windows order is categories, account list, transactions
    if platform == WINDOWS:
        for index, entry in enumerate(qif_list):
            if entry.startswith(CATEGORY_TAG_WIN):
                first_category_index = index
            elif entry.startswith(OPTION_AUTO_SWITCH):
                first_account_index = index
            elif entry.startswith(CLEAR_AUTO_SWITCH):
                first_transaction_index = index
            else:
                continue

        result["categories"] = (0, first_account_index - 1, )
        result["account_list"] = (first_account_index, first_transaction_index - 1, )
        result["transactions"] = (first_transaction_index, last_index, )

    # assumes macos order is account list, categories, transactions
    else:  # MACOS
        for index, entry in enumerate(qif_list):
            if entry.startswith(OPTION_AUTO_SWITCH):
                first_account_index = index
            elif entry.startswith(CLEAR_AUTO_SWITCH):
                first_category_index = index
            # for macos, the first entry for transaction is '!Account'
            # which is also used for separating transactions
            elif entry.startswith(ACCOUNT_TAG):
                first_transaction_index = index
                break  # stop at the first !Account tag
            else:
                continue

        result["account_list"] = (0, first_category_index - 1, )
        result["categories"] = (first_category_index, first_transaction_index - 1, )
        result["transactions"] = (first_transaction_index, last_index, )

    return result


def parse_transaction_account(account_chunk):
    """
    Parse the account information part from a chunk's transaction.


    :param account_chunk: string separated by new line character

    A account_chunk contains all informations about a Qif account.
    """

    lines = chunk_to_list(account_chunk)
    account = {}
    for line in lines:
        prefix = line[0]
        data = line[1:]

        if prefix == '!': continue
        elif prefix == 'N': account["name"] = data
        elif prefix == 'B': account["balance"] = data
        elif prefix == 'D': account["description"] = data
        elif prefix == 'T': account["type"] = data
        elif prefix == 'L': account["credit_limit"] = data
        elif prefix == 'A': account["address"] = data
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

        if prefix == 'S': split["category"] = data
        elif prefix == 'E': split["memo"] = data
        elif prefix == '$':
            split["amount"] = data
            splits.append(split)
            split = {}
        else:
            continue

    return splits



# ---------------------------------------------------------------------------
#   Parse begin here
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
#   Parsing catgegories
# ---------------------------------------------------------------------------

def parse_category(cat_chunk):
    category = {
        "name": None,
        "description": None,
        "type": None,   # 'I' for income, 'E' for expense
        "tax": None,    # a number if category is tax related,
    }

    lines = chunk_to_list(cat_chunk)
    for line in lines:
        prefix = line[0]
        data = line[1:]
        if not data: data = None
        if prefix == '!': continue

        # not documented for categories and is
        # always empty in both my mac and windows
        # data files
        elif prefix == 'T': continue
        elif prefix == 'N': category["name"] = data
        elif prefix == 'D': category["description"] = data
        elif prefix == 'R': category["tax"] = data

        # special cases
        elif prefix == 'E':
            if category['type']:
                raise ValueError(f'Category is both income and expense: {line}')
            category["type"] = prefix

        elif prefix == 'I':
            if category['type']:
                raise ValueError(f'Category is both income and expense: {line}')
            category["type"] = prefix

        elif prefix == 'B':
            if not category.get("budget"):
                category["budget"] = []
            category["budget"].append(data)
        else:
            raise ValueError(f'Unknown prefix: {prefix}')

    return category


def parse_categories(cat_list):
    """
    Given a list of categories in qif format, return a list of
    python category object.
    """

    return [parse_category(c) for c in cat_list]


# ---------------------------------------------------------------------------
#   Parsing account list
# ---------------------------------------------------------------------------

def new_parse_account(acc_chunk):

    lines = chunk_to_list(acc_chunk)
    account = {
        "name": None,
        "description": None,
        "type": None,
    }
    for line in lines:
        prefix = line[0]
        data = line[1:]
        if not data: data = None

        if prefix == '!': continue
        elif prefix == 'N': account["name"] = data
        elif prefix == 'B': account["balance"] = data
        elif prefix == 'D': account["description"] = data
        elif prefix == 'T': account["type"] = data
        elif prefix == 'L': account["credit_limit"] = data
        elif prefix == 'A': account["address"] = data
        else:
            raise ValueError(f'Unknown prefix: {prefix}')
    return account


def parse_account_list(account_list):
    """
    Given a list of accounts in qif format, return a list of
    python account object.
    """

    return [new_parse_account(a) for a in account_list]


# ---------------------------------------------------------------------------
#   Parsing transactions
# ---------------------------------------------------------------------------

def parse_transaction_account_info(chunk):
    """
    Returns the transaction's account name and information.

    :param chunk: see chunk description
    :return tuple ((str), dict)
            (account name, account infos, )
    """

    account_name = None
    account_info = {}

    lines = chunk_to_list(chunk)
    for line in lines:
        prefix = line[0]
        data = line[1:]
        if not data: data = None

        if prefix == '!': continue
        elif prefix == 'N':
            account_name = data
            account_info["name"] = account_name
        elif prefix == 'T': account_info["type"] = data
        elif prefix == 'D': account_info["description"] = data

        # mac qmtf file specifics
        elif prefix == 'B': account_info["balance"] = data
        elif prefix == 'L': account_info["credit_limit"] = data
        elif prefix == 'A': account_info["memo"] = data


        else:
            raise ValueError(f'Unknown prefix: {prefix}, chunk: {chunk}')

    return account_name, account_info


def parse_account_transaction(transaction_chunk):
    """
    Extract a transaction from a chunk.

    :param transaction_chunk: string separated by new line character

    A transaction_chunk contains all informations about a Qif transaction.
    """
    lines = chunk_to_list(transaction_chunk)
    transaction = {}

    for line in lines:
        prefix = line[0]
        data = line[1:]

        if prefix == '!': continue
        elif prefix == 'D': transaction["date"] = convert_date(data)
        elif prefix == 'P': transaction["payee"] = data
        elif prefix == 'M': transaction["memo"] = data
        elif prefix == 'T': transaction["amount"] = data
        elif prefix == 'U': transaction["amount2"] = data
        elif prefix == 'C': transaction["reconciled"] = data
        elif prefix == 'L': transaction["category"] = data
        elif prefix == 'N': transaction["ref_number"] = data
        elif prefix == 'F': transaction["reimbursable"] = data
        elif prefix == 'Y': transaction["security_name"] = data
        elif prefix == 'I': transaction["security_price"] = data
        elif prefix == 'Q': transaction["share_qty"] = data
        elif prefix == 'O': transaction["commission_cost"] = data
        elif prefix == 'A':
            if not transaction.get("address"):
                transaction["address"] = data
            else:
                transaction["address"] += (data + '\n')
        elif prefix == '$' or prefix == 'S' or prefix == 'E':
            transaction["splits"] = parse_splits(lines)
        else:
            print(transaction_chunk)
            raise ValueError(f'Unknown prefix: {prefix}')

    return transaction


def parse_transaction_list(list_):
    """
    Given the list of all transactions in a QIF file,
    returns a list of dictionaries grouped by account.

    :param :list_ [(str), ] list of all transactions for all accounts
    :return :list [(dict), ] See notes below.

    Each element in the list has
    the following format:
    {
        "account_name": str,
        "account_infos: dict { name, description, type ...}
        "account_transactions: list of dicts [{date, amount, splits, etc}, ]
    }

    """
    result = []
    account_name = None  # (for convenience, also in account infos)
    account_infos = None  # each transaction list for a account has this
    account_group = {
        "account_name": None,
        "account_infos": None,
        "account_transactions": []
    }

    for t in list_:
        if ACCOUNT_TAG in t:
            if account_group["account_transactions"]:
                result.append(account_group)
                account_group = account_group = {
                    "account_name": None,
                    "account_infos": None,
                    "account_transactions": []
                }
            account_name, account_infos = parse_transaction_account_info(t)
            account_group["account_name"] = account_name
            account_group["account_infos"] = account_infos
            # check if we're processing transactions for a new account

        else:
            account_transaction = parse_account_transaction(t)
            account_group["account_transactions"].append(account_transaction)
    # save last transactions
    result.append(account_group)
    return result


def parse_qif_file(qif_path, encoding=ENCODING_CP1252, platform=WINDOWS):
    qif_path = Path(qif_path)
    list_ = qif2list(qif_path, encoding=encoding)
    all_sections = get_sections_ranges(list_, platform=platform)

    # categories
    start = all_sections["categories"][0]
    end = all_sections["categories"][1]
    cat_list = list_[start:end + 1]
    categories = parse_categories(cat_list)

    # account list
    start = all_sections["account_list"][0]
    end = all_sections["account_list"][1]
    account_list = list_[start:end + 1]
    accounts = parse_account_list(account_list)

    # transactions
    start = all_sections["transactions"][0]
    end = all_sections["transactions"][1]
    transaction_list = list_[start:end + 1]
    transactions = parse_transaction_list(transaction_list)

    return {
        "categories": categories,
        "accounts": accounts,
        "transactions": transactions,
    }


def convert_qif(qif_path, output_path, encoding=ENCODING_CP1252):
    """
    Converts a qif formatted file using the passed encoding to json.

    :params qif_path: full path to qif file
    :params output: full path where the json file will end up
    :params encoding: of the qif file (utf-8 or cp1252) default is cp1252
    """

    qif_path = Path(qif_path)
    output = Path(output_path)
    filename, file_extension = os.path.splitext(qif_path)
    platform = get_platform(qif_path)

    data = parse_qif_file(qif_path, encoding=encoding, platform=platform)
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def convert_qif_test():

    qif_path = './data/data_2019.QIF'
    output_path = './data/data_2019.json'
    convert_qif(qif_path, output_path, encoding=ENCODING_CP1252)


def run_convert_qif():
    default_encoding = ENCODING_CP1252

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


if __name__ == "__main__":

    # Exemple call:
    # python qif2json.py D:\data_2019.QIF --output D:\my_data.json

    convert_qif_test()
    # run_convert_qif()
