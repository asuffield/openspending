from nose.tools import *
from nose.plugins.skip import SkipTest
from mock import Mock, patch, MagicMock

import os as _os
import csv

from openspending.model import Dataset, meta as db
from openspending.lib import solr_util as _solr

TEST_ROOT = _os.path.dirname(__file__)

def load_fixture(name, manager=None):
    """
    Load fixture data into the database.
    """
    import json
    from openspending.etl.validation.types import convert_types
    fh = open(fixture_path('%s.js' % name), 'r')
    data = json.load(fh)
    fh.close()
    dataset = Dataset(data)
    if manager is not None:
        dataset.managers.append(manager)
    db.session.add(dataset)
    db.session.commit()
    dataset.generate()
    fh = open(fixture_path('%s.csv' % name), 'r')
    reader = csv.DictReader(fh)
    for row in reader:
        entry = convert_types(data['mapping'], row)
        dataset.load(entry)
    fh.close()
    dataset.commit()
    return dataset

def fixture_file(name):
    """Return a file-like object pointing to a named fixture."""
    return open(fixture_path(name))

def fixture_path(name):
    """
    Return the full path to a named fixture.

    Use fixture_file rather than this method wherever possible.
    """
    return _os.path.join(TEST_ROOT, 'fixtures', name)

def clean_all():
    clean_db()
    clean_solr()

def make_account(name='test', fullname='Test User', 
                 email='test@example.com'):
    from openspending.model import Account
    account = Account()
    account.name = name
    account.fullname = fullname
    account.email = email
    db.session.add(account)
    db.session.commit()
    return account

def clean_db():
    db.session.rollback()
    db.metadata.drop_all()

def clean_solr():
    '''Clean all entries from Solr.'''
    s = _solr.get_connection()
    s.delete_query('*:*')
    s.commit()

def clean_and_reindex_solr():
    '''Clean Solr and reindex all entries in the database.'''
    clean_solr()
    for dataset in db.session.query(Dataset):
        _solr.build_index(dataset.name)

def skip_if_stubbed_solr():
    if type(_solr.get_connection()) == _solr._Stub:
        skip("Not running test with stubbed Solr.")

def skip(*args, **kwargs):
    raise SkipTest(*args, **kwargs)


