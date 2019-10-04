import base64
import os
import datetime
import plaid
import json
import time
import pprint
import numpy

# ARIMA
from statsmodels.tsa.arima_model import ARIMA
from random import random
import pandas as pd

pp = pprint.PrettyPrinter(indent=4)

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


# create a differenced series
def difference(dataset, interval=1):
	diff = list()
	for i in range(interval, len(dataset)):
		value = dataset[i] - dataset[i - interval]
		diff.append(value)
	return numpy.array(diff)

# invert differenced value
def inverse_difference(history, yhat, interval=1):
	return yhat + history[-interval]

def predict_spend(access_token):
  # Pull transactions for the last 30 days
  start_date = '{:%Y-%m-%d}'.format(datetime.datetime.now() + datetime.timedelta(-365))
  end_date = '{:%Y-%m-%d}'.format(datetime.datetime.now())
  try:
    data = client.Transactions.get(access_token, start_date, end_date)
  except plaid.errors.PlaidError as e:
    exit(e)

  clean_amounts = []
  clean_dates = []
  clean_data = {}
  for tx in data["transactions"]:
    clean_amounts.append(tx["amount"])
    clean_dates.append(datetime.datetime.strptime(tx["date"], '%Y-%m-%d'))
    if clean_data.has_key(datetime.datetime.strptime(tx["date"], '%Y-%m-%d')):
      clean_data[
        datetime.datetime.strptime(tx["date"], '%Y-%m-%d')
      ] += tx["amount"]
    else:
      clean_data[
        datetime.datetime.strptime(tx["date"], '%Y-%m-%d')
      ] = tx["amount"]


  df = pd.DataFrame(clean_dates, columns=['date'])
  df['data'] = clean_amounts
  df['datetime'] = pd.to_datetime(df['date'])
  df = df.set_index('datetime')
  df.drop(['date'], axis=1, inplace=True)
  df = df.resample('D').mean()
  df = df.fillna(0)


  # contrived dataset
  # fit model
  model = ARIMA(df, order=(5, 0,0))
  model_fit = model.fit(trend='nc', disp=0)

  # make predictions
  cur_date = (df.index.max())
  predictions = list()
  cur_date += datetime.timedelta(days=1)

  # rolling forecasts
  for i in range(7):
  	# predict
    model = ARIMA(df, order=(5,0,0))
    model_fit = model.fit(trend='nc', disp=0)
    yhat = float(model_fit.forecast()[0])
    predictions.append(yhat)

    df2 = pd.DataFrame([cur_date], columns=['date'])
    df2['data'] = yhat
    df2['datetime'] = pd.to_datetime(df2['date'])
    df2 = df2.set_index('datetime')
    df2.drop(['date'], axis=1, inplace=True)
    df2 = df2.resample('D').mean()
    df2 = df2.fillna(0)

    df = df.append(df2)
    df = df.resample('D').mean()
  
  return predictions
