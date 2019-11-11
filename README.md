# qif2json

Python script for parsing QIF files

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


