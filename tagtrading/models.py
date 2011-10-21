#!/usr/bin/env python
# encoding: utf-8
from google.appengine.ext import db
from filters.templatefilters import currency
import logging
import os
import time
from datetime import datetime
from django.utils import simplejson as json
from google.appengine.api import taskqueue


class Tag(db.Model):
    id = db.StringProperty()
    name = db.StringProperty()
    price = db.IntegerProperty()
    high = db.IntegerProperty()
    low = db.IntegerProperty()
    dividend = db.IntegerProperty()
    open_price = db.IntegerProperty()
    _history = db.TextProperty()

    def yield_(self):
        return self.dividend / self.price

    def pe(self):
        return 0.0

    def change(self):
        return self.price - self.open_price

    def direction(self):
        change = self.change()
        if change > 0:
            return "up"
        if change < 0:
            return "down"
        return "still"

    def dividend_history(self):
        return self._history

    def add_dividend(self, price):
        self.dividend = price
        h = json.loads(self._history or '[]')
        h.append([int(time.time()*1000),price])
        self._history = json.dumps(h, indent=2)

    def available(self):
        return sum([offer.quantity for offer in self.offer_set])

class UserDetails(db.Model):
    email = db.EmailProperty()
    name = db.StringProperty()
    cash = db.IntegerProperty()

    @classmethod
    def get_by_email(klass, email):
        return users[0]

    def stock_total(self):
        return sum([stock.purchase_price * stock.quantity for stock in self.stock_set])

    def stock_sell_total(self):
        return sum([stock.tag.price * stock.quantity for stock in self.stock_set])

    def current_stocks(self):
        return Stock.all().filter('user =',self).order("tag")

    def sell_offers(self):
        return Offer.all().filter('user =',self).order("tag").order("min_price")

    def make_deposit(self, value, msg):
        self.cash += value
        msg = Message.create_message_without_put(self, msg)
        db.put([msg, self])

    def get_messages(self):
        return Message.messages_for_user(self).fetch(10)

    def pay_dividend(self, stock, paid_dividend):
        msg = Message.create_message_without_put(self, 'Received dividend of %s for owning %d of %s' % (currency(paid_dividend), stock.quantity, stock.tag.name))
        self.cash += paid_dividend
        db.put([self, msg])

    def add_stock(self, tag, qty, price):
        stock = self.stock_set.filter('tag =', tag).get()
        if not stock:
            stock = Stock(user=self, tag=tag, quantity=0, on_offer=0)
        stock.quantity += qty
        self.cash -= qty*price
        db.put([self, stock])


    def pay_for_offer(self, offer, qty, price):
        logging.info("Offers found, now fulfilling each offer")

        stock = self.stock_set.filter('tag =', offer.tag).get()
        logging.info("We have a stock %s" % (stock))
        if stock and stock.quantity >= qty:
            total = qty * price
            msg = Message.create_message_without_put(self, 'Offer accepted for %d of %s at %s' % (qty, offer.tag.name, currency(total)))
            self.cash += total
            stock.quantity -= qty
            stock.on_offer -= qty
            db.put([self, msg, stock])
            return True
        return False

    def buy_stock(self, tag, qty):
        if tag.available >= qty:
            price = tag.price * qty
            if price <= self.cash:
                stock = self.stock_set.filter("tag =", tag).get()
                if stock:
                    stock.quantity += qty
                    stock.purchase_price = max(stock.purchase_price, tag.price)
                    stock.put()
                else:
                    stock = Stock(user=self, tag=tag, quantity=qty, purchase_price=tag.price)
                msg = Message.create_message_without_put(self, "Purchased %d of %s for %s (%s per stock)" % (qty, tag.name, currency(price), currency(tag.price)))
                self.cash -= price
                tag.available -= qty
                db.put([stock, self, tag, msg])
                return True
        return False

bank = UserDetails.get_by_key_name("bank")
if not bank:
    bank = UserDetails(key_name="bank", email='bank@bank.com', name="The Bank of Guardian", cash=1000000000)
    bank.put()

class Message(db.Model):
    user = db.ReferenceProperty(UserDetails)
    msg = db.TextProperty()
    dt = db.DateTimeProperty()

    @classmethod
    def create_message(klass, user, msg):
        klass(msg = msg, dt = datetime.now(), user=user).put()

    @classmethod
    def create_message_without_put(klass, user, msg):
        return klass(msg = msg, dt = datetime.now(), user=user)

    @classmethod
    def messages_for_user(klass, user):
        return klass.all().filter('user =',user).order('-dt')

class Stock(db.Model):
    user = db.ReferenceProperty(UserDetails)
    tag = db.ReferenceProperty(Tag)
    quantity = db.IntegerProperty()
    on_offer = db.IntegerProperty(default=0)

    def gain(self):
        return self.tag.price - self.purchase_price
    def available(self):
        return self.quantity - self.on_offer

class Offer(db.Model):
    user = db.ReferenceProperty(UserDetails)
    tag = db.ReferenceProperty(Tag)
    quantity = db.IntegerProperty(default=0)
    min_price = db.IntegerProperty(default=0)

    @classmethod
    def create(klass, tag, price, qty, user):
        offername = "%s-%d" % (tag.name, price)
        offer = klass(user=user, tag=tag, quantity=qty, min_price=price)
        offer.put()

    @classmethod
    def find_all(klass, tag):
        return klass.all().filter('tag =', tag).order('-min_price')

    def fulfill(self, qty, price, otheruser):
        logging.info("fulfilling offer for %d at %d" % (qty, price))

        if self.user.pay_for_offer(self, qty, price):
            self.quantity -= qty
            if self.quantity:
                self.put()
            else:
                self.delete()
            otheruser.add_stock(self.tag, qty, price)

    def difference(self):
        return self.price - self.tag.price
    def sellqty(self):
        if not self.buy:
            return self.quantity
    def buyqty(self):
        if self.buy:
            return self.quantity