# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals, division

import logging

from shapely.wkt import loads
from shapely.geometry import shape, mapping

from ..solr.command import solr_q_fields

log = logging.getLogger(__name__)


class SolrQuery:
    def __init__(self, data_dict):

        self._query = {}

        for field, v in data_dict.items():
            if 'q' == field:
                continue

            values = v.split(',')
            for value in values:
                value = value.strip()
                if field not in self._query:
                    self._query[field] = []
                self._query[field].append(value)

        q = data_dict.get('q', '')
        qs = q.split()
        for condition in qs:
            condition = condition.strip()
            if condition == '': continue

            field = None
            value = None

            fv = condition.split(':', 1)
            if len(fv) == 1:
                field = 'values'
                value = fv[0]
            elif len(fv) == 2:
                field = fv[0]
                value = fv[1]

            if field is not None:
                if field not in self._query:
                    self._query[field] = []
                self._query[field].append(value)

        self._query['fl'] = self._query.get('fl', ['fields', 'values', 'fvs', 'resource_id', 'id',
                                                   'organization_id', 'package_id', 'row'])

    def _q(self, query):
        q_fields = solr_q_fields()

        queries = []
        for field, values in self._query.items():

            if field not in q_fields:
                continue

            # log.info('field = {}, values={}'.format(field, values))

            for value in values:
                new_query = '{}:"{}"'.format(field, value)
                queries.append(new_query)

        queries_num = len(queries)

        query['q'] = ' AND '.join(queries) if queries_num > 1 else queries[0] if queries_num == 1 else '*:*'

    def _sort(self, query):

        sort_query = []

        s = self._query.get('sort', '')
        sort_fields = s.split(',')
        for sort_field in sort_fields:
            sort_field = sort_field.strip()

            f_s = sort_field.split()
            if len(f_s) == 2 and f_s[1].lower() in ['asc', 'desc']:
                sort_query.append('{} {}'.format(f_s[0], f_s[1].lower()))

        if len(sort_query) > 0:
            query['sort'] = ','.join(sort_query)

    def _rows(self, query):
        limit = self._query.get('limit', 10)

        try:
            if isinstance(limit, list):
                limit = limit[0]
            limit = min(int(limit), 1000)
        except ValueError:
            limit = 10

        query['rows'] = limit

    def _start(self, query):
        offset = self._query.get('offset', 0)
        try:
            if isinstance(offset, list):
                offset = offset[0]

            offset = int(offset)
        except ValueError:
            offset = 0

        query['offset'] = offset


    def _fl(self, query):
        if 'geometry' in self._query:
            self._query['fl'].append('geometry')

        if 'label' in self._query:
            self._query['fl'].append('label')

        if 'address' in self._query:
            self._query['fl'].append('address')

        fl = self._query.get('fl', [])
        query['fl'] = ','.join(fl)

    def _facet_field(self, query):

        facet_field = self._query.get('facet.field', None)

        if facet_field:
            query['facet'] = 'on'
            query['facet.field'] = facet_field[0]

    def _facet_mincount(self, query):
        mincount = self._query.get('facet.mincount', None)
        if mincount:
            query['facet.mincount'] = mincount[0]

    def to_dict(self):
        query = {}

        self._q(query)
        self._sort(query)
        self._rows(query)
        self._start(query)
        self._fl(query)
        self._facet_field(query)
        self._facet_mincount(query)

        query.update({
            'wt': 'json',
            'echoParams': 'none',
        })

        return query


    def _point(self, lat, lon):

        point = {
            "type": "Point",
            "coordinates": [float(lon), float(lat)]
        }
        return shape(point)

    def _fq(self, param):
        value = None
        code = 200

        if 'lat' in param and 'lon' in param:
            try:
                value = self._point(param['lat'], param['lon'])
                # 'geometry:"Contains({})"'.format(polygon)
                # Intersects,Within,Contains,Disjoint,Equals
            except Exception as e:
                log.debug(e)

        return code, value