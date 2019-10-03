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

# days in a month
MONTH_DAYS = 30
FULL_WEEK_DAYS = 7
WEEK_DAYS_COUNT = 4
WEEKEND_DAYS_COUNT = 3

# cash balance factor, reduce max limit based on cash balance to 25%
CASH_FACTOR = 0.1

# maximum monthly limit
MAX_LIMIT = 2600

# day limit base
DAY_BASE = 52
WEEK_FACTOR = 1
WEEKEND_FACTOR = 3

client = plaid.Client(client_id = PLAID_CLIENT_ID, secret=PLAID_SECRET,
                      public_key=PLAID_PUBLIC_KEY, environment=PLAID_ENV, api_version='2019-05-29')


def underwrite_decision(data, liabilities):
  total_balances = check_accounts(data)
  txn_data = check_transactions(data)
  total_income = txn_data["total_income"]
  total_discretionary = txn_data["total_discretionary"]
  payments = check_liabilities(liabilities)
  net_income = total_income - total_discretionary - payments

  print("Total Cash Balances: %d" % total_balances)
  print("Total Cash * Factor: %d" % (total_balances * CASH_FACTOR))
  print("Liability Payments: %d" % payments)
  print("Total Income: %d" % total_income)
  print("Total Discretionary Spend: %d" % total_discretionary)
  print("Net Income: %d" % net_income)

  limit = min(
    max(
      net_income,
      total_discretionary
    ),
    MAX_LIMIT,
    total_balances * CASH_FACTOR,
  )

  base = limit / DAY_BASE
  week_limit = base * WEEK_FACTOR
  weekend_limit = base * WEEKEND_FACTOR
  print("Mon - Thurs: %d" % week_limit)
  print("Fri - Sat: %d" % weekend_limit)

  today = datetime.date.today()
  cur_day = today

  output = []
  for x in range(0, FULL_WEEK_DAYS):
    limit = 0
    if (cur_day.weekday() < WEEK_DAYS_COUNT):
      limit = week_limit
    else:
      limit = weekend_limit

    output.append({
      "date": cur_day.strftime("%Y-%m-%d"),
      "day": cur_day.strftime("%A"),
      "limit": limit
    })

    cur_day += datetime.timedelta(days=1)

  pp.pprint(output)



def check_liabilities(data):
  # ignore credit card liabilities, included in spend data
  student = None

  if (data.has_key("liabilities")):
    liabilities = data["liabilities"]
    if liabilities.has_key("student"): 
      student = liabilities["student"]

  amount = 0
  if student is not None:
    for liability in student:
      cur_amount = 0
      last_payment_date = liability["last_payment_date"]
      next_payment_date = liability["next_payment_due_date"]
      last_payment_date = datetime.datetime.strptime(last_payment_date, '%Y-%m-%d')
      next_payment_date = datetime.datetime.strptime(next_payment_date, '%Y-%m-%d')

      days = (next_payment_date - last_payment_date).days

      if liability.has_key("last_statement_balance"):
        cur_amount += liability["last_statement_balance"]
      else:
        cur_amount += liability["last_payment_amount"]
      
      cur_amount *= (MONTH_DAYS * 1.0 / days)
      amount += cur_amount

  return amount

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

  return {
    "total_income": total_income,
    "total_discretionary": total_discretionary,
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
  liabilities = client.Liabilities.get(access_token)
except plaid.errors.PlaidError as e:
  exit(e)

underwrite_decision(data, liabilities)


