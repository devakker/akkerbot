

from reddit import Reddit

# url handler
import urllib.request  # todo check if these are correct
import urllib.parse



user_agent = "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7"


import hashlib
import pickle
from collections import deque
import random
import os


import errno, os
import sys




reddit = Reddit('botconfig.json')

print(reddit.client.read_only)  # Output: True
print(reddit.collectURLs("pantsu+ecchi", sorting='top', time='month'))
print(reddit.collectURLs("askreddit", sorting='hot', limit=34))








# Output: 10 submission