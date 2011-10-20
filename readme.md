TagTrading
==========

Introduction
------------

Welcome to Tag Trading, the opportunity to understand more about market forces while simultaneously proving how good a predictor of news you are.

Tag Trading is a very simple premis, it involves you buying shares in a news tag on the guardian.  You will receive in game money for each tag share that you own at midnight GMT based on the performance of that tag in the previous 24 hours.  If you choose tags that perform well you will receive more money, and tags that underperform may payout nothing or withdraw from the stock market, loosing you money.  
The value of a tags shares when issued by the guardian central bank is based upon the performance of news items in terms of "zeitgeistyness" over the previous 4 weeks.

Scratch space
-------------

So, market should consist of the 4 week best trading 100/200/500 tags from the guardian.  
We shoudl track the main market and internally the wider market, so tags that consistently perform well might spring into the top 100 for a month or two then drop back down.  
A tags performance is marked by it's zeitgeistyness for the previous 4 weeks.  
Zetigeistyness is a score associated with a tag based on the number of articles produced in a month times the average number of page views per article + secret sauce.
A tag has a hotness value, ranging from 1 to several thousand.  

Architecture
------------

Trade

* buyer
* seller
* stock
* quantity
* price

Offer

* direction
* person
* stock
* price

Stock

* central price
* last trade
* last 100 trades
* agregate last 1000 trades (in 10s)

User

* email
* handle
* money

UI flows
--------

My Stocks

1. View mystocks page
2. See list of stocks, their current central price, their last traded price and a click through to each stocks page

Stock page

1. show stock price, last 10 trades, etc...

buy:
user selects stock and puts offer price, we save an Offer.
The matcher comes round and looks for offers that match in the other direction, looking for offers with identical prices first.

sell:
User slects stock and puts a price per share, we save an offer.

