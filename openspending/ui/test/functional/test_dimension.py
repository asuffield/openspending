import csv
import json
from StringIO import StringIO

from .. import ControllerTestCase, url, helpers as h
from openspending.ui.lib.helpers import member_url
from openspending.model import Dataset, CompoundDimension, meta as db

class TestDimensionController(ControllerTestCase):

    def setup(self):
        h.skip_if_stubbed_solr()
        
        super(TestDimensionController, self).setup()
        h.load_fixture('cra')
        h.clean_and_reindex_solr()
        self.cra = Dataset.by_name('cra')
        for dimension in self.cra.dimensions:
            if isinstance(dimension, CompoundDimension) and \
                    dimension.name == 'cofog1':
                members = list(dimension.members(
                    dimension.alias.c.name=='3',
                    limit=1))
                self.member = members.pop()
                break


    def test_index(self):
        response = self.app.get(url(controller='dimension', dataset='cra',
                                    action='index'))
        h.assert_true('Paid by' in response, "'Paid by' not in response!")
        h.assert_true('Paid to' in response, "'Paid to' not in response!")
        h.assert_true('Programme Object Group' in response, "'Programme Object Group' not in response!")
        h.assert_true('Central government' in response, "'Central government' not in response!")

    def test_index_descriptions(self):
        response = self.app.get(url(controller='dimension', dataset='cra',
                                    action='index'))
        h.assert_true('The entity that the money was paid from.' in response,
                      "'The entity that the money was paid from.' not in response!")
        h.assert_true('Central government, local government or public' in response,
                      "'Central government, local government or public' not in response!")

    def test_index_json(self):
        response = self.app.get(url(controller='dimension', dataset='cra',
                                    action='index', format='json'))
        obj = json.loads(response.body)
        h.assert_equal(len(obj), 12)
        h.assert_equal(obj[0]['key'], 'cap_or_cur')
        h.assert_equal(obj[0]['label'], 'CG, LG or PC')

    def test_index_csv(self):
        h.skip("CSV dimension index not yet implemented!")

    def test_view(self):
        response = self.app.get(url(controller='dimension', dataset='cra',
                                    action='view', dimension='from'))
        h.assert_true('Paid by' in response, "'Paid by' not in response!")
        h.assert_true('The entity that the money was paid from.' in response,
                      "'The entity that the money was paid from.' not in response!")
        h.assert_true('Department for Work and Pensions' in response,
                      "'Department for Work and Pensions' not in response!")

    def test_view_json(self):
        response = self.app.get(url(controller='dimension', dataset='cra',
                                    action='view', dimension='from',
                                    format='json'))
        obj = json.loads(response.body)
        #h.assert_equal(obj['meta']['dataset'], 'cra')
        h.assert_equal(obj['meta']['key'], 'from')
        h.assert_equal(len(obj['values']), 5)
        # FIXME: why are these doubly-nested lists?
        h.assert_equal(obj['values'][0][0]['label'], 'Department for Work and Pensions')

    def test_view_csv(self):
        h.skip("CSV dimension view not yet implemented!")

    def test_view_member_html(self):
        url_ = member_url(self.cra.name, 'cofog1', self.member)
        result = self.app.get(url_)

        h.assert_equal(result.status, '200 OK')

        # Links to entries json and csv and entries listing
        h.assert_true('<a href="/cra/cofog1/3.json">'
                        in result)
        h.assert_true('<a href="/cra/cofog1/3/entries">Search</a>'
                        in result)

    def test_view_member_json(self):
        url_ = member_url(self.cra.name, 'cofog1', self.member, format='json')
        result = self.app.get(url_)

        h.assert_equal(result.status, '200 OK')
        h.assert_equal(result.content_type, 'application/json')

        json_data = json.loads(result.body)
        h.assert_equal(json_data['name'], u'3')
        h.assert_equal(json_data['label'], self.member['label'])
        h.assert_equal(json_data['id'], self.member['id'])

    def test_view_entries_json(self):
        url_ = url(controller='dimension', action='entries', format='json',
                   dataset=self.cra.name,
                   dimension='cofog1',
                   name=self.member['name'])
        result = self.app.get(url_)

        h.assert_equal(result.status, '200 OK')
        h.assert_equal(result.content_type, 'application/json')

        json_data = json.loads(result.body)
        h.assert_equal(len(json_data['results']), 5)

    def test_view_entries_csv(self):
        url_ = url(controller='dimension', action='entries', format='csv',
                   dataset=self.cra.name,
                   dimension='cofog1',
                   name=self.member['name'])
        result = self.app.get(url_)

        h.assert_equal(result.status, '200 OK')
        h.assert_equal(result.content_type, 'text/csv')
        h.assert_true('amount,' in result.body)  # csv headers
        h.assert_true('id,' in result.body)  # csv headers

    def test_view_entries_html(self):
        url_ = url(controller='dimension', action='entries', format='html',
                   dataset=self.cra.name,
                   dimension='cofog1',
                   name=self.member['name'])
        result = self.app.get(url_)
        h.assert_equal(result.status, '200 OK')
        h.assert_equal(result.content_type, 'text/html')
        h.assert_true(('Public order and safety') in result)
        h.assert_equal(result.body.count('details'), 5)
