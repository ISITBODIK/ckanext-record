"use strict";

ckan.module('ckanext-record-search', function ($) {

  function search_resource_id(options, callback, el) {

    var q = options.q;
    var pacakge_id = options.pacakge_id;
    var resources = options.resources;

    if (q === true) {
      q = '';
    }

    var url = '/api/action/record_search?facet.field=resource_id&facet.mincount=1&q=' + q
      + '&package_id=' + pacakge_id + '&limit=0';

    $.ajax({
      url: url,
      type: 'GET',
    })
      .done((data) => {
        var result = data['result'];
        callback(q, result, resources, el)
      })
      .fail((data) => {
        //$('.result').html(data);
        console.log(data);
      })
      .always((data) => {

      });
  }


  function search_record(q, resource_id, callback, el) {

    var url = '/api/action/record_search?q=' + q + '&resource_id=' + resource_id + '&limit=3';

    $.ajax({
      url: url,
      type: 'GET',
    })
      .done((data) => {
        var result = data['result'];
        callback(result, el)
      })
      .fail((data) => {
        //$('.result').html(data);
        console.log(data);
      })
      .always((data) => {

      });
  }


  function recordView(q, result, resources, el) {
    var facet_counts = result['facet_counts'] || [];

    var resource_ids = facet_counts['facet_fields']['resource_id'];

    var response = result['response'];
    var responseHeader = result['responseHeader'];

    var records = response['docs'];
    var num = response['numFound'];

    var resource_counts = {};

    for (var i = 0; i < resource_ids.length; i += 2) {
      var id = resource_ids[i];
      resource_counts[id] = resource_ids[i + 1];
    }

    for (var resource of resources) {
      if (resource_counts[resource.id]) {


        var url = resource.url.split('download');
        var resource_url = url[0];

        var count = resource_counts[resource.id];



        var a = $("<div class=\"list-group-item\"></div>");
        el.append(a);

        var format = resource.format;
        var format_lower = format.toLowerCase();

        a.append("<span class=\"label label-default\" data-format=\"" + format_lower + "\">" + format + "</span>");
        a.append("<a href=\"" + resource_url + "\" class=\"list-group-item-heading\">" + resource.name + "</a>");
        a.append("<span class=\"badge\">" + count + "</span>");

        if (q !== '') {
          var p = $("<p class=\"list-group-item-text summary\"></p>");
          a.append(p);

          search_record(q, resource.id, function (result, p) {

            var docs = result['response']['docs'];

            var text = [];
            for (var doc of docs) {
              text.push(doc['values'].join(','));
            }

            p.append(text.join('<br />'));

          }, p);

        }

      }
    }

  }

  return {
    initialize: function () {
      var el = this.$('.list-group');
      search_resource_id(this.options, recordView, el);
    },

    teardown: function () {
      console.log('teardown');
    },

  };
})
;
