# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division, unicode_literals

import logging

import os
import ckan.plugins.toolkit as toolkit

from sqlalchemy.orm.exc import NoResultFound

from ..model import ResourceIndexInfo
from .. import task

from ..solr.query import SolrQuery
from ..solr.command import Solr

log = logging.getLogger(__name__)


def _is_target_format(format):
    return format.lower().encode('utf8') in ['csv', 'xsl', 'xlsx', 'geojson']


# @check_access('record_update')
# @validate(schema.exif_extract)
def record_update(context, data_dict):
    # log.debug('### record_update {} ###'.format(data_dict['id']))

    force = data_dict.get('force', False)
    # resource_dict = toolkit.get_action('resource_show')(context, data_dict)

    task_id = None
    index_info = None
    data_dict['url'] = os.path.basename(data_dict['url'])

    try:
        index_info = ResourceIndexInfo.one(resource_id=data_dict['id'])
        if index_info.task_id:
            status = 'inprogress'
            task_id = index_info.task_id
        elif (index_info.url != data_dict['url']):
            status = 'update'
        else:
            status = 'unchanged'
    except NoResultFound:
        status = 'new'

    if not _is_target_format(data_dict['format']):
        status = 'ignored'
        if index_info:
            index_info.delete()
            index_info.commit()
            index_info = None

    log.info('RESOUCE: {}, STATUS: {}'.format(data_dict['id'], status))

    if status in ('new', 'update') or (status != 'ignored' and force):
        if index_info is None:
            index_info = ResourceIndexInfo.create(resource_id=data_dict['id'])

        args = (toolkit.config['__file__'], data_dict)
        title = 'Solr update for resource {}'.format(data_dict['id'])
        job = toolkit.enqueue_job(task.update, args, title=title)
        task_id = index_info.task_id = job.id
        index_info.url = data_dict['url']
        index_info.save()
    return {
        'status': status,
        'task_id': task_id
    }

def record_delete(context, data_dict):
    log.debug('record_delete {}'.format(data_dict['id']))

    try:
        index_info = ResourceIndexInfo.one(resource_id=data_dict['id'])
        index_info.delete().commit()
    except NoResultFound:
        pass


@toolkit.side_effect_free
def record_search(context, data_dict):
    '''
    Search a record data.
    '''

    query = SolrQuery(data_dict)
    solr = Solr('record')
    result = solr.search(query.to_dict())

    return result

