# pyripedb

This project makes a pythonic view on REST api of RIPE database.

You can find original API docoumentation here https://github.com/RIPE-NCC/whois/wiki/WHOIS-REST-API

## Installing

    pip3 install .

## Usage

Find examples of usage in *examples* folder.

With this API implementation you should be able to easily search, lookup, create, update and delete RIPE DB objects.

The project uses request caching by default using https://pypi.org/project/requests-cache/
To disable the caching, just call the constructor with *cache_timeout = None*

### Lookups and searches

The approach tries to be as pythonic as possible. Therefore each RIPE DB object is represented by a python object *RipeObject* (or descendat class).
Also the API provides abstraction over database object types through the API object properties.
So to get a person object with nic-hdl *JOSM1-RIPE* you do

    my_person = api.person.get('JOSM1-RIPE')

To get attributes of the RIPE DB object, you just get an attribute of the corresponding Python object

    my_person.person
    my_person.address
    my_person.nic_hdl

Please note that

1. Attributes that allow multiple values are returned as a list of values
2. Hyphen characters (*-*) are replaced by underscore (*_*) whne coming to Python API. The replacement works both ways

The RipeDBApi object offers a *search* method. This persorms a search on RIPE DB and returns a list objects.

    api.search('John Smith')

The usual additional parameters are also accepted (again hyphens to undescores).

    api.search('John Smith', type_filter = 'person')
    api.search('JOSM1-RIPE', type_filter = ['role', 'domain', 'inetnum'], inverse_attribute = 'tech-c')

### Creating and updating objects

While lookups are free for all, to create, update and delete objects in the RIPE DB, you need to have a valid maintainer and password, which you enter into *RipeDBApi* constructor.

    api = RipeDBApi(mntner='pyripedb-demo-mnt', password='VerySecurePassword')

To create an object in RIPE DB just call

    new_person = api.person.create(
        'JODO1-RIPE',   # new id as the first parameter
        {               # attributes for the new object
            'person': 'John Doe',
            'address': [
                'Under the bridge 1',
                'Prague',
                'CZ'
            ],
            'phone': '+420601123456' # everybody has a cell phone now, even John Doe living under the bridge
        }
    )

This returns a new object that can further be updated

    new_person.update({
        'phone': '+420000000000' # John Doe lost his phone :'(
    })

### Deleting objects

Deleting is always the easiest part isn't it? But the consequences...
To delete an object just call

    new_person.delete()

To delete a specific object by id from RIPE DB

    obj = api.inetnum.get('10.0.0.0 - 10.0.255.255').delete()

To delete all objects maintained by you, do (or maybe don't)

    for obj in api.search('pyripedb-demo-mnt', inverse_attribute = 'mnt-by'):
        obj.delete()

## Testing

Testing read access is perfectly safe. If you're not sure, just dont give your maintainer id and password.
RIPE DB will not allow writing without it anway.

It's also a good idea to set cache timeout to a greater value. Speeds up the debugging and will not get you blocked by poosible rate limiting from RIPE.

    api = RipeDBApi(
        cache_timeout = 3600
    )

For write operations testing, RIPE offers access to TEST database. So the easiest way to test your code is:

1. Go to https://apps-test.db.ripe.net/db-web-ui/webupdates/select (you need ripe.net account)
2. Create *role and maintainer pair*
3. Set MD5 password authentication for your newly created maintainer
4. Put maintainer id and password to RipeDBApi constructor
5. Knock your self out

To use the test database, set *source* and *base_url* parameters of the API constructor.

    api = RipeDBApi(
        source='TEST',
        base_url='https://rest-test.db.ripe.net',
        cache_timeout=3600,
        mntner='pyripedb-demo-mnt',
        password='VerySecurePassword'
    )

# State of the project

This project is brand new product of inspiration and Covid19 time boredom.
It may be work in progress for quite a while...

However it should be safe to use it all the basic functionality is tested (at least a bit).

## TODO

There's always things to do.
Right now they include

* Adding classes for all RIPE DB object types
* Implementing resolve for other *set* object types
* Code cleanup and object method, property protection
* Testing and documenting *raw text* updates
* Implementing *attribute list* update
* Preparing a PIP distribution release

## Contributing

Feel free to fork and modify the project.

If you plan to do any of those things mentioned above or have a great (or even not that great) idea what can be done, let me know.

