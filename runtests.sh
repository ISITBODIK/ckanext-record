#!/usr/bin/env bash

# Create database tables if necessary
# paster --plugin=ckanext-exif init -c test.ini

nosetests --nologcapture --nocapture --ckan \
          --with-pylons=test.ini \
          ckanext/record/tests
