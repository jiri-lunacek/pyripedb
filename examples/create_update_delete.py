import logging
logging.basicConfig(level=logging.INFO)
from ripedb import RipeDBApi

api = RipeDBApi(
    source='TEST',
    base_url='https://rest-test.db.ripe.net',
    cache_timeout=3600,
    mntner='pyripedb-demo-mnt',
    password='VerySecurePassword'
)

me = api.mntner.get('pyripedb-demo-mnt')


# let's create a person object
new_person = api.person.create(
    'AUTO-1',   # autogenerate new id
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

print(new_person.id)

new_role = api.role.create('AUTO-1',
    {
        'role': 'Demo role',
        'e-mail': 'abuse@example.com',
        'address': 'Practically everywhere',
        'admin-c': new_person.id
    }
)

print(new_role.id)

# create another person
new_person2 = api.person.create(
    'AUTO-1',   # autogenerate new id
    {               # attributes for the new object
        'person': 'Jane Doe',
        'address': [
            'Under the bridge 1', # they live together
            'Prague',
            'CZ'
        ],
        'phone': '+420601123456' # and share the phone
    }
)

# and add this person to the role
#
# note the update_type parameter
#
new_role.update(attributes = {'admin-c': new_person2.id}, update_type='add')
print(new_role.admin_c)

# now we remove John

new_role.update(attributes = {'admin-c': new_person.id}, update_type='remove')
print(new_role.admin_c)

# and delete his contact

new_person.delete()