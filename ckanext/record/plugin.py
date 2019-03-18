# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function #, unicode_literals

import logging
import os
import sys
import errno
import socket

from ckan.logic import NotFound

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from .logic import action
from . import model

# from . import interfaces
# from .exception import RecordException


log = logging.getLogger(__name__)


def _is_resource(data_dict):
    return 'package_id' in data_dict


class RecordPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurable)

    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)

    # plugins.implements(plugins.IDatasetForm, inherit=False)

    # plugins.implements(plugins.IOrganizationController, inherit=False)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IResourceController, inherit=True)
    plugins.implements(plugins.IActions)

    # plugins.implements(plugins.IAuthFunctions)
    # These record how many times methods that this plugin's methods are
    # called, for testing purposes.

    '''
    IConfigurable
    Initialization hook for plugins.
    '''

    def configure(self, config_):
        model.setup()

    '''
    IConfigurer
    '''

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'record')

        # self._start_debug_client(config_)

    '''
    IRoutes
    '''

    def after_map(self, map):

        # map.connect('/api/geo_shape',
        #             controller='ckanext.record.controllers.api.geo_shape:Controller',
        #             action='get')

        # map.connect('/api/record_search',
        #             controller='ckanext.record.controllers.api.record_search:Controller',
        #             action='get')

        map.connect('record_index', '/record',
                    controller='ckanext.record.controllers.record:RecordController',
                    action='search')

        map.connect('record_map_index', '/map',
                    controller='ckanext.record.controllers.map:MapController',
                    action='index')

        return map

    '''
    IOrganizationController

    read(entity)
        Called after IOrganizationController.before_view inside organization_read.

    create(entity)
        Called after organization had been created inside organization_create.

    edit(entity)
        Called after organization had been updated inside organization_update.

    delete(entity)
        Called before commit inside organization_delete.

    before_view(pkg_dict)
        Extensions will recieve this before the organization gets displayed. The dictionary passed will be the one that gets sent to the template.

    To Do: 組織名を修正したとき、インデックスの値を更新する必要あり。
    '''

    '''
    IResourceController/IPackageController
    '''

    # def before_create(self, context, data_dict):
    #     pass

    def after_create(self, context, data_dict):
        if _is_resource(data_dict):
            toolkit.get_action('record_update')(context, data_dict)
        else:
            pkg_dict = toolkit.get_action('package_show')(context, data_dict)
            if pkg_dict.get('private', True) is False:
                for resource_dict in pkg_dict.get('resources', []):
                    toolkit.get_action('record_update')(context, resource_dict)

    def after_update(self, context, data_dict):
        if _is_resource(data_dict):
            data_dict['force'] = True
            toolkit.get_action('record_update')(context, data_dict)
        else:
            pkg_dict = toolkit.get_action('package_show')(context, data_dict)
            if pkg_dict.get('private', True):
                for resource_dict in pkg_dict.get('resources', []):
                    try:
                        toolkit.get_action('record_delete')(context, resource_dict)
                    except toolkit.ObjectNotFound:
                        pass
            else:
                for resource_dict in pkg_dict.get('resources', []):
                    toolkit.get_action('record_update')(context, resource_dict)

    '''
    IResourceController
    '''

    def before_delete(self, context, resource, resources):
        ctx = dict(context, ignore_auth=True)
        try:
            toolkit.get_action('record_delete')(ctx, resource)
        except NotFound:
            pass

    '''
    IPackageController
    '''

    def before_index(self, pkg_dict):
        log.info('### before_index ###')
        return pkg_dict

    '''
    IActions
    '''

    def get_actions(self):
        return {
            'record_delete': action.record_delete,
            'record_update': action.record_update,
            'record_search': action.record_search,
        }

    '''
    IAuthFunctions
    '''

    # def get_auth_functions(self):
    #     return {
    #         # 'exif_delete': auth.exif_delete,
    #         'record_extract': auth.exif_extract,
    #         # 'exif_list': auth.exif_list,
    #         # 'exif_show': auth.exif_show,
    #     }

    '''
        Debug Setting for PyCharm
    '''

    def _start_debug_client(self, config):
        egg_dir = config.get('debug.remote.egg_dir', None)
        # If we have an egg directory, add the egg to the system path
        # If not set, user is expected to have made pycharm egg findable
        if egg_dir:
            sys.path.append(os.path.join(egg_dir, 'pycharm-debug.egg'))

        try:
            import pydevd
        except ImportError:
            pass

        debug = True
        host_ip = 'host.docker.internal'
        host_port = 8888
        stdout = True
        stderr = True
        suspend = False

        if debug:
            # We don't yet have a translator, so messages will be in english only.
            log.info("Initiating remote debugging session to {}:{}".format(host_ip, host_port))
            try:
                pydevd.settrace(host_ip, port=int(host_port), stdoutToServer=stdout, stderrToServer=stderr,
                                suspend=suspend)
            except NameError:
                log.warning("debug.enabled set to True, but pydevd is missing.")
            except SystemExit:
                log.warning("Failed to connect to debug server; is it started?")
            except socket.error as error:
                if error.errno == errno.ECONNREFUSED:
                    log.error("Connection Refused!")
                else:
                    raise
