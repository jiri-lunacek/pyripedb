import logging
logging.basicConfig(level=logging.INFO)
from ripedb import RipeDBApi


import pprint

api = RipeDBApi(cache_timeout=3600)

res = api.search('AS-IGNUM-OUT', resource_holder=False, iterator=False)

pprint.pprint(list(map(lambda x: x.id, res[0].resolve_members())))

pprint.pprint(list(map(lambda x: x.id, res[0].resolve_routes())))