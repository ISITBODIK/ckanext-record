# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import logging
import datetime
import tempfile
import json

import pysolr
import tabulator
from tabulator import Stream
from tabulator.exceptions import TabulatorException

from shapely.geometry import shape

from sqlalchemy.orm.exc import NoResultFound
from requests.exceptions import RequestException
from requests import Request, Session
from ckan.lib.search import index_for
from ckan.plugins import PluginImplementations, toolkit

from .model import ResourceIndexInfo
from .solr.command import Solr

# from .interfaces import IExtractorPostprocessor

log = logging.getLogger(__name__)

def empty_check(row):
    if row[0] is None:
        return True

    text = "".join(str(row))
    if text == "":
        return True

    return False

def create_record(fields, values, fvs):
    return {
        'fields': fields,
        'values': values,
        'fvs': fvs,
    }

def row_to_record(fields, row):
    data = {}

    fvs = []
    values = []

    for i, field in enumerate(fields):
        value = row[i]

        if type(value) is datetime.datetime:
            value = str(value)

        # log.info("{}: {}".format(type(value), value))

        data[field] = value
        fv = '{}:{}'.format(field, value)
        values.append(value)
        fvs.append(fv)

    return create_record(fields, values, fvs), data


def properties_to_record(properties):
    fields = []
    values = []
    data = {}
    fvs = []

    for field, value in properties.items():
        if isinstance(value, (dict, list)):
            continue

        fields.append(field)
        values.append(value)
        data[field] = value
        fv = '{}:{}'.format(field, value)
        fvs.append(fv)

    return create_record(fields, values, fvs), data


def extend_record(record, data):
    if data.get('緯度', '') != '' and data.get('経度', '') != '':
        lat = data.get('緯度')
        lon = data.get('経度')
        point = {
            "type": "Point",
            "coordinates": [float(lon), float(lat)],
        }

        record['geometry_type'] = point['type'].lower()
        record['geometry'] = str(shape(point))

    if data.get('住所', '') != '':
        address = data.get('住所')
        record['address'] = address

    if data.get('名称', '') != '':
        label = data.get('名称')
        record['label'] = label

    return record


def table_to_records(resource_url, base_record):
    records = []

    try:
        with Stream(resource_url, headers=1) as stream:
            headers = {}
            for i, v in enumerate(stream.headers):
                if v in headers:
                    continue
                headers[v] = i

            fields = stream.headers
            counter = 0

            for row in stream.iter():
                counter += 1

                try:
                    if empty_check(row):
                        continue

                    # log.info("ROW[{}]: {}".format(counter, row))

                    record, data = row_to_record(fields, row)
                    record = extend_record(record, data)
                    record['id'] = '{}_{}'.format(base_record['resource_id'], counter)
                    record['row'] = counter
                    record.update(base_record)
                    records.append(record)

                except Exception as e:
                    log.info('ROW ERROR: {} {}'.format(e, ",".join(row)))


    except TabulatorException as e:
        log.info('Tabulator ERROR: {}'.format(e))
    except Exception as e:
        log.info('ERROR: {}'.format(e))

    return records


def geojson_to_records(resource_url, base_record):

    records = []
    session = Session()
    request = Request('GET', resource_url).prepare()

    geojson = None
    with tempfile.NamedTemporaryFile() as f:
        r = session.send(request, stream=True)
        r.raise_for_status()
        for chunk in r.iter_content(chunk_size=1024):
            f.write(chunk)
        f.flush()
        f.seek(0)

        try:
            geojson = json.load(f)
        except Exception as e:
            log.info('Error: {}'.format(e))

    if geojson is not None:

        counter = 0
        for feature in geojson.get('features', []):
            counter += 1

            try:
                record, data = properties_to_record(feature.get('properties', []))
                record = extend_record(record, data)
                geometry = feature.get('geometry', None)
                if geometry:
                    record['geometry_type'] = geometry.get('type','').lower()
                    record['geometry'] = str(shape(geometry))

                record['id'] = '{}_{}'.format(base_record['resource_id'], counter)
                record['row'] = counter
                record.update(base_record)
                records.append(record)
            except Exception as e:
                log.info('Error: {}'.format(e))



    return records


def create_base_record(package_dict, resource_dict):

    organization_id = package_dict['organization']['id']
    package_id = package_dict['id']
    resource_id = resource_dict['id']
    resource_format = resource_dict['format']

    return {
        'organization_id': organization_id,
        'package_id': package_id,
        'resource_id': resource_id,
        'resource_format': resource_format.lower()
    }

def update(ini_path, resource_dict):
    try:
        package_dict = toolkit.get_action('package_show')(
            {'validate': False}, {'id': resource_dict['package_id']})
    except toolkit.NotAuthorized:
        log.debug(('Not indexing resource {} since it belongs to the ' +
                   'private dataset {}.').format(resource_dict['id'],
                                                 resource_dict['package_id']))
        return

    for resource in package_dict.get('resources', []):
        if resource['id'] == resource_dict['id']:
            resource_dict = resource
            break

    try:
        index_info = ResourceIndexInfo.one(resource_id=resource_dict['id'])
    except NoResultFound:
        index_info = ResourceIndexInfo.create(resource_id=resource_dict['id'])

    try:
        solr = Solr('record')
        solr.delete(resource_dict['id'])

        index_info.indexed = datetime.datetime.now()
        base_record = create_base_record(package_dict, resource_dict)

        if resource_dict['format'] == 'GeoJSON':
            records = geojson_to_records(resource_dict['url'], base_record)
        else:
            records = table_to_records(resource_dict['url'], base_record)

        solr.store(records)

    except RequestException as e:
        log.warn('Failed to download resource data from "{}": {}'.format(
            resource_dict['url'], e.message))
    finally:
        index_info.task_id = None
        index_info.save()

    index_for('package').update_dict(package_dict)
