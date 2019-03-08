from multiprocessing.pool import ThreadPool
import os
import time
from urllib.parse import urlparse

from fake_useragent import UserAgent

import utils

__all__ = ['download_books']
USER_AGENT = UserAgent().chrome

def download_chapter(arg):
  (path, chapter) = arg

  url = urlparse(chapter.url, scheme='http')
  ext = url.path.split('.')[-1]
  fqp = '%s/%s.%s' % (path, chapter.title, ext)

  r = utils.get(chapter.url, stream=True)
  with open(fqp, 'wb') as f:
    for chunk in r.iter_content(chunk_size=0x100000):
      f.write(chunk)

  return chapter

def download_book(book, num_threads):
  os.makedirs(book.title, exist_ok=True)

  print('\nDownloading \"%s\"...' % (book.title))
  chapters = [ (book.title, chapter) for chapter in book.chapters ]
  utils.do_multi(download_chapter, chapters,
           lambda total, chapter: utils.print_progress(len(book.chapters), total, chapter.title), num_threads)

def download_books(books, num_threads):
  for book in books:
    download_book(book, num_threads)
