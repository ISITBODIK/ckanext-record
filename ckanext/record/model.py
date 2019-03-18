# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import logging
from sqlalchemy import Column, ForeignKey, Table, types
from ckan.model.domain_object import DomainObject
from ckan.model.meta import mapper, metadata

log = logging.getLogger(__name__)

resource_index_info_table = None
RESOURCE_INDEX_INFO_TABLE_NAME = 'ckanext_record_resource_index_info'


class ResourceIndexInfo(DomainObject):
    @classmethod
    def filter_by(cls, **kwargs):
        return cls.Session.query(cls).filter_by(**kwargs)

    @classmethod
    def one(cls, **kwargs):
        return cls.filter_by(**kwargs).one()

    @classmethod
    def create(cls, **kwargs):
        instance = cls(**kwargs)
        cls.Session.add(instance)
        cls.Session.commit()
        return instance

    def delete(self):
        super(ResourceIndexInfo, self).delete()
        return self


def setup():
    global resource_index_info_table
    if resource_index_info_table is None:
        resource_index_info_table = Table(RESOURCE_INDEX_INFO_TABLE_NAME, metadata,
                                          Column('resource_id', types.UnicodeText,
                                                 ForeignKey('resource.id',
                                                            ondelete='CASCADE',
                                                            onupdate='CASCADE'),
                                                 nullable=False,
                                                 primary_key=True),
                                          Column('indexed', types.DateTime),
                                          Column('url', types.UnicodeText),
                                          Column('task_id', types.UnicodeText)
                                          )
        mapper(ResourceIndexInfo, resource_index_info_table)
    else:
        log.debug('Resource index info table already defined')


def create_tables():
    setup()
    if not resource_index_info_table.exists():
        log.info('Creating resource index info table')
        resource_index_info_table.create()
    else:
        log.info('Resource index info table already exists')
