import glob
from importlib import import_module
from os.path import dirname, abspath, isfile

def get_sites():
  files = glob.glob(dirname(abspath(__file__)) + '/*.py')
  names = [ f.split('/')[-1][:-3] for f in files ]
  return [ import_module('sites.' + name) for name in names if not name == '__init__' ]
