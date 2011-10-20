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
    available = db.IntegerProperty(default=100)
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

    def ladder(self):
        return OfferBracket.all().filter('tag =',self).order('price')

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
        return Stock.all().filter('sold =',False).filter('user =',self).order("purchase_date")

    def buy_offers(self):
        return Offer.all().filter('resolved =',False).filter('user =',self).filter('buy =',True).order("tag").order("price")

    def sell_offers(self):
        return Offer.all().filter('resolved =',False).filter('user =',self).filter('buy =',False).order("tag").order("price")

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

    def buy_stock(self, tag, qty):
        if tag.available >= qty:
            price = tag.price * qty
            if price <= self.cash:
                stock = Stock(user=self, tag=tag, quantity=qty, purchase_date=datetime.now(), purchase_price=tag.price, sold=False)
                msg = Message.create_message_without_put(self, "Purchased %d of %s for %s (%s per stock)" % (qty, tag.name, currency(price), currency(tag.price)))
                self.cash -= price
                tag.available -= qty
                db.put([stock, self, tag, msg])
                return True
        return False

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
    purchase_date = db.DateTimeProperty()
    purchase_price = db.IntegerProperty()
    sold = db.BooleanProperty(default=False)
    on_offer = db.IntegerProperty(default=0)

    def gain(self):
        return self.tag.price - self.purchase_price
    def available(self):
        return self.quantity - self.on_offer

class OfferBracket(db.Model):
    buy_quantity = db.IntegerProperty(default=0)
    sell_quantity = db.IntegerProperty(default=0)
    price = db.IntegerProperty(default=0)
    tag = db.ReferenceProperty(Tag)
    offers = db.StringListProperty()

class Offer(db.Model):
    user = db.ReferenceProperty(UserDetails)
    tag = db.ReferenceProperty(Tag)
    quantity = db.IntegerProperty(default=0)
    price = db.IntegerProperty(default=0)
    buy = db.BooleanProperty()
    resolution_date = db.DateTimeProperty()
    resolved = db.BooleanProperty(default=False)

    @classmethod
    def create(klass, tag, price, buy, qty, user):
        offername = "%s-%d" % (tag.name, price)
        offer = klass(user=user, tag=tag, quantity=qty, price=price, buy=buy, resolved=False)
        offer.put()
        offer_bracket = OfferBracket.get_or_insert(offername, tag=tag, price=price)
        if buy:
            offer_bracket.buy_quantity += qty
        else:
            offer_bracket.sell_quantity += qty
        offer_bracket.offers.append(unicode(offer.key()))
        offer_bracket.put()
        taskqueue.add('/tasks/checkoffer', {'offer_bracket':offer_bracket.key()})


    def difference(self):
        return self.price - self.tag.price
    def sellqty(self):
        if not self.buy:
            return self.quantity
    def buyqty(self):
        if self.buy:
            return self.quantity