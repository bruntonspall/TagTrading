#!/usr/bin/env python
# encoding: utf-8

from django.contrib.humanize.templatetags.humanize import intcomma
# import the webapp module
from google.appengine.ext import webapp
# get registry, we need it to register our filter later.
register = webapp.template.create_template_register()

def currency(dollars):
    dollars = float(dollars)/100.0
    return "$%s%s" % (intcomma(int(dollars)), ("%0.2f" % dollars)[-3:])

register.filter(currency)