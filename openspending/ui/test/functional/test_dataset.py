import csv
import json
from StringIO import StringIO

from .. import ControllerTestCase, url, helpers as h
from openspending.model import Dataset, meta as db

class TestDatasetController(ControllerTestCase):

    def setup(self):
        h.skip_if_stubbed_solr()

        super(TestDatasetController, self).setup()
        h.load_fixture('cra')
        h.make_account('test')
        h.clean_and_reindex_solr()

    def test_index(self):
        response = self.app.get(url(controller='dataset', action='index'))
        assert 'The database contains the following datasets' in response
        assert 'cra' in response

    def test_index_json(self):
        response = self.app.get(url(controller='dataset', action='index', format='json'))
        obj = json.loads(response.body)
        h.assert_equal(len(obj), 1)
        h.assert_equal(obj[0]['name'], 'cra')
        h.assert_equal(obj[0]['label'], 'Country Regional Analysis v2009')
    
    def test_index_hide_private(self):
        cra = Dataset.by_name('cra')
        cra.private = True
        db.session.commit()
        response = self.app.get(url(controller='dataset', action='index', format='json'))
        obj = json.loads(response.body)
        h.assert_equal(len(obj), 0)

    def test_index_csv(self):
        response = self.app.get(url(controller='dataset', action='index', format='csv'))
        r = csv.DictReader(StringIO(response.body))
        obj = [l for l in r]
        h.assert_equal(len(obj), 1)
        h.assert_equal(obj[0]['name'], 'cra')
        h.assert_equal(obj[0]['label'], 'Country Regional Analysis v2009')

    def test_view(self):
        response = self.app.get(url(controller='dataset', action='view', dataset='cra'))
        h.assert_true('Country Regional Analysis v2009' in response,
                      "'Country Regional Analysis v2009' not in response!")
        h.assert_true('36 Entries' in response, "'36 spending entries' not in response!")
    
    def test_view_private(self):
        cra = Dataset.by_name('cra')
        cra.private = True
        db.session.commit()
        response = self.app.get(url(controller='dataset', action='view',
            dataset='cra'), status=403)
        h.assert_false('Country Regional Analysis v2009' in response,
                      "'Country Regional Analysis v2009' not in response!")
        h.assert_false('36 spending entries' in response, "'36 spending entries' not in response!")

    def test_about_has_format_links(self):
        url_ = url(controller='dataset', action='about', dataset='cra')
        response = self.app.get(url_)

        url_ = url(controller='dataset', action='model', dataset='cra',
           format='json')

        h.assert_true(url_ in response,
                      "Link to view page (JSON format) not in response!")

    def test_view_json(self):
        response = self.app.get(url(controller='dataset', action='view',
                                    dataset='cra', format='json'))
        obj = json.loads(response.body)
        h.assert_equal(obj['name'], 'cra')
        h.assert_equal(obj['label'], 'Country Regional Analysis v2009')
    
    def test_model_json(self):
        response = self.app.get(url(controller='dataset', action='model',
                                    dataset='cra', format='json'))
        obj = json.loads(response.body)
        assert 'dataset' in obj.keys(), obj
        h.assert_equal(obj['dataset']['name'], 'cra')
        h.assert_equal(obj['dataset']['label'], 'Country Regional Analysis v2009')

    def test_view_csv(self):
        response = self.app.get(url(controller='dataset', action='view',
                                    dataset='cra', format='csv'))
        r = csv.DictReader(StringIO(response.body))
        obj = [l for l in r]
        h.assert_equal(len(obj), 1)
        h.assert_equal(obj[0]['name'], 'cra')
        h.assert_equal(obj[0]['label'], 'Country Regional Analysis v2009')

    def test_entries(self):
        response = self.app.get(url(controller='entry', action='index',
            dataset='cra'))
        h.assert_true('36 entries' in response, "'36 entries' not in response!")

    def test_entries_json(self):
        response = self.app.get(url(controller='entry', action='index',
                                    dataset='cra', format='json'),
                                params={'limit': '20'})
        obj = json.loads(response.body)
        h.assert_equal(len(obj['facets']), 2)
        #h.assert_equal(obj['stats']['count'], 36)
        h.assert_equal(len(obj['results']), 36)
        h.assert_equal(obj['results'][0]['amount'], 46000000)

    def test_entries_csv(self):
        response = self.app.get(url(controller='entry', action='index',
                                    dataset='cra', format='csv'),
                                params={'limit': '20'})
        r = csv.DictReader(StringIO(response.body))
        obj = [l for l in r]
        h.assert_equal(len(obj), 36)
        h.assert_equal(obj[0]['amount'], '46000000.0')

    def test_explorer(self):
        h.skip("Not Yet Implemented!")

    def test_timeline(self):
        h.skip("Not Yet Implemented!")

    def test_new_form(self):
        response = self.app.get(url(controller='dataset', action='new'), 
            params={'limit': '20'})
        assert "Import a dataset" in response.body
        assert 'Import from a DataHub Dataset' in response.body, response.body
    
    def test_create_dataset(self):
        response = self.app.post(url(controller='dataset', action='create'))
        assert "Import a dataset" in response.body
        assert "Required" in response.body

        params = {'name': 'testds', 'label': 'Test Dataset', 
                  'description': 'I\'m a banana!', 'currency': 'EUR'}
        
        response = self.app.post(url(controller='dataset', action='create'),
                params=params, extra_environ={'REMOTE_USER': 'test'})
        assert "302" in response.status

        ds = Dataset.by_name('testds')
        assert ds.label == params['label'], ds
