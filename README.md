## Volt Underwrite (ft. Plaid)

Volt provides a **credit card** with a **daily (not monthly) limit**, gone are the days of large and irresponsible $1,000+ limits, simply have a $25 limit for Monday, and a $50 limit for Tuesday. 

Volt underwrites **daily** with limits changing automatically as your personal circumstances change. 

We use Machine Learning to predict spend / income and augment that with more traditional undewriting methods to compute daily limits suitable to you. 

Manage your limit and pay your account with our app: [https://github.com/derman232/volt-app](https://github.com/derman232/volt-app)

* Receive daily notifications informing you of your limit today
* See your limits for the week
* Earn rewards and points which can be applied to your account when you Pay as cashback
* Manually adjust limits if you have accrued unusued credit limits in the month (will cost you cashback)
* Pay your account

[Choose the response Credit Card with Volt.](https://docs.google.com/presentation/d/10_5U09o-VN7zTYVyC2Y7AfPqcqHyDqmnsRB7K-maYsE/edit?usp=sharing)

## Screenshots

[See the app here](https://github.com/derman232/volt-app)

Dashboard | Manage Limits | Pay
:-------: | :----------: | :----: 
![Volt - Dashboard](https://raw.githubusercontent.com/derman232/volt-app/master/screenshots/Simulator%20Screen%20Shot%20-%20iPhone%20X%20-%202019-10-03%20at%2020.28.48.png) | ![Volt - Manage Limits](https://raw.githubusercontent.com/derman232/volt-app/master/screenshots/Simulator%20Screen%20Shot%20-%20iPhone%20X%20-%202019-10-03%20at%2020.28.53.png) | ![Volt - Pay](https://raw.githubusercontent.com/derman232/volt-app/master/screenshots/Simulator%20Screen%20Shot%20-%20iPhone%20X%20-%202019-10-03%20at%2020.29.02.png)

## Quickstart

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

## Undewriting overview

#### Key inputs

1. Historical transaction data
2. Current account balances
3. Income and expenditure over last recent period
4. Other upcoming liabilities not captured in recent spending

#### Calculations

* **net_income**: Compute income over last month 
* **discretionary_spend**: Compute expenditure on non utilities etc. over last month 
* **total_balances**: Get total account balances net of any credit card debt due (i.e. do not net off longer term debts e.g. student loans). 
* **Transaction Data**: Using LTM of transaction data make predictions around next 7 days of spend using ARIMA model
* **MAX_LIMIT**: Maximum our company is willing to underwrite (in this case $2,600 per month)

#### Total Monthly Limit Calculation

1. Minimum of:
	1. 	Max (net_income, discretionary_spend)
	2. total_balances
	3. MAX_LIMIT

#### Daily Limit Calculation

1. Calculate Total Limit over next 7 Days
2. Apply limit to each day as either the Maximum:
	1. Minimum of:
		1. Maximum of:
			1. 	Max Day Limit
			2. Predicted Spend
		2. Total Limit Remaining to Be Allocated
	2. 0 (limit cannot be less than zero)
