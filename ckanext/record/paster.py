# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import logging
from ckan.lib.cli import CkanCommand
from .solr.command import Solr, ADD_DYNAMIC_FIELD, ADD_FIELD, ADD_FIELD_TYPE, REPLACE_FIELD_TYPE

log = logging.getLogger(__name__)


class RecordCommand(CkanCommand):
    """
    Base class for ckanext-record Paster commands.
    """
    pass


class InitCommand(RecordCommand):
    """
    Initialize database tables.
    """

    max_args = 0
    min_args = 0
    usage = __doc__
    summary = __doc__.strip().split('\n')[0]

    def command(self):
        self._load_config()
        from .model import create_tables
        create_tables()
        solr = Solr('record')

        print(solr.schema(ADD_FIELD_TYPE))
        print(solr.schema(REPLACE_FIELD_TYPE))
        print(solr.schema(ADD_FIELD))
        # print(solr.schema(ADD_DYNAMIC_FIELD))
