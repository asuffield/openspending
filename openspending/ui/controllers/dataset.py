import logging

from pylons import request, response, tmpl_context as c
from pylons.i18n import _

from openspending import model
from openspending.model import meta as db
from openspending.plugins.core import PluginImplementations
from openspending.plugins.interfaces import IDatasetController
from openspending.lib.csvexport import write_csv
from openspending.lib.jsonexport import to_jsonp
from openspending.lib import json
from openspending.ui.lib import helpers as h
from openspending.ui.lib.base import BaseController, render, abort
from openspending.ui.lib.browser import Browser
from openspending.ui.lib.views import View, ViewState, handle_request
from openspending.ui.lib.color import rgb_rainbow
from openspending.validation.currency import CURRENCIES

log = logging.getLogger(__name__)

class DatasetController(BaseController):

    extensions = PluginImplementations(IDatasetController)

    model = model.Dataset

    def index(self, format='html'):
        c.results = model.Dataset.all_by_account(c.account)
        for item in self.extensions:
            item.index(c, request, response, c.results)

        if format == 'json':
            return to_jsonp(map(lambda d: d.as_dict(),
                                c.results))
        elif format == 'csv':
            results = map(lambda d: d.as_dict(), c.results)
            return write_csv(results, response)
        else:
            return render('dataset/index.html')

    def new(self):
        c.currencies = [(k, v['name']) for k,v in CURRENCIES.items()]
        c.currencies = sorted(c.currencies, key=lambda (k,v): v)
        return render('dataset/new.html')

    def create(self):
        pass

    def view(self, dataset, format='html'):
        self._get_dataset(dataset)
        c.num_entries = len(c.dataset)

        handle_request(request, c, c.dataset)

        if c.view is None:
            url = h.url_for(controller='entry', action='index',
                        dataset=c.dataset.name)
            c.browser = Browser(c.dataset, request.params, url=url)
            c.browser.facet_by_dimensions()

        for item in self.extensions:
            item.read(c, request, response, c.dataset)

        if format == 'json':
            return to_jsonp(c.dataset.as_dict())
        elif format == 'csv':
            return write_csv([c.dataset.as_dict()], response)
        else:
            return render('dataset/view.html')

    def bubbles(self, name, breakdown_field, drilldown_fields, format="html"):
        c.drilldown_fields = json.dumps(drilldown_fields.split(','))
        self._get_dataset(name)
        c.dataset_name = c.dataset.name

        # TODO: make this a method
        c.template = 'dataset/view_bubbles.html'

        curs = model.entry.find({'dataset.name':name})# , {breakdown_field: True})
        breakdown_names = list(set([ i[breakdown_field]['name'] for i in curs ]))

        count = len(breakdown_names)

        styles = [ s for s in rgb_rainbow(count) ]
        breakdown_styles = dict([ (breakdown_names[n], styles[n]) for n in range(0, count) ])
        c.breakdown_styles = [ "'%s' : { color: '%s' }," % (k, v) for k, v in breakdown_styles.iteritems() ]
        c.breakdown_field = breakdown_field

        handle_request(request, c, c.dataset)
        if c.view is None:
            self._make_browser()

        if hasattr(c, 'time'):
            delattr(c, 'time') # disable treemap(!)

        return render(c.template)

    def explorer(self, name=None):
        self._get_dataset(name)
        c.keys_meta = dict([(d.name, {"label": d.label,
                "description": d.description})
                for d in c.dataset.dimensions])
        c.breakdown_keys = c.keys_meta.keys()[:3]
        c.keys_meta_json = json.dumps(c.keys_meta)
        c.breakdown_keys_json = json.dumps(c.breakdown_keys)
        return render('dataset/explorer.html')

    def timeline(self, name):
        self._get_dataset(name)
        c.dataset = model.Dataset.by_name(name)
        view = View.by_name(c.dataset, "default")
        viewstate = ViewState(c.dataset, view, None)
        data = []
        meta = []
        for entry, year_data in viewstate.aggregates:
            meta.append({"label": entry.get("label"),
                         "description": entry.get("description", ""),
                         "name": entry.get("name"),
                         "index": len(meta),
                         "taxonomy": entry.get("taxonomy")})
            sorted_year_data = sorted(year_data.items(), key=lambda kv: kv[0])
            data.append([{"x": k, "y": v,
                          "meta": len(meta) - 1} for
                         k, v in sorted_year_data])
        c.data = json.dumps(data)
        c.meta = json.dumps(meta)
        return render('dataset/timeline.html')

