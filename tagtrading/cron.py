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

from google.appengine.dist import use_library
use_library('django', '1.2')

import urllib2
from django.utils import simplejson as json
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util, template
from google.appengine.api import taskqueue
import logging
from models import Tag
import os
from settings import *

def random_json():
    import random
    class randomiser(object):
        def next(self):
            return random.randint(1,4000)
    path = os.path.join(os.path.dirname(__file__), 'templates/random.json')
    return template.render(path, {'rand':randomiser()})

class ZeitgeistHandler(webapp.RequestHandler):
    def get(self):
        if os.environ['SERVER_SOFTWARE'].startswith('Dev'):
            results = json.loads(random_json())
        else:
            results = json.loads(''.join(urllib2.urlopen(API_URL).readlines()))
        for r in results:
            logging.warn('Creating task for %s' % (r))
            taskqueue.add(url='/tasks/tagupdate', params=r)

def main():
    application = webapp.WSGIApplication([
                                    ('/cron_jobs/zeitgeist', ZeitgeistHandler),
                                    ],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
