#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = u'Yuji Nakao'
SITENAME = u'UGarchive'
SITEURL = ''

PATH = 'content'
STATIC_PATHS = ['images', 'images/favicon.ico']
EXTRA_PATH_METADATA = {'images/favicon.ico': {'path': 'favicon.ico'}}
DELETE_OUTPUT_DIRECTORY = True

TIMEZONE = 'Asia/Tokyo'

DEFAULT_LANG = u'en'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = 'feeds/all.atom.xml'
TAG_FEED_ATOM = 'feeds/%s.atom.xml'

# Blogroll
# LINKS = (('Pelican', 'http://getpelican.com/'),
#         ('Python.org', 'http://python.org/'),
#         ('Jinja2', 'http://jinja.pocoo.org/'),
#         ('You can modify those links in your config file', '#'),)

# Social widget
SOCIAL = (('github', 'https://github.com/ynakao/'),
          ('twitter', 'https://twitter.com/nakaoyuji'),
          ('flickr', 'https://www.flickr.com/photos/ynakao/'),
          ('rss', '/feeds/all.atom.xml'),)

DEFAULT_PAGINATION = 10

# Uncomment following line if you want document-relative URLs when developing
# RELATIVE_URLS = True

ARTICLE_URL = '{date:%Y}/{date:%m}/{date:%d}/{slug}/'
ARTICLE_SAVE_AS = '{date:%Y}/{date:%m}/{date:%d}/{slug}/index.html'
PAGE_URL = '{slug}/'
PAGE_SAVE_AS = '{slug}/index.html'
TAG_URL = 'tag/{slug}/'
TAG_SAVE_AS = 'tag/{slug}/index.html'

FILENAME_METADATA = '(?P<date>\d{4}-\d{2}-\d{2})_(?P<slug>.*)'

THEME = "themes/pelican-sundown"
TYPOGRIFY = True
SUMMARY_MAX_LENGTH = 20
