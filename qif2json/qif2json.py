import os
from decimal import Decimal
from datetime import datetime

# ---------------------------------------------------------------------------
#   Constants
# ---------------------------------------------------------------------------

# supported encoding
MAC_ENCODING = 'utf-8'
WIN_ENCODING = 'cp1252'

# supported qif extension
MAC_EXTENSION = '.qmtf'
WIN_EXTENSION = '.qif'
SUPPORTED_EXTENSIONS = (MAC_EXTENSION, WIN_EXTENSION, )

# qif file tags
QIF_CHUNK_SEPARATOR = '\n^\n'
OPTION_AUTO_SWITCH = '!Option:AutoSwitch'
ACCOUNT_TAG = '!Account'
CLEAR_AUTO_SWITCH = '!Clear:AutoSwitch'
CATEGORY_TAG_MAC = '!TYPE:Cat'
CATEGORY_TAG_WIN = '!Type:Cat'

# test files
script_dir = os.path.dirname(__file__)
data_dir = 'data'
mac_qif_filename = 'quicken_mac_export.qmtf'
win_qif_filename = 'data_2019.QIF'
QIF_FILE_PATH_MAC = os.path.join(script_dir, data_dir, mac_qif_filename)
QIF_FILE_PATH_WIN = os.path.join(script_dir, data_dir, win_qif_filename)



# ---------------------------------------------------------------------------
#   Helpers
# ---------------------------------------------------------------------------


class Qif2JsonException(Exception):
    pass


class QifObject:
    def __init__(self):
        self.account_name = None
        self.account_type = None
        self.description = None
        self.balance = Decimal('0')
        self.transactions = []







def file_supported(qif_file):
    """
    Check that the qif_file is a qif file.
    We accept files with extensions '.qif' and '.qmtf'.
    """
    filename, file_extension = os.path.splitext(qif_file)

    return file_extension.lower() in SUPPORTED_EXTENSIONS



def parse_date_windows(qif_date):
    """
    Convert a date with Quicken strange format to a python datetime.

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

    return datetime(int(year), int(month), int(day))



def parse_date(qif_date):
    """
    Convert a date with format MM/DD/YY to a python datetime.
    Our test file dates only have 2 digits for years so we have to
    fix a pivot year for 20th or 21st century. We've choosed 2 years from
    the current date's year as a pivot year.

    Ex: today's year is 2019, pivot year is 2021. So any qif date's year
        between 22 and 99 will be in 20th century (1922)

    Note: this is the format used by Quicken MacOS
    """

    if "'" in qif_date:
        return parse_date_windows(qif_date)

    month, day, year = qif_date.split('/')
    pivot_year = datetime.now().year + 2 - 2000
    if pivot_year < int(year) <= 99:
        year = '19' + year
    else:
        year = '20' + year

    return datetime(int(year), int(month), int(day))


def parse_amount(amount):
    """
    Convert an amount from a qif file to Decimal.
    """
    if type(amount) != str:
        raise ValueError(f'Expected a string and was passed a {type(amount)}.')

    # Decimal don't like commas
    amount = amount.replace(',', '')
    return Decimal(amount)



def qif2str(qif_file, encoding=MAC_ENCODING):
    """Reads a qif file and returns a Python str"""

    with open(qif_file, mode='r', encoding=encoding) as fp:
        data = fp.read()

    if len(data) == 0:
        raise Qif2JsonException("Data is empty")
    return data


def qif2list(qif_file, encoding=MAC_ENCODING):
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

    lines = account_chunk.split('\n')
    account = {}
    for line in lines:
        prefix = line[0]
        data = line[1:]

        if prefix == '!': continue
        elif prefix == 'N': account["Name"] = data
        elif prefix == 'B': account["Balance"] = parse_amount(data)
        elif prefix == 'D': account["Description"] = data
        elif prefix == 'T': account["Type"] = data
        elif prefix == 'L': account["Credit Limit"] = data
        else:
            raise ValueError(f'Unknown prefix: {prefix}')
    return account


def parse_transaction(transaction_chunk):
    """
    Parse account infos from a chunk.

    :param transaction_chunk: string separated by new line character

    A transaction_chunk contains all informations about a Qif transaction.
    """
    lines = transaction_chunk.split('\n')
    transaction = {}
    for line in lines:
        prefix = line[0]
        data = line[1:]

        if prefix == '!': continue
        elif prefix == 'D': transaction["Date"] = parse_date(data)
        elif prefix == 'P': transaction["Payee"] = data
        elif prefix == 'M': transaction["Memo"] = data
        elif prefix == 'T': transaction["amount"] = parse_amount(data)
        elif prefix == 'C': transaction["Reconciled"] = data
        elif prefix == 'L': transaction["Category"] = data
        elif prefix == 'N': transaction["Transfer"] = data
        else:
            print(transaction_chunk)
            raise ValueError(f'Unknown prefix: {prefix}')

    return transaction


def parse(qif_file=QIF_FILE_PATH_MAC, encoding=MAC_ENCODING):
    """
    Main parsing function.
    Parse a qif file and returns a python object.
    Use the result to convert the object to json, csv, etc.
    """

    if not file_supported(qif_file):
        raise Qif2JsonException(f'Unsupported file type: {qif_file}')

    # convert qif file to python list
    entry_list = qif2list(qif_file, encoding=encoding)
    entry_list = entry_list[:-1]  # empty line at the end
    # is file mac or windows?
    filename, file_extension = os.path.splitext(qif_file)
    file_type = 'Windows' if file_extension == WIN_EXTENSION else 'MacOS'
    transaction_start_index = find_account_start(entry_list, file_type)
    transaction_list = entry_list[transaction_start_index:]

    # begin parsing
    done = False
    index = 0
    objects = []
    account = {}
    transactions = []
    processing = None
    while not done:
        chunk = transaction_list[index]
        if ACCOUNT_TAG in chunk:
            # starting transaction for a new account
            if processing == 'transactions':
                # done parsing transactions for this account
                obj = { account['Name']: account }
                objects.append(obj)

            processing = 'account_infos'
            account = parse_account(chunk)
        else:
            # transactions
            processing = 'transactions'
            transaction = parse_transaction(chunk)
            transactions.append(transaction)
            account["Transactions"] = transactions
        # stop here for now
        index += 1
        done = index == len(transaction_list) - 1
    return objects


if __name__ == "__main__":
    result = parse()

