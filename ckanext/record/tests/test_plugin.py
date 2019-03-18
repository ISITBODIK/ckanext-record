"""Tests for plugin.py."""

from __future__ import absolute_import, print_function, unicode_literals

import datetime

import mock
from sqlalchemy.orm.exc import NoResultFound

from ckan.model import Package
from ckan.lib.search import index_for
from ckan.tests import factories, helpers

from .helpers import (assert_equal, get_metadata, assert_metadata,
                      assert_no_metadata, assert_package_found,
                      assert_package_not_found)

from ..model import ResourceMetadata


class TestRecordPlugin(object):

    pass

    # def setup(self):
    #     self.app = helpers._get_test_app()
    #
    # def teardown(self):
    #     # Unload the plugin
    #     ckan.plugins.unload('record')
    #     model.repo.rebuild_db()
    #
    # def test_resource_create(self):
    #     user = factories.Sysadmin()
    #     package = factories.Dataset(user=user)
    #
    #     # Set up the plugin
    #     ckan.plugins.load('record')
    #     plugin = ckan.plugins.get_plugin('record')
    #
    #     res = helpers.call_action('resource_create',
    #                               package_id=package['id'],
    #                               name='test-resource',
    #                               url='http://resource.create/',
    #                               apikey=user['apikey'])
    #
    #     print(plugin.counter)


    # def test_resource_controller_plugin_update(self):
    #     user = factories.Sysadmin()
    #     resource = factories.Resource(user=user)
    #
    #     # Set up the plugin here because we don't want the resource creation
    #     # to affect it (because we will only check for changes to update)
    #     ckan.plugins.load('example_iresourcecontroller')
    #     plugin = ckan.plugins.get_plugin('example_iresourcecontroller')
    #
    #     res = helpers.call_action('resource_update',
    #                               id=resource['id'],
    #                               url='http://resource.updated/',
    #                               apikey=user['apikey'])
    #
    #     assert plugin.counter['before_create'] == 0, plugin.counter
    #     assert plugin.counter['after_create'] == 0, plugin.counter
    #     assert plugin.counter['before_update'] == 1, plugin.counter
    #     assert plugin.counter['after_update'] == 1, plugin.counter
    #     assert plugin.counter['before_delete'] == 0, plugin.counter
    #     assert plugin.counter['after_delete'] == 0, plugin.counter
    #
    # def test_resource_controller_plugin_delete(self):
    #     user = factories.Sysadmin()
    #     resource = factories.Resource(user=user)
    #
    #     # Set up the plugin here because we don't want the resource creation
    #     # to affect it (because we will only check for changes to delete)
    #     ckan.plugins.load('example_iresourcecontroller')
    #     plugin = ckan.plugins.get_plugin('example_iresourcecontroller')
    #
    #     res = helpers.call_action('resource_delete',
    #                               id=resource['id'],
    #                               apikey=user['apikey'])
    #
    #     assert plugin.counter['before_create'] == 0, plugin.counter
    #     assert plugin.counter['after_create'] == 0, plugin.counter
    #     assert plugin.counter['before_update'] == 0, plugin.counter
    #     assert plugin.counter['after_update'] == 0, plugin.counter
    #     assert plugin.counter['before_delete'] == 1, plugin.counter
    #     assert plugin.counter['after_delete'] == 1, plugin.counter
    #
    # def test_resource_controller_plugin_show(self):
    #     """
    #     Before show gets called by the other methods but we test it
    #     separately here and make sure that it doesn't call the other
    #     methods.
    #     """
    #     user = factories.Sysadmin()
    #     package = factories.Dataset(user=user)
    #     resource = factories.Resource(user=user, package_id=package['id'])
    #
    #     # Set up the plugin here because we don't want the resource creation
    #     # to affect it (because we will only check for changes to delete)
    #     ckan.plugins.load('example_iresourcecontroller')
    #     plugin = ckan.plugins.get_plugin('example_iresourcecontroller')
    #
    #     res = helpers.call_action('package_show',
    #                               name_or_id=package['id'])
    #
    #     assert plugin.counter['before_create'] == 0, plugin.counter
    #     assert plugin.counter['after_create'] == 0, plugin.counter
    #     assert plugin.counter['before_update'] == 0, plugin.counter
    #     assert plugin.counter['after_update'] == 0, plugin.counter
    #     assert plugin.counter['before_delete'] == 0, plugin.counter
    #     assert plugin.counter['after_delete'] == 0, plugin.counter
    #     assert plugin.counter['before_show'] == 1, plugin.counter

