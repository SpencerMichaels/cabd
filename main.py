#!/usr/bin/env python3
import sys
from urllib.parse import urlparse

import aiohttp
import asyncio
import argparse
from fake_useragent import UserAgent

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
  parser.add_argument('-m', '--max-conns', type=int, dest='limit', default=100,
      help='The maximum number of concurrent connections. Defaults to 100.')
  return parser

def find(l, pred):
  return next((e for e in l if pred(e)), None)

async def main(loop, limit):
  async with aiohttp.ClientSession(
      connector = aiohttp.TCPConnector(limit=limit),
      headers = { 'User-Agent': UserAgent().chrome },
      loop=loop) as session:
        books = await site.get(session, url)
        await download_books(session, books)

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

  # Use a fake user agent to fool certain sites into presenting normal content
  loop = asyncio.get_event_loop()
  loop.run_until_complete(main(loop, args.limit))
