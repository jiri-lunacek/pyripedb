import logging
logging.basicConfig(level=logging.INFO)
from ripedb import RipeDBApi

import pprint

api = RipeDBApi(cache_timeout=3600)

# to get inetnum object you can either search

inetnum = api.search('185.123.128.0/22', type_filter='inetnum', iterator=False)[0]
print(inetnum.netname)

# get it by proper id
inetnum = api.inetnum.get('185.123.128.0 - 185.123.131.255')
print(inetnum.netname)

# or by prefix
inetnum = api.inetnum.get(prefix='185.123.128.0/22')
print(inetnum.netname)
