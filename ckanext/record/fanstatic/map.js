"use strict";

const TYPE_NAVIGATE = 0;
const TYPE_RELOAD = 1;
const TYPE_BACK_FORWARD = 2;

ckan.module('ckanext-record-map', function ($) {

  function mapInit() {
    var location = [33.5988733, 130.3172089];
    var zoom = 10;

    if (window.performance.navigation.type === TYPE_RELOAD) {

      $.removeCookie('current');
    }

    else {
      var currentValue = $.cookie("current");
      if (currentValue) {
        var current = JSON.parse(currentValue);
        location = current['center'];
        zoom = current['zoom'];
      }
    }

    var map = L.map('mapid').setView(location, zoom);

    L.tileLayer('https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png', {
      attribution: '<a href=\'https://maps.gsi.go.jp/development/ichiran.html\' target=\'_blank\'>地理院タイル</a>',
      maxZoom: 18,
    }).addTo(map);

    return map;
  }

  function ckanAPI(self, callback, url) {
    $.ajax({
      url: url,
      type: 'GET',
    }).done((data) => {
      var result = data['result'];
      callback(self, result)
    })
      .fail((data) => {
        console.log('FAIL:', data);
      })
      .always((data) => {
      });
  }

  function createResource(self, el, resource_id, count, geometry_type) {

    var url = '/api/action/resource_show?id=' + resource_id;

    ckanAPI(self, function (self, result) {
      var name = result['name'];
      var format = result['format'];
      var package_id = result['package_id'];

      var li = createResourceItem(resource_id, name, format, count);

      li.on('click', self._onItemClick);
      $('.resource-format', li).css('cursor', 'pointer');
      //$('.record-count', li).css('cursor', 'pointer');

      li.data('resource-id', resource_id);
      li.data('package-id', package_id);
      li.data('format', format);
      li.data('geometry-type', geometry_type);

      el.append(li);

    }, url);
  }

  function createResourceItem(resource_id, name, format, count) {
    var li = $('<li class="nav-item"></li>');
    li.attr('resource-id', resource_id);
    var anchor = $('<a></a>');
    var resource_name = $('<div class="item-label resource-name"></div>');
    resource_name.append(name);

    var resource_format = $('<span class="label label-default resource-format"></span>');

    resource_format.attr('data-format', format.toLowerCase());
    resource_format.append(format);

    var record_count = $('<span class="item-count badge record-count"></span>');
    record_count.append(count);

    anchor.append(resource_name);
    anchor.append(resource_format);
    anchor.append(record_count);
    li.append(anchor);

    return li;
  }

  return {

    initialize: function () {

      if (window.performance.navigation.type === TYPE_RELOAD) {
        $.removeCookie('current');
      }

      this.map = mapInit();
      var self = this;
      this.map.on('moveend', function (e) {

        var current = {
          'center': self.map.getCenter(),
          'zoom': self.map.getZoom()
        };

        $.cookie("current", JSON.stringify(current));

      });

      if (this.options.q !== true && this.options.q !== "") {
        this.searchRecord(this.options.q);
      }

      $.proxyAll(this, /_on/);
      this.$('button.btn-search').on('click', this._onClick);
      this.$('#sidebar-search').on('keypress', this._onEnter);
    },

    teardown: function () {
      console.log('teardown');
    },

    _onClick: function (event) {
      event.preventDefault();
      var q = this.$('#sidebar-search').val();
      //q = "百道";
      this.searchRecord(q);
    },

    _onEnter: function (event) {
      if (event.key === 'Enter') {
        event.preventDefault();
        var q = this.$('#sidebar-search').val();
        this.searchRecord(q);
      }
    },

    _onItemClick: function (event) {
      event.preventDefault();
      event.stopPropagation();

      var target = $(event.target);
      var currentTarget = $(event.currentTarget);
      var resource_id = currentTarget.data('resource-id');
      var package_id = currentTarget.data('package-id');
      var format = currentTarget.data('format');
      var geometry_type = currentTarget.data('geometry-type');


      var item_key = resource_id + '_' + geometry_type;
      if (target.hasClass('resource-format')) {
        window.location.href = "/dataset/" + package_id + "/resource/" + resource_id;
      }
      else {
        var resourceItem = this._selectedResourceItems[item_key] || null;

        if (resourceItem) {

          if (currentTarget.hasClass('active')) {
            currentTarget.removeClass('active');
            resourceItem['item_active'] = false;
          }
          else {
            currentTarget.addClass('active');
            resourceItem['item_active'] = true;
          }

        }
        else {
          resourceItem = {
            'resource_id': resource_id,
            'package_id': package_id,
            'format': format,
            'geometry_type': geometry_type,
            'item_active': false,
          };
          this._selectedResourceItems[item_key] = resourceItem;
          currentTarget.addClass('active');
          resourceItem['item_active'] = true;
        }

        this._render(resourceItem);
      }


    },

    _removeLayer: function () {
      this.map.eachLayer(function (layer) {
        if (layer.options.attribution) {
          //console.log('attribution: ', layer);
        }
        else {
          layer.remove();
        }
      });
    },

    _pointShow: function (self, result) {
      var el = self.$('#resource-points');
      el.empty();

      var facet_counts = result['facet_counts'] || [];
      var resource_ids = facet_counts['facet_fields']['resource_id'];
      // var response = result['response'];
      // var responseHeader = result['responseHeader'];

      for (var i = 0; i < resource_ids.length; i += 2) {
        var resource_id = resource_ids[i];
        var count = resource_ids[i + 1];
        createResource(self, el, resource_id, count, 'point');
      }
    },

    _polygonShow: function (self, result) {

      var el = self.$('#resource-polygons');
      el.empty();

      var facet_counts = result['facet_counts'] || [];
      var resource_ids = facet_counts['facet_fields']['resource_id'];
      // var response = result['response'];
      // var responseHeader = result['responseHeader'];

      for (var i = 0; i < resource_ids.length; i += 2) {
        var resource_id = resource_ids[i];
        var count = resource_ids[i + 1];

        createResource(self, el, resource_id, count, 'polygon');
      }

    },

    searchRecord: function (q) {
      this._selectedResourceItems = {};
      this._q = q;

      this._removeLayer();

      history.replaceState(null, null, '/map?q=' + q);

      var url = '/api/action/record_search?geometry_type=point&facet.field=resource_id&facet.mincount=1&q=' + q + '&limit=0';
      ckanAPI(this, this._pointShow, url);
      var url_polygon = '/api/action/record_search?geometry_type=polygon&facet.field=resource_id&facet.mincount=1&q=' + q + '&limit=0';
      ckanAPI(this, this._polygonShow, url_polygon);
    },

    _render: function (resourceItem) {

      var resource_id = resourceItem['resource_id'];
      var geometry_type = resourceItem['geometry_type'];
      var layer = resourceItem['layer'];

      if (resourceItem['item_active']) {
        var markers = [];

        if (layer) {
          var features = resourceItem['features'];
          for (var feature of features) {
            layer.addData(feature);
          }
          this.map.fitBounds(layer.getBounds());
        }
        else {

          var url = '/api/action/record_search?q=' + this._q + '&geometry_type=' + geometry_type + '&geometry&resource_id=' + resource_id + '&limit=1000';

          var pointToLayer = function (geoJsonPoint, coordinates) {
//            var iconMarker = L.AwesomeMarkers.icon({
//              prefix: 'fa',
//              icon: 'circle',
//              //markerColor: 'blue'
//            });
            //var marker = L.marker(coordinates, {icon: iconMarker});
            return L.marker(coordinates);
          };

          var onEachFeature = function (feature, layer) {
            var properties = feature.properties;
            var fvs = properties['fvs'];
            layer.bindPopup(fvs.join('<br />'));
          };

          layer = L.geoJSON(false, {pointToLayer, onEachFeature}).addTo(this.map);
          resourceItem['layer'] = layer;

          ckanAPI(this, function (self, result) {
              var response = result['response'] || [];
              var docs = response['docs'] || [];

              var features = [];
              for (var doc of docs) {
                var geometry = wellknown.parse(doc['geometry']);
                var fvs = doc['fvs'] || [];
                var feature = {
                  "type": "Feature",
                  "properties": {fvs},
                  "geometry": geometry
                };
                layer.addData(feature);
                features.push(feature);
              }

              resourceItem['features'] = features;
              self.map.fitBounds(layer.getBounds());
            }
            ,
            url
          );
        }
      }
      else {
        layer.clearLayers();
      }

    },
  };
});

//ckan.module('ckanext-record-map-nav-item', function ($) {
//
//  return {
//    initialize: function () {
//
//      console.log('initialize');
//
//      $.proxyAll(this, /_on/);
//      console.log(this.options);
//    },
//    teardown: function () {
//      console.log('teardown');
//    }
//  }
//});

// "use strict";
//ckan.module('example_theme_popover', function ($) {
//  return {
//    initialize: function () {
//      $.proxyAll(this, /_on/);
//      this.el.popover({
//        title: this.options.title, html: true,
//        content: this._('Loading...'), placement: 'left'
//      });
//      this.el.on('click', this._onClick);
//      this.sandbox.subscribe('dataset_popover_clicked',
//        this._onPopoverClicked);
//    },
//
//    teardown: function () {
//      this.sandbox.unsubscribe('dataset_popover_clicked',
//        this._onPopoverClicked);
//    },
//
//    _snippetReceived: false,
//
//    // Start of _onClick method.
//    _onClick: function (event) {
//
//      // Make all the links on the page turn green.
//      this.$('i').greenify();
//
//      if (!this._snippetReceived) {
//        this.sandbox.client.getTemplate('example_theme_popover.html',
//          this.options,
//          this._onReceiveSnippet);
//        this._snippetReceived = true;
//      }
//      this.sandbox.publish('dataset_popover_clicked', this.el);
//    },
//    // End of _onClick method.
//
//    _onPopoverClicked: function (button) {
//      if (button != this.el) {
//        this.el.popover('hide');
//      }
//    },
//
//    _onReceiveSnippet: function (html) {
//      this.el.popover('destroy');
//      this.el.popover({
//        title: this.options.title, html: true,
//        content: html, placement: 'left'
//      });
//      this.el.popover('show');
//    },
//  };
//});


//(function (ckan, $) {
//
//  $(function () {
//
//
//    $('#form-search-map').submit(function (event) {
//      event.preventDefault();
//
//      //$('#field-sitewide-search').val()
//
//      $.ajax({
//        url: '/api/record_search',
//        type: 'GET'
//      })
//        .done((data) => {
//          //$('.result').html(data);
//          console.log(data);
//        })
//        .fail((data) => {
//          //$('.result').html(data);
//          console.log(data);
//        })
//        .always((data) => {
//
//        });
//
//    });
//  });
//
//})(this.ckan, this.jQuery);
