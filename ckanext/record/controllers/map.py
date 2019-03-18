# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division, unicode_literals

import logging

import ckan.plugins.toolkit as toolkit

log = logging.getLogger(__name__)


class MapController(toolkit.BaseController):

    def index(self):

        # log.info('MapController {}'.format(toolkit.request.cookies.get("map_test")))
        # toolkit.response.set_cookie(str('map_test'), 'test', max_age=24*60*60)

        params = toolkit.request.params
        q = params.get('q', '')

        extra_vars = {}
        extra_vars['q'] = q

        return toolkit.render('record/map/index.html', extra_vars=extra_vars)