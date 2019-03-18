# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals, division

import logging

from pylons.decorators import jsonify

from ckan.lib.base import request, config, abort

from shapely.wkt import loads
from shapely.geometry import shape, mapping

from . import APIController

log = logging.getLogger(__name__)


class Controller(APIController):

    def _convert_query(self, query):
        q = None
        v = query.split(':')

        if len(v) == 2:
            if v[0] != '' and v[1] == '':
                q = '{}:"{}"'.format('_fields', v[0])
            elif v[0] != '' and v[1] != '':
                q = '{}:"{}"'.format('_fvs', query)

        return q

    def _point(self, param):
        value = None
        code = 200

        if 'lat' in param and 'lon' in param:
            try:
                _lon = float(param.get('lon'))
                _lat = float(param.get('lat'))

                point = {
                    "type": "Point",
                    "coordinates": [_lon, _lat]
                }
                value = shape(point)
            except ValueError as e:
                log.debug(e)
                code = 400

        return value, code

    def _resource_id(self, param):
        if 'resource_id' in param:
            resource_id = param.get('resource_id')
            index = "geo_shape-{}".format(resource_id)
            param_check = True
        pass

    def _query(self, param):
        queries = []

        if 'query' in param:
            for query in param.get('query', '').split(','):
                new_query = self._convert_query(query)
                if new_query is not None:
                    queries.append(new_query)

        return queries

    @jsonify
    def get(self):
        status = {}
        status['code'] = 200
        status['msg'] = 'Success'

        param = request.params

        fl = ['_fvs', 'resource_id', 'id']

        query = {}

        point, code = self._point(param)
        status['code'] = max(code, status['code'])
        if point is not None:
            query['fq'] = 'geometry:"Contains({})"'.format(point)

        queries = self._query(param)
        if 'resource_id' in param:
            queries.append('resource_id:{}'.format(param.get('resource_id')))

        q_num = len(queries)
        if q_num == 1:
            query['q'] = queries[0]
        elif q_num > 1:
            query['q'] = ' AND '.join(queries)

        if len(query) == 0:
            status['code'] = 400

        query.update({
            'wt': 'json',
            'echoParams': 'none',
            'start': 0,
            'rows': 100,
        })

        if 'from' in param:
            try:
                query['start'] = int(param.get('from'))
            except ValueError:
                status['code'] = 400

        if 'size' in param:
            try:
                size = min(int(param.get('size')), 1000)
                query['rows'] = size
            except ValueError:
                status['code'] = 400

        if 'geometry' in param:
            fl.append('geometry')

        query['fl'] = ','.join(fl)

        response = {}
        if status['code'] == 200:

            try:
                res = self.search(query)
                results = []

                response['total'] = res['response']['numFound']
                response['from'] = res['response']['start']

                for doc in res['response']['docs']:
                    fvs = doc['_fvs']
                    resource_id = doc['resource_id']
                    record_id = doc['id']
                    source = {}
                    geometry = doc.get('geometry', None)
                    if geometry is not None:
                        source['type'] = 'Feature'
                        geometry = loads(geometry)
                        source['geometry'] = mapping(geometry)

                    properties = {}
                    for fv in fvs:
                        field, value = fv.split(':')
                        properties[field] = value

                    source['properties'] = properties
                    result = {
                        'record_id': record_id,
                        'resource_id': resource_id,
                        'source': source
                    }

                    results.append(result)

                response['results'] = results

            except Exception as e:
                log.debug(e)
                status['code'] = 400
                status['msg'] = 'Bad Query'

        elif status['code'] == 400:
            status['msg'] = 'Parameter Error'

        response['status'] = status

        return response
