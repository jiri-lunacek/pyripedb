from .. import logger as base_logger

logger = base_logger.getChild('objects')

from ipaddress import ip_network

def empty_object(api, object_type):
    if object_type in object_types:
        obj = object_types[object_type](api, object_type = object_type)
    else:
        obj = RipeObject(api, object_type = object_type)
    return obj

def object_from_json(api, json_data):
    obj = empty_object(api,json_data['type'])
    obj._parse_json(json_data)
    return obj

def object_from_link(api, attr):
    json_data = api.get_url_json(attr['link']['href'])
    if json_data is None:
        obj = empty_object(api,attr['referenced-type'])
        obj._id = attr['value']
        return obj
    else:
        return object_from_json(api, json_data)


class RipeObject():
    _type = None
    _id = None
    _id_attr = None
    _api = None
    _template = None
    _template_attributes = {}
    _link = None
    attributes = []

    def __init__(self, api, object_type, json_data = None):
        self._api = api
        try:
            self._template = api.get_template(object_type)
            # get primary key attribute
            for template_attr in self._template['attributes']['attribute']:
                self._template_attributes[template_attr['name']] = template_attr
                if 'keys' in template_attr and 'PRIMARY_KEY' in template_attr['keys']:
                    self._id_attr = template_attr['name']
            self._type = object_type
        except:
            raise ValueError(f'Invalid object type {object_type}')
        if json_data is not None:
            self._parse_json(json_data)
        pass

    def _parse_json(self, json_data):
        self._type = json_data['type']
        self._id = json_data['primary-key']['attribute'][0]['value']
        self._link = json_data['link']
        self.attributes = json_data['attributes']['attribute']
    
    def _resolve_attribute(self,attr):
        if 'link' in attr and attr['link']['type'] == 'locator':
            return object_from_link(self._api, attr)
        else:
            return attr['value']

    def __getattr__(self,attrname):
        if attrname == 'id':
            return self._id
        elif attrname == 'type':
            return self._type
        found_items = []
        attrname = attrname.replace('_','-')
        if attrname not in self._template_attributes:
            raise AttributeError
        for item in self.attributes:
            if item['name'] == attrname:
                item_resolved = self._resolve_attribute(item)
                if item_resolved is not None:
                    found_items.append(self._resolve_attribute(item))

        if self._template_attributes[attrname].get('cardinality','SINGLE') == 'MULTIPLE':
            return found_items
        elif len(found_items) > 0:
            return found_items[0]
        else:
            return None
    
    def get_attributes(self, format = dict):
        if format == str:
            return '\n'.join(map(lambda x: f"{x['name']}:\t{x['value']}", self.attributes))
        elif format == dict:
            out_attributes = {}
            for attr in self.attributes:
                if self._template_attributes[attr['name']].get('cardinality','SINGLE') == 'MULTIPLE':
                    if attr['name'] not in out_attributes:
                        out_attributes[attr['name']] = []
                    out_attributes[attr['name']].append(attr['value'])
                else:
                    out_attributes[attr['name']] = attr['value']
            return out_attributes
        raise ValueError('Format not implemented')

    def get(self,id):
        json = self._api.get_object_json(self._type,id)
        if json is None:
            raise ValueError('Object not found')
        self._parse_json(json)
        return self
    
    def __get_ripe_object(self, attributes):
        # perform basic validation
        missing_attributes = []
        possible_attributes = {}
        for template_attr in self._template['attributes']['attribute']:
            possible_attributes[template_attr['name']] = template_attr
            if template_attr['requirement'] == 'MANDATORY' and (
                    template_attr['name'] not in attributes or
                    attributes[template_attr['name']] in [None,'',[]]
            ):
                missing_attributes.append(template_attr['name'])
        if len(missing_attributes) > 0:
            raise ValueError(f'Missing mandatory attributes: {",".join(missing_attributes)}')
        object_attributes = []
        # object type attribute must be first in the list
        # I suspect that the json is really converted to string
        # ask in RIPE why this really is
        #
        # we can assume that type attribute is mandatory ans SINGLE cardinality
        #
        object_attributes.append({'name':self._type, 'value': attributes[self._type]})
        for attr_name in attributes:
            if attr_name == self._type:
                continue
            if attr_name not in possible_attributes:
                raise ValueError(f'Invalid attribute {attr_name}')
            if isinstance(attributes[attr_name], list):
                if possible_attributes[attr_name].get('cardinality','SINGLE') != 'MULTIPLE':
                    raise ValueError(f'Attribute {attr_name} may only have one value')
                for value in attributes[attr_name]:
                    object_attributes.append({'name':attr_name, 'value': value})
            else:
                object_attributes.append({'name':attr_name, 'value': attributes[attr_name]})
        ripe_object = {
            "objects": {
                "object": [
                {
                    "source": {
                        "id": attributes['source']
                    },
                    "attributes": {
                    "attribute": object_attributes
                    }
                }
                ]
            }
        }
        return ripe_object

    def __get_ripe_ojbect_from_string(self, data):
        object_attributes = [ {'name': name, 'value': value} for (name,value) in map(
            lambda x: x.split(':', 1),
            filter(lambda x: x.strip() != '', data.split('\n'))
        )]
        ripe_object = {
            "objects": {
                "object": [
                {
                    "source": {
                        "id": self._api._source
                    },
                    "attributes": {
                    "attribute": object_attributes
                    }
                }
                ]
            }
        }
        return ripe_object

    def create(self, id, attributes):
        if not self._api.is_writable():
            raise ValueError('API is not writable, please supply maintainer and password')
        if isinstance(attributes, str):
            object_data = self.__get_ripe_ojbect_from_string(attributes)
        else:
            # push id and maintainer
            attributes[self._id_attr] = id
            attributes['source'] = self._api._source
            if 'mnt-by' in attributes:
                if not isinstance(attributes['mnt-by'], list):
                    attributes['mnt-by'] = [attributes['mnt-by']]
                if self._api._mntner not in attributes['mnt-by']:
                    attributes['mnt-by'].append(self._api._mntner)
            else:
                attributes['mnt-by'] = self._api._mntner
            
            object_data = self.__get_ripe_object(attributes)
        logger.debug(object_data)
        json_data = self._api._post(self._type,object_data)
        self._parse_json(json_data)
        return self
    
    def delete(self):
        if not self._api.is_writable():
            raise ValueError('API is not writable, please supply maintainer and password')
        if self._id is None:
            raise ValueError('Cannot delete non-resolved object template')
        return self._api._delete(self._type, self._id)

    def update(self, attributes, update_type = 'replace'):
        if not self._api.is_writable():
            raise ValueError('API is not writable, please supply maintainer and password')
        if self._id is None:
            raise ValueError('Cannot update non-resolved object template')
        if update_type not in ['add', 'replace', 'remove']:
            raise ValueError('update_type must by one of add, replace, remove')
        if isinstance(attributes, str):
            object_data = self.__get_ripe_ojbect_from_string(attributes)
        else:
            update_attributes = {}
            original_attributes = self.get_attributes()
            logger.debug(self.attributes)

            if update_type == 'remove':
                update_attributes = original_attributes
                for attr_name in attributes:
                    if attributes[attr_name] is None:
                        del(update_attributes[attr_name])
                    if isinstance(attributes[attr_name], list):
                        for item in attributes[attr_name]:
                            update_attributes[attr_name].remove(item)
                    else:
                        update_attributes[attr_name].remove(attributes[attr_name])
            else:
                for attr_name in original_attributes:
                    if attr_name in ['created', 'last-modified']:
                        continue
                    if attr_name not in attributes or update_type == 'add':
                        update_attributes[attr_name] = original_attributes[attr_name]
                for attr_name in attributes:
                    if update_type == 'replace' or attr_name not in update_attributes:
                        update_attributes[attr_name] = attributes[attr_name]
                    elif update_type == 'add':
                        if isinstance(attributes[attr_name],list):
                            update_attributes[attr_name] += attributes[attr_name]
                        else:
                            update_attributes[attr_name].append(attributes[attr_name])
                    else:
                        raise Exception('You should not be here! How did you get here?')
            
            # TODO the new style does not really preserve attribute order. Is this a problem?

            # for original_attr in self.attributes:
            #     if original_attr in ['created', 'last-modified']:
            #         continue
            #     if original_attr['name'] not in update_keys:
            #         if self._template_attributes[original_attr['name']].get('cardinality','SINGLE') == 'MULTIPLE':
            #             # TODO - this is weird...
            #             if original_attr['name'] not in attributes:
            #                 update_attributes[original_attr['name']] = [original_attr['value']]
            #             else:
            #                 update_attributes[original_attr['name']].append(original_attr['value'])
            #         else:
            #             update_attributes[original_attr['name']] = original_attr['value']
            #     elif self._template_attributes[original_attr['name']].get('cardinality','SINGLE') == 'MULTIPLE' and update_type == 'add':
            #         if not isinstance(attributes[original_attr['name']],list):
            #             update_attributes[original_attr['name']] = [attributes[original_attr['name']]] + [original_attr['value']]
            #         else:
            #             update_attributes[original_attr['name']] = attributes[original_attr['name']] + [original_attr['value']]
            #     else:
            #         update_attributes[original_attr['name']] = original_attr['value']
            #     # else:
            # if update_type == 'remove':
            #     for attr_name in attributes:
            #         if attributes[attr_name] is None:
            #             continue
            #         else:
            #             update_attributes[attr_name] = self.__getattr__(attr_name)
            #             if isinstance(attributes[attr_name], list):
            #                 for item in attributes[attr_name]:
            #                     update_attributes[attr_name].remove(item)
            #             else:
            #                 update_attributes[attr_name].remove(attributes[attr_name])
            # else:
            #     for attr_name in attributes:
            #         # the option of add and key exists is already handled by previous code
            #         if update_type == 'replace' or (update_type == 'add' and attr_name not in update_attributes):
            #             update_attributes[attr_name] = attributes[attr_name]
            logger.debug(update_attributes)
            object_data = self.__get_ripe_object(update_attributes)
        logger.debug(object_data)
        logger.debug((self._type, self._id))
        json_data = self._api._put(self._type, self._id, object_data)
        self._parse_json(json_data)
        return self


class Maintainer(RipeObject):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)

class Role(RipeObject):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)

class Person(RipeObject):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)

class ASSet(RipeObject):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
    
    def resolve_members(self, seen_ids = None):
        aut_nums = []
        if seen_ids is None:
            seen_ids = []
        members = self.members
        if not isinstance(members,list):
            members = [members]
        # get indirect members
        members += self._api.search(query_string = self.id, type_filter = ['aut-num', 'as-set'], inverse_attribute = 'member-of')
        for member in members:
            if member.id not in seen_ids:
                seen_ids.append(member.id)
                if member.type == 'as-set':
                    aut_nums += member.resolve_members(seen_ids)
                elif member.type == 'aut-num':
                    aut_nums.append(member)
        return aut_nums

    def resolve_routes(self):
        aut_nums = self.resolve_members()
        routes = []
        for aut_num in aut_nums:
            routes += aut_num.resolve_routes()
        return routes

class AutNum(RipeObject):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self._routes = None
    
    def __int__(self):
        return int(self._id.replace('AS',''))
    
    def resolve_routes(self):
        if self._routes is None:
            self._routes = self._api.search(
                query_string = self._id,
                inverse_attribute = 'origin',
                type_filter = ['route','route6']
            )
        return self._routes

class InetNum(RipeObject):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
    
    def get(self, id = None, prefix = None):
        if prefix is not None:
            network = ip_network(prefix, strict = True)
            id = f'{network.network_address} - {network.broadcast_address}'
        return super().get(id)


class Route(RipeObject):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)

object_types = {
    'mntner': Maintainer,
    'role': Role,
    'person': Person,
    'as-set': ASSet,
    'aut-num': AutNum,
    'route': Route,
    'route6': Route,
    'inetnum': InetNum,
}