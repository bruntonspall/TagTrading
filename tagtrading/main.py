#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

is_dev = os.environ['SERVER_SOFTWARE'].startswith('Dev')

from google.appengine.dist import use_library
use_library('django', '1.2')

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util, template
from google.appengine.ext import db
from models import *
from datetime import datetime
import functools

webapp.template.register_template_library('filters.templatefilters')

def set_cookie(self, key, value='', max_age=None,
                   path='/', domain=None, secure=None, httponly=False,
                   version=None, comment=None):
   self.response.headers.add_header('Set-Cookie', '%s=%s; max=age=%d' % (key.encode(), value.encode(), max_age or 0))

def loggedin(f):
    @functools.wraps(f)
    def get_user(handler, *args, **kvargs):
        if handler.request.get('email'):
            email = handler.request.get('email')
            logging.info('Logged in as "%s" via query parameter' % (email))
            if is_dev:
                set_cookie(handler, 'loggedin', email)
            user = UserDetails.get_or_insert(email, email=email, name='Joe Bloggs', cash=50000)
            return f(handler, user, *args, **kvargs)
    
        if not 'loggedin' in handler.request.cookies or not handler.request.cookies['loggedin']:
            logging.info('Redirecting to /signin')
            handler.redirect('/signin')
            return
        userid = handler.request.cookies['loggedin'] or handler.request.get('email')
        logging.info('Logged in as "%s"' % (userid))
        user = UserDetails.get_by_key_name(userid)
        if not user:
            set_cookie(handler, 'loggedin')
            handler.redirect('/signin')
            return None
        return f(handler, user, *args, **kvargs)
    return get_user

class MainHandler(webapp.RequestHandler):
    @loggedin
    def get(self, user):
        path = os.path.join(os.path.dirname(__file__), 'templates/main.html')
        template_values = {'tags':Tag.all(), 'user':user}
        self.response.out.write(template.render(path, template_values))
        
class TagDetailsHandler(webapp.RequestHandler):
    @loggedin
    def get(self, user, tagid):
        tag = Tag.get(tagid)
        path = os.path.join(os.path.dirname(__file__), 'templates/tag.html')
        template_values = {'tag':tag}
        self.response.out.write(template.render(path, template_values))
        

class BuyHandler(webapp.RequestHandler):
    @loggedin
    def get(self, user, tagid=None):
        stock = Tag.get(tagid)
        template_values = {'stock':stock, 'user':user}
        path = os.path.join(os.path.dirname(__file__), 'templates/buy.html')
        self.response.out.write(template.render(path, template_values))
        
    @loggedin    
    def post(self, user, tagid):
        qty = int(self.request.get('qty'))
        tag = Tag.get(tagid)
        if user.buy_stock(tag, qty):
            self.redirect('/')
        self.redirect('/?error=%s' % ('Failed to buy stock'.encode()))

class SellHandler(webapp.RequestHandler):
    @loggedin
    def get(self, user, stockid):
        stock = Stock.get(stockid)
        template_values = {'stock':stock, 'user':user}
        path = os.path.join(os.path.dirname(__file__), 'templates/sell.html')
        self.response.out.write(template.render(path, template_values))

    @loggedin
    def post(self, user, stockid):
        qty = int(self.request.get('qty'))
        stock = Stock.get(stockid)
        if stock.quantity >= qty:
            price = stock.tag.price * qty
            if stock.quantity > qty:
                # We've not sold all stock, so adjust quanityt and create new stock record for sold stock
                Stock(user=user, tag=stock.tag, quantity=qty, purchase_date=stock.purchase_date, purchase_price=stock.purchase_price, sold=True, sold_date=datetime.now(), sold_price=stock.tag.price).put()
                stock.quantity = stock.quantity - qty
            else:
                #We've sold the lot
                stock.sold_price = stock.tag.price
                stock.sold_date = datetime.now()
                stock.sold = True
            stock.put()
            user.cash += price
            user.put()
            stock.tag.available += qty
            stock.tag.put()
            self.redirect('/')
            return
        self.response.out.write('Not enough stock to sell %d of %s\nOnly %d available' % (qty, stock.tag.name, stock.quantity))

class OfferBuyHandler(webapp.RequestHandler):
    @loggedin
    def post(self, user, tagid):
        qty = int(self.request.get('qty'))
        price = int(self.request.get('price'))
        tag = Tag.get(tagid)
        if tag:
            Offer.create(tag=tag, price=price, qty=qty, buy=True, user=user)            
        self.redirect('/')

class OfferSellHandler(webapp.RequestHandler):
    @loggedin
    def post(self, user, stockid):
        qty = int(self.request.get('qty'))
        price = int(self.request.get('price'))
        stock = Stock.get(stockid)
        if stock:
            Offer.create(tag=stock.tag, price=price, qty=qty, buy=False, user=user)
            if stock.on_offer:
                stock.on_offer+=qty
            else:
                stock.on_offer=qty
            stock.put()
        self.redirect('/')
        
class SignInHandler(webapp.RequestHandler):
    def get(self):
        if 'loggedin' in self.request.cookies and self.request.cookies['loggedin']:
            self.redirect('/')
        template_values = {}
        path = os.path.join(os.path.dirname(__file__), 'templates/signin.html')
        self.response.out.write(template.render(path, template_values))
        
    def post(self):
        email = self.request.get('email')
        user = UserDetails.get_or_insert(email, email=email, name='Joe Bloggs', cash=50000)
        set_cookie(self, 'loggedin',email)
        self.redirect('/')
        
class SignOutHandler(webapp.RequestHandler):
    def get(self):
        if 'loggedin' in self.request.cookies:        
            set_cookie(self, 'loggedin', '')
            self.redirect('/signin')
        else:
            self.redirect('/')
        

class RandomJsonHandler(webapp.RequestHandler):
    def get(self):
        import random
        class randomiser(object):
            def next(self):
                return random.randint(1,4000)
        path = os.path.join(os.path.dirname(__file__), 'templates/random.json')
        self.response.headers["Content-Type"] = "text/javascript"
        self.response.out.write(template.render(path, {'rand':randomiser()}))
        

def main():
    application = webapp.WSGIApplication([
                                    ('/', MainHandler),
                                    ('/stock/(?P<stockid>[a-zA-Z0-9-]+)/offer', OfferSellHandler),
                                    ('/tag/(?P<tagid>[a-zA-Z0-9-]+)/buy', OfferBuyHandler),
                                    ('/tag/(?P<tagid>[a-zA-Z0-9-]+)', TagDetailsHandler),
                                    ('/signin', SignInHandler),
                                    ('/signout', SignOutHandler),
                                    ('/randomjson', RandomJsonHandler),
                                    ],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
