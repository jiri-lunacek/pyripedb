import requests, logging
from . import logger as parent_logger
from . objects import object_from_json, empty_object

logger = parent_logger.getChild('rest')

class RestApi():
    _base_url = 'https://rest.db.ripe.net'
    _source = 'RIPE'
    _mntner = None
    _password = None
    _templates = {}

    def __init__(self, base_url = None, source = None, mntner = None, password = None, cache_timeout = 300):
        if base_url is not None:
            self._base_url = base_url
        if source is not None:
            self._source = source
        self._mntner = mntner
        self._password = password
        self._writable = mntner is not None and password is not None
        if cache_timeout is not None:
            import requests_cache
            from datetime import timedelta
            expire_after = timedelta(seconds=cache_timeout)
            requests_cache.install_cache(expire_after=expire_after)
    
    def is_writable(self):
        return self._writable
    
    def _post(self, object_type, object_data):
        q = requests.post(
            url=f'{self._base_url}/{self._source}/{object_type}',
            headers = {'Accept': 'application/json'},
            params = {'password': self._password},
            json = object_data
        )
        if q.status_code == 200:
            return q.json()['objects']['object'][0]
        else:
            logger.debug({'code': q.status_code, 'data': q.content})
            raise ValueError
    def _delete(self, object_type, id):
        q = requests.delete(
            url=f'{self._base_url}/{self._source}/{object_type}/{id}',
            headers = {'Accept': 'application/json'},
            params = {'password': self._password}
        )
        if q.status_code == 200:
            return q.json()['objects']['object'][0]
        else:
            logger.debug({'code': q.status_code, 'data': q.content})
            raise ValueError
    
    def _put(self, object_type, id, object_data):
        q = requests.put(
            url=f'{self._base_url}/{self._source}/{object_type}/{id}',
            headers = {'Accept': 'application/json'},
            params = {'password': self._password},
            json = object_data
        )
        if q.status_code == 200:
            return q.json()['objects']['object'][0]
        else:
            logger.debug({'code': q.status_code, 'data': q.content})
            raise ValueError

    def get_template(self,object_type):
        if object_type not in self._templates:
            q = requests.get(
                url=f'{self._base_url}/metadata/templates/{object_type}',
                headers = {'Accept': 'application/json'}
            )
            if q.status_code == 404:
                # not found
                return None
            elif q.status_code == 200:
                self._templates[object_type] = q.json()['templates']['template'][0]
            else:
                logger.debug({'code': q.status_code, 'data': q.content})
                raise ValueError
        return self._templates[object_type]

    def get_url_json(self, url):
        q = requests.get(
            url = url,
            headers = {'Accept': 'application/json'}
        )
        if q.status_code == 404:
            # not found
            return None
        elif q.status_code == 200:
            return q.json()['objects']['object'][0]
        else:
            logger.debug({'code': q.status_code, 'data': q.json()})
            raise ValueError
        
    def get_object_json(self, object_type, id):
        url = f'{self._base_url}/{self._source}/{object_type}/{requests.utils.quote(id)}'
        return self.get_url_json(url)

    def __getattr__(self, attrname):
        object_type = attrname.replace('_','-')
        return empty_object(self, object_type)

    def search(self, query_string, iterator=True, resource_holder = False, type_filter = None, inverse_attribute = None):
        params = {
            'query-string': query_string,
            'resource-holder': int(resource_holder),
            'type-filter': type_filter,
            'inverse-attribute': inverse_attribute,
        }
        q = requests.get(
            url=f'{self._base_url}/search',
            params = params,
            headers = {'Accept': 'application/json'}
        )
        if q.status_code == 404:
            # not found
            return []
        elif q.status_code == 200:
            # found
            json = q.json()
            itr = map(lambda x: object_from_json(self,x), json['objects']['object'])
            if iterator:
                return itr
            else:
                return list(itr)
        else:
            logger.debug({'code': q.status_code, 'data': q.json()})
            raise ValueError
