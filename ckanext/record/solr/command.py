# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import logging
import json
import urllib2
import urllib
from urlparse import urlparse

import ckan.plugins.toolkit as toolkit

log = logging.getLogger(__name__)

ADD_FIELD_TYPE = {
    "add-field-type": [
        {
            "name": "text_2gram",
            "class": "solr.TextField",
            "positionIncrementGap": "100",
            "autoGeneratePhraseQueries": "true",
            "analyzer": {
                "tokenizer": {
                    "class": "solr.NGramTokenizerFactory",
                    "minGramSize": "2",
                    "maxGramSize": "2"}}
        },
    ]
}

REPLACE_FIELD_TYPE = {
    "replace-field-type": [
        {
            "name": "location_rpt",
            "class": "solr.SpatialRecursivePrefixTreeFieldType",
            "spatialContextFactory": "org.locationtech.spatial4j.context.jts.JtsSpatialContextFactory",
            "autoIndex": "true",
            "validationRule": "repairBuffer0",
            "distErrPct": "0.025",
            "maxDistErr": "0.001",
            "distanceUnits": "kilometers"
        }
    ]
}

ADD_FIELD = {
    "add-field": [
        {
            "name": 'fields',
            "type": "text_2gram",
            "stored": True,
            "indexed": True,
            "multiValued": True,
        },

        {
            "name": 'values',
            "type": "text_2gram",
            "stored": True,
            "indexed": True,
            "multiValued": True,
        },

        {
            "name": 'fvs',
            "type": "text_2gram",
            "stored": True,
            "indexed": True,
            "multiValued": True,
        },

        {
            "name": 'row',
            "type": "int",
            "stored": True,
            "indexed": True,
            "multiValued": False,
        },

        {
            "name": 'resource_id',
            "type": "string",
            "stored": True,
            "indexed": True,
            "multiValued": False,
        },

        {
            "name": 'resource_format',
            "type": "string",
            "stored": True,
            "indexed": True,
            "multiValued": False,
        },

        {
            "name": 'package_id',
            "type": "string",
            "stored": True,
            "indexed": True,
            "multiValued": False,
        },

        {
            "name": 'organization_id',
            "type": "string",
            "stored": True,
            "indexed": True,
            "multiValued": False,
        },

        {
            "name": 'geometry',
            "type": "location_rpt",
            "stored": True,
            "indexed": True,
            "multiValued": False,
        },

        {
            "name": 'geometry_type',
            "type": "string",
            "stored": True,
            "indexed": True,
            "multiValued": False,
        },

        {
            "name": 'address',
            "type": "text_2gram",
            "stored": True,
            "indexed": True,
            "multiValued": False,
        },

        {
            "name": "label",
            "type": "text_2gram",
            "stored": True,
            "indexed": True,
            "multiValued": False,
        },

        {
            "name": "description",
            "type": "text_2gram",
            "stored": True,
            "indexed": True,
            "multiValued": False,
        },
    ]
}

ADD_DYNAMIC_FIELD = {
    "add-dynamic-field": [
        {
            "name": "*_date",
            "type": "date",
            "stored": True,
            "indexed": True,
            "multiValued": False,
        }
    ]
}


def solr_q_fields():
    fields = []

    for _field in ADD_FIELD['add-field']:
        if _field['name'] in ['geometry']:
            continue

        fields.append(_field['name'])

    return fields


class Solr:

    def __init__(self, core_name):

        url = toolkit.config['solr_url']
        o = urlparse(url)

        scheme = o.scheme
        hostname = o.hostname
        port = o.port

        self._base_url = '{scheme}://{hostname}:{port}/solr/{core}'.format(scheme=scheme,
                                                                           hostname=hostname,
                                                                           port=port,
                                                                           core=core_name)

    def _get(self, url):

        req = urllib2.Request(url)
        res = urllib2.urlopen(req)
        response = json.loads(res.read())

        return response

    def _post(self, url, values):
        headers = {
            'Content-Type': 'application/json',
        }
        req = urllib2.Request(url, json.dumps(values).encode(), headers)
        res = urllib2.urlopen(req)
        response = json.loads(res.read())

        return response

    def delete(self, resource_id):
        response = None
        try:
            url = '{base_url}/update?commit=true'.format(base_url=self._base_url)

            values = {
                'delete': {'query': 'resource_id:{}'.format(resource_id)}
            }

            response = self._post(url, values)
        except Exception as e:
            log.info('Error: {}'.format(e))

        return response


    def search(self, query):
        response = None

        try:
            q = urllib.urlencode(
                dict([k, v.encode('utf-8') if isinstance(v, unicode) else v] for k, v in query.items()))
            url = '{base_url}/select?{query}'.format(base_url=self._base_url,
                                                     query=q)
            response = self._get(url)

        except Exception as e:
            log.info('Error: {}'.format(e))

        return response

    def post_search(self, query):
        response = None
        try:
            q = {
                'params': query
            }

            url = '{base_url}/query'.format(base_url=self._base_url)
            response = self._post(url, q)

        except Exception as e:
            log.info('Error: {}'.format(e))

        return response

    def store(self, records):
        response = None
        try:
            url = '{base_url}/update?commit=true&indent=true'.format(base_url=self._base_url)
            response = self._post(url, records)
        except Exception as e:
            log.info('Error: {}'.format(e))

        return response

    def schema(self, schema):
        response = None

        try:
            url = '{base_url}/schema'.format(base_url=self._base_url)
            response = self._post(url, schema)
        except Exception as e:
            log.info('Error: {}'.format(e))

        return response
