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

  tries = 1
  done = False
  while not done:
    try:
      await utils.get_to_file(session, chapter.url, path)
      done = True
    except Exception as e:
      print('Download of %s (%s) failed, %d tries: %s! Retrying...' % \
          (chapter.title, chapter.url, tries, str(e)))
      if tries == 20:
        print('  ERR: Giving up')
        return
      tries += 1
  print('Download of %s succeeded!' % (chapter.url))

async def download_book(session, book):
  os.makedirs(book.title, exist_ok=True)

  tasks = map(lambda chapter: download_chapter(session, book.title, chapter),
              book.chapters)
  try:
    await asyncio.gather(*tasks)
  except Exception as e:
    print('Download of ' + book.title + ' failed!')
    print(e)

async def download_books(session, books):
  print('Downloading...')
  tasks = map(lambda book: download_book(session, book), books)
  await asyncio.gather(*tasks)
