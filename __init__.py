#!/usr/bin/env python3

import argparse
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool
import sys
from urllib.parse import urlparse

from book import Book
from chapter import Chapter
from downloader import download_books
from sites import get_sites

SITES = get_sites()

def make_pretty_site_list():
  return [ '%s (%s)' % (site.NAME, ', '.join(site.DOMAINS)) for site in SITES ]

def make_parser():
  parser = argparse.ArgumentParser(
      description='Download Chinese audiobooks.',
      epilog='Supported sites: ' + ', '.join(make_pretty_site_list())) 
  parser.add_argument('url', type=str,
      help='The URL of the audiobook\'s main page.')
  parser.add_argument('-t', '--threads', type=int, default=cpu_count(),
      help='The number of threads to use for multi-threaded downloads. Defaults to %d.' \
          % (cpu_count()))
  return parser

def find(l, pred):
  return next((e for e in l if pred(e)), None)

if __name__ == '__main__':
  parser = make_parser()
  args = parser.parse_args()
  url = urlparse(args.url, scheme='http')
  domain = url.netloc.split(':')[0] # Remove port if present

  site = find(SITES, lambda site: site.can_handle(domain))

  if not site:
    print('ERROR: Unsupported site! The following are supported.')
    [ print('  ' + s) for s in make_pretty_site_list() ]
    sys.exit(1)

  books = site.get(url, args.threads)
  download_books(books, args.threads)
