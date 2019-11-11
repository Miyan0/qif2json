# qif2json

Python script for parsing QIF files

Based on [Qif Format](https://en.wikipedia.org/wiki/Quicken_Interchange_Format) and my own observations on **my** data.

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


