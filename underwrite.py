import base64
import os
import datetime
import plaid
import json
import time
import pprint

pp = pprint.PrettyPrinter(indent=4)
access_token = "access-sandbox-fa2f4574-03fe-4157-a94f-bb5a9ea01c7e"

# Fill in your Plaid API keys - https://dashboard.plaid.com/account/keys
PLAID_CLIENT_ID = os.getenv('PLAID_CLIENT_ID')
PLAID_SECRET = os.getenv('PLAID_SECRET')
PLAID_PUBLIC_KEY = os.getenv('PLAID_PUBLIC_KEY')
# Use 'sandbox' to test with Plaid's Sandbox environment (username: user_good,
# password: pass_good)
# Use `development` to test with live users and credentials and `production`
# to go live
PLAID_ENV = os.getenv('PLAID_ENV', 'sandbox')
# PLAID_PRODUCTS is a comma-separated list of products to use when initializing
# Link. Note that this list must contain 'assets' in order for the app to be
# able to create and retrieve asset reports.
PLAID_PRODUCTS = os.getenv('PLAID_PRODUCTS', 'transactions')



# PLAID_COUNTRY_CODES is a comma-separated list of countries for which users
# will be able to select institutions from.
PLAID_COUNTRY_CODES = os.getenv('PLAID_COUNTRY_CODES', 'US,CA,GB,FR,ES')

client = plaid.Client(client_id = PLAID_CLIENT_ID, secret=PLAID_SECRET,
                      public_key=PLAID_PUBLIC_KEY, environment=PLAID_ENV, api_version='2019-05-29')


def underwrite_decision(data):
  total_balances = check_accounts(data)
  txn_data = check_transactions(data)

  print("Total Balances: %d" % total_balances)

def check_accounts(data):
  total_balances = 0

  if (data.has_key("accounts")):
    for account in data["accounts"]:
      if account["type"] == "depository":
        if account["balances"]["available"] is None:
          total_balances += account["balances"]["current"]
        else:
          total_balances += account["balances"]["available"]
      elif account["type"] == "credit":
        total_balances -= account["balances"]["current"]
        continue
      elif account["type"] == "investment":
        continue
      elif account["type"] == "ira":
        continue
      elif account["type"] == "loan":
        # ignore loans, only care about repayments in transactions
        continue
  else:
    return total_balances
  return total_balances

def check_transactions(data):
  total_income = 0
  total_discretionary = 0

  if data.has_key("transactions"):
    for txn in data["transactions"]:
      cat = txn["category"]
      amount = txn["amount"]

      if "Debit" in cat:
        # income sources
        total_income += amount
        continue

      if "Transfer" in cat:
        continue

      total_discretionary += txn["amount"]
      pp.pprint(txn)

  print("Total Income: %d" % total_income)
  print("Total Discretionary: %d" % total_discretionary)
  return {
    total_income: total_income,
    total_discretionary: total_income,
  }
 
try:
  client.Auth.get(access_token)
except ItemError as e:
  exit(e)

# Pull transactions for the last 30 days
start_date = '{:%Y-%m-%d}'.format(datetime.datetime.now() + datetime.timedelta(-30))
end_date = '{:%Y-%m-%d}'.format(datetime.datetime.now())
try:
  data = client.Transactions.get(access_token, start_date, end_date)
except plaid.errors.PlaidError as e:
  exit(e)

underwrite_decision(data)


