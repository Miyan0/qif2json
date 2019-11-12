# qif2json

Python script for parsing QIF files.

Require Python > 3.6 but tested on 3.7.5 (Windows)

Should parse MacOS exported `.qmtf` files correctly, but was tested only on Windows. Need to pass the encoding though.

## Licence

MIT

Do whatever you want with this code but you can't sue me ;-)

## Usage:

``` python
python qif2json.py C:\myqif.QIF C:\my_export.json
```

or

``` python
python qif2json.py C:\myqif.qmtf C:\my_export.json --encoding utf-8
```

Supported encoding are `utf-8` and `cp1252`. Default is `cp1252`. Make sure you pass the correct one.

Based on [Qif Format](https://en.wikipedia.org/wiki/Quicken_Interchange_Format) and my own observations on **my** data.

This project uses [Poetry](https://poetry.eustace.io/) but you can use any virtual environment manager, or none.

Anyway, if you only want to convert a qif file to json, you don't need the whole project, just download `qif2json.py` in the `qif2json` folder.

---

## Notes

Converts only accounts and their respective transactions. Skips account list and categories. Also assumes that the qif file don't contains anything after the last transaction (i.e) it ends with the last transaction of the last account. The script will fail horribly if there's anything other than a new line after the last transaction. Any data **before** the accounts is skipped. This is because, my data is organized this way and I don't plan/have time to mess with this. I suppose that adding a new line could work but didn't test it.

TLDR: anything before the list of transactions don't matter, need a new line after it.


The script has preferences settings for the JSON output:

`USE_DEFAULTS_FOR_ACCOUNTS` to always have fields for:
1. Name
2. Description
3. Type
4. Transaction Count
5. Transaction

Default value is `True`

`USE_DEFAULTS_FOR_TRANSACTIONS` to always have fields for:
1. Date
2. Payee
3. Amount
4. Category

Default value is `True`

No matter what the qif input file contains.

This ensure a default ordering for the keys.


