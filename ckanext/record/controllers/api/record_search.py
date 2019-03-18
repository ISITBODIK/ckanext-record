# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals, division

import logging
from pylons.decorators import jsonify

from ckan.lib.base import request, config, abort

from . import APIController

log = logging.getLogger(__name__)


class Controller(APIController):

    @jsonify
    def get(self):
        param = request.params
        response = self.record_search(param)

        response.get('facet_counts')
        response.get('response')
        response.get('responseHeader')

        log.info(response)

        return response


        # response = {}
        #
        # if status_code == 200:
        #     query.update({
        #         'wt': 'json',
        #         'echoParams': 'none',
        #     })
        #
        #     try:
        #         result = {}
        #
        #         res = self.search(query)
        #         records = []
        #
        #         result['count'] = res['response']['numFound']
        #         response['offset'] = res['response']['start']
        #
        #         for doc in res['response']['docs']:
        #             record_id = doc['id']
        #             resource_id = doc['resource_id']
        #             organization = doc['organization']
        #             package_name = doc['package_name']
        #
        #             # resource_format = doc['resource_format']
        #             resource_name = doc['resource_name']
        #
        #             fields = doc['fields']
        #             values = doc['values']
        #
        #             record = {
        #                 'record_id': record_id,
        #                 'resource_id': resource_id,
        #                 'organization': organization,
        #                 'package_name': package_name,
        #                 'resource_name': resource_name,
        #                 'fields': fields,
        #                 'values': values
        #             }
        #
        #             label = doc.get('label', None)
        #             if label is not None:
        #                 record['label'] = label
        #
        #             address = doc.get('address', None)
        #             if address is not None:
        #                 record['address'] = address
        #
        #             geometry = doc.get('geometry', None)
        #             if geometry is not None:
        #                 geometry = loads(geometry)
        #                 record['geometry'] = mapping(geometry)
        #
        #             records.append(record)
        #
        #         result['records'] = records
        #         response['result'] = result
        #
        #     except Exception as e:
        #         log.debug('Error: {}'.format(e))
        #         status_code = 400
        #         status_success = False
        # else:
        #     status_success = False
        #
        # response['success'] = status_success
        # response['code'] = status_code
        #
        # return response
