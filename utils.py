from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool
import sys

from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import requests

USER_AGENT = UserAgent().chrome

def get(url, stream=False):
  return requests.get(url, headers={ 'User-Agent': USER_AGENT }, stream=stream)

def get_soup(url):
  with get(url) as response:
    return BeautifulSoup(response.content, 'html5lib')

def do_multi(func, args, on_progress, num_threads=cpu_count()):
  class _func():
    def __init__(self):
      self.total = 0

    def __call__(self, arg):
      result = func(arg)
      self.total += 1
      if on_progress:
        on_progress(self.total, result)
      return result

  pool = ThreadPool(num_threads)
  result = pool.map(_func(), args)
  pool.close()
  pool.join()

  return result

def print_progress(num_total, num_current, message, indent_level=0, write_over=False):
  def overwrite(s):
    sys.stdout.write('\r' + s)
    sys.stdout.flush()

  write = overwrite \
            if write_over \
            else print
  write('  ' * indent_level + '[%d%%]\t%s' % ((num_current*100)/num_total, message))

  if (num_total == num_current and write_over):
    print('')
