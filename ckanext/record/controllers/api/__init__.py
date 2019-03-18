# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals, division

import logging

import urllib2
import urllib
import json

from pylons.decorators import jsonify

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.plugins.toolkit import url_for, redirect_to, request, config
from ckan.lib.base import request, config, abort

from ckan.controllers.api import ApiController as BaseApiController


from ckanext.record.solr.query import SolrQuery
from ckanext.record.solr.command import Solr


log = logging.getLogger(__name__)

# SOLR_HOST = "solr:8983"
# CORE_NAME = 'record'


class APIController(BaseApiController):
    def __init__(self, *args, **kwargs):
        super(APIController, self).__init__(*args, **kwargs)


    def record_search(self, data_dict):
        query = SolrQuery(data_dict)
        solr = Solr('record')
        response = solr.search(query.to_dict())
        return response


# def search(self, query):
    #     response = None
    #
    #     try:
    #         query = urllib.urlencode(
    #             dict([k, v.encode('utf-8') if isinstance(v, unicode) else v] for k, v in query.items()))
    #
    #         url = 'http://{host}/solr/{core}/select?{query}'.format(host=SOLR_HOST, core=CORE_NAME,
    #                                                                 query=query)
    #         req = urllib2.Request(url)
    #         res = urllib2.urlopen(req)
    #         response = json.loads(res.read())
    #
    #     except Exception as e:
    #         log.info('Error: {}'.format(e))
    #
    #     return response
