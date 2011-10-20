import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from google.appengine.dist import use_library
use_library('django', '1.2')

import urllib2
from django.utils import simplejson as json
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util, template
from datetime import datetime
from models import *
from filters.templatefilters import currency
from google.appengine.api import taskqueue


import logging
class NewTagHandler(webapp.RequestHandler):
    def post(self):
        tagid = self.request.get('tagid')
        tag = Tag.get(tagid)
        offer = Offer(user=None, tag=tag, buy=False, resolved=False, quantity=200, price=tag.price)
        offer.put()

class TagUpdateHandler(webapp.RequestHandler):
    def post(self):
        tagid = self.request.get('id')
        score = int(self.request.get('score'))
        name = self.request.get('webTitle')
        articles = self.request.get_all('articles')
        dividend = (score / 10)
        logging.info('Tag %s has score %d with %d articles, dividend = %d' % (name, score, len(articles), dividend))
        tag = Tag.get_by_key_name(tagid)
        if not tag:
            logging.warn('Tag %s did not exist, creating now' % (tagid))
            score = score / 10
            tag = Tag(key_name=tagid, id=tagid,name=name,price=score, high=score,low=score,dividend=dividend, open_price=score)
            #If we just created it, it's not possibel to have any stocks for it
            # Need at this point to alert everyone that a new stock just floated.
            tag.put()
            taskqueue.add(url='/tasks/newtag', params={'tagid':tag.key()})
        else:
            logging.warn('Updating Tag %s' % (tagid))
            for stock in [stock for stock in tag.stock_set if not stock.sold]:
                paid_dividend = dividend * stock.quantity
                stock.user.pay_dividend(stock, paid_dividend)
            tag.add_dividend(dividend)
            tag.put()

        self.response.out.write('Done')

class CheckOfferHandler(webapp.RequestHandler):
    def post(self):
        offer_bracket = OfferBracket.get(self.request.get('offer_bracket'))
        if offer_bracket.buy_quantity > 0 and offer_bracket.sell_quantity > 0:
            # There are both buyers and sellers at this price, match them up
            if offer_bracket.buy_quantity > offer_bracket.sell_quantity:
                # We want to buy more than we sell, so for each seller, find an offer to match
                offers = [Offer.get(offer) for offer in offer_bracket.offers]
                # for offer in offers:
                #     if not offer.buy and not offer.resolved:
                #         for match in

def main():
    application = webapp.WSGIApplication([
                                    ('/tasks/tagupdate', TagUpdateHandler),
                                    ('/tasks/newtag', NewTagHandler),
                                    ('/tasks/checkoffer', CheckOfferHandler),
                                    ],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
