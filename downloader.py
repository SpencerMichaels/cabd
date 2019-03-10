import asyncio

import os
from urllib.parse import urlparse

from fake_useragent import UserAgent

import utils

__all__ = ['download_books']
USER_AGENT = UserAgent().chrome

async def download_chapter(session, directory, chapter):
  url = urlparse(chapter.url, scheme='http')
  ext = url.path.split('.')[-1]
  path = '%s/%s.%s' % (directory, chapter.title, ext)

  await utils.get_to_file(session, chapter.url, path)

async def download_book(session, book):
  os.makedirs(book.title, exist_ok=True)

  tasks = map(lambda chapter: download_chapter(session, book.title, chapter),
              book.chapters)
  await asyncio.gather(*tasks)

async def download_books(session, books):
  print('Downloading...')
  tasks = map(lambda book: download_book(session, book), books)
  await asyncio.gather(*tasks)
