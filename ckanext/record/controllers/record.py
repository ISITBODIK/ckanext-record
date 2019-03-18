# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division, unicode_literals

import logging

from collections import defaultdict, OrderedDict

from urllib import urlencode
from six import string_types

import ckan.lib.helpers as h
import ckan.model as model
import ckan.lib.plugins
import ckan.plugins as p
import ckan.plugins.toolkit as toolkit
import json

log = logging.getLogger(__name__)

asbool = toolkit.asbool
config = toolkit.config
c = toolkit.c
_ = toolkit._
request = toolkit.request
render = toolkit.render
abort = toolkit.abort
NotAuthorized = toolkit.NotAuthorized
check_access = toolkit.check_access
get_action = toolkit.get_action


def _encode_params(params):
    return [(k, v.encode('utf-8') if isinstance(v, string_types) else str(v))
            for k, v in params]


def url_with_params(url, params):
    params = _encode_params(params)
    return url + u'?' + urlencode(params)


def search_url(params, package_type=None):
    if not package_type or package_type == 'dataset':
        url = h.url_for(controller='package', action='search')
    else:
        url = h.url_for('{0}_search'.format(package_type))
    return url_with_params(url, params)


class RecordController(toolkit.BaseController):

    def _package_ids(self, q):

        context = {}
        try:
            context = {'model': model, 'user': c.user,
                       'auth_user_obj': c.userobj}
            check_access('site_read', context)
        except NotAuthorized:
            abort(403, _('Not authorized to see this page'))

        data_dict = {
            'q': q,
            'facet.field': 'package_id',
            'facet.mincount': '1',
            'limit': '0',
            'fl': '',
        }

        package_ids = []
        try:
            result = get_action('record_search')(context, data_dict)
            ids = result['facet_counts']['facet_fields']['package_id']
            package_ids = ids[0::2]

            # package_counts = ids[1::2]
            # package_info = zip(package_ids, package_counts)
            # log.info(package_info)

        except Exception as e:
            log.info(e)

        return package_ids

    def _package_search(self, package_ids, params):

        from ckan.lib.search import SearchError, SearchQueryError

        package_type = 'dataset'

        q = ' OR '.join(["id:{}".format(package_id) for package_id in package_ids])

        c.query_error = False
        page = h.get_page_number(params)

        limit = int(config.get('ckan.datasets_per_page', 20))

        params_nopage = [(k, v) for k, v in params.items()
                         if k != 'page']

        def drill_down_url(alternative_url=None, **by):
            return h.add_url_param(alternative_url=alternative_url,
                                   controller='package', action='search',
                                   new_params=by)

        c.drill_down_url = drill_down_url

        def remove_field(key, value=None, replace=None):
            return h.remove_url_param(key, value=value, replace=replace,
                                      controller='package', action='search',
                                      alternative_url='record')

        c.remove_field = remove_field

        sort_by = params.get('sort', None)
        params_nosort = [(k, v) for k, v in params_nopage if k != 'sort']

        def _sort_by(fields):
            params = params_nosort[:]

            if fields:
                sort_string = ', '.join('%s %s' % f for f in fields)
                params.append(('sort', sort_string))
            return search_url(params, package_type)

        c.sort_by = _sort_by
        if not sort_by:
            c.sort_by_fields = []
        else:
            c.sort_by_fields = [field.split()[0]
                                for field in sort_by.split(',')]

        def pager_url(q=None, page=None):
            params = list(params_nopage)
            params.append(('page', page))
            return search_url(params, package_type)

        c.search_url_params = urlencode(_encode_params(params_nopage))

        try:
            c.fields = []
            c.fields_grouped = {}
            search_extras = {}
            fq = ''
            for (param, value) in params.items():
                if param not in ['q', 'page', 'sort'] \
                        and len(value) and not param.startswith('_'):
                    if not param.startswith('ext_'):
                        c.fields.append((param, value))
                        fq += ' %s:"%s"' % (param, value)
                        if param not in c.fields_grouped:
                            c.fields_grouped[param] = [value]
                        else:
                            c.fields_grouped[param].append(value)
                    else:
                        search_extras[param] = value

            context = {'model': model, 'session': model.Session,
                       'user': c.user, 'for_view': True,
                       'auth_user_obj': c.userobj}

            search_all_type = config.get(
                'ckan.search.show_all_types', 'dataset')
            search_all = False

            try:
                search_all = asbool(search_all_type)
                search_all_type = 'dataset'
            except ValueError:
                search_all = True

            if not package_type:
                package_type = 'dataset'

            if not search_all or package_type != search_all_type:
                fq += ' +dataset_type:{type}'.format(type=package_type)

            facets = OrderedDict()

            default_facet_titles = {
                'organization': _('Organizations'),
                'groups': _('Groups'),
                'tags': _('Tags'),
                'res_format': _('Formats'),
                'license_id': _('Licenses'),
            }

            for facet in h.facets():
                if facet in default_facet_titles:
                    facets[facet] = default_facet_titles[facet]
                else:
                    facets[facet] = facet

            # Facet titles
            for plugin in p.PluginImplementations(p.IFacets):
                facets = plugin.dataset_facets(facets, package_type)

            c.facet_titles = facets

            data_dict = {
                'q': q,
                'fq': fq.strip(),
                'facet.field': facets.keys(),
                'rows': limit,
                'start': (page - 1) * limit,
                'sort': sort_by,
                'extras': search_extras,
                'include_private': asbool(config.get(
                    'ckan.search.default_include_private', False)),
            }

            query = get_action('package_search')(context, data_dict)
            c.sort_by_selected = query['sort']

            c.page = h.Page(
                collection=query['results'],
                page=page,
                url=pager_url,
                item_count=query['count'],
                items_per_page=limit
            )

            c.search_facets = query['search_facets']
            c.page.items = query['results']

        except SearchQueryError as se:
            log.info('Dataset search query rejected: %r', se.args)
            abort(400, _('Invalid search query: {error_message}')
                  .format(error_message=str(se)))
        except SearchError as se:
            log.error('Dataset search error: %r', se.args)
            c.query_error = True
            c.search_facets = {}
            c.page = h.Page(collection=[])
        except NotAuthorized:
            abort(403, _('Not authorized to see this page'))

        c.search_facets_limits = {}
        for facet in c.search_facets.keys():
            try:
                limit = int(params.get('_%s_limit' % facet,
                                       int(config.get('search.facets.default', 10))))
            except ValueError:
                abort(400, _('Parameter "{parameter_name}" is not '
                             'an integer').format(
                    parameter_name='_%s_limit' % facet))
            c.search_facets_limits[facet] = limit

        return {
            'resource_filter': self.resource_filter,
            'dataset_type': str(package_type),
            'page': c.page,
            'search_facets_limits': c.search_facets_limits,
            'search_facets': c.search_facets,
            'facet_titles': c.facet_titles,
            'fields_grouped': c.fields_grouped,
            'translated_fields': c.translated_fields,
            'remove_field': c.remove_field,
            'sort_by_selected': c.sort_by_selected
        }

    def resource_filter(self, resources):
        return json.dumps([{
            'description': resource['description'],
            'url': resource['url'],
            'format': resource['format'],
            'id': resource['id'],
            'name': resource['name'],
        } for resource in resources])

    def search(self):
        params = request.params
        q = params.get('q', '')
        package_ids = self._package_ids(q)

        if len(package_ids) > 0:
            extra_vars = self._package_search(package_ids, request.params)
        else:
            page = h.Page(
                collection=[],
                page=0,
                url=None,
                item_count=0,
                items_per_page=0
            )
            extra_vars = {'dataset_type': str('dataset'), 'page': page}

        extra_vars['q'] = q

        return render('record/search.html', extra_vars=extra_vars)
