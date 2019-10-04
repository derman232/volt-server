## Volt Underwrite (Using Plaid)

### Quickstart

``` bash
PLAID_CLIENT_ID='CLIENT_ID' \
PLAID_SECRET='SECRET' \
PLAID_PUBLIC_KEY='PUBLIC_KEY' \
PLAID_ENV='sandbox' \
PLAID_PRODUCTS='transactions' \
PLAID_COUNTRY_CODES='US,CA,GB,FR,ES' \
python server.py
# Go to http://localhost:5000
```

Connect an account and click on "Underwrite" --> "Send Request" to receive a daily underwriting decision for the next 7 days. 

### How to


