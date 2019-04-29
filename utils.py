import aiohttp
import asyncio
import os
import sys

from bs4 import BeautifulSoup
import json
import requests

async def get_json(session, url):
  async with session.get(url) as response:
    content = await response.content.read()
    return json.loads(content)

async def get_soup(session, url):
  async with session.get(url) as response:
    content = await response.content.read()
    return BeautifulSoup(content, 'html5lib')

async def get_to_file(session, url, filename=None):
  async with session.get(url) as response:
    filename = filename if filename else os.path.basename(url)
    with open(filename, 'wb') as handle:
      async for chunk, _ in response.content.iter_chunks():
        handle.write(chunk)
    return await response.release()
