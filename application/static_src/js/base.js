/**
 * Created by daniel on 8/9/15.
 */
require('jquery');
require('bootstrap');
// require("bootstrap.datepicker");
require("jquery.cookie");
require("jquery.metisMenu");
require("jquery.slimscroll");
require("inspinia");
require("pace");
require("jquery.ui");
require("jquery.chosen");
require("spinner");

$(document).ready(function () {
  $('.btn-refresh').on('click', function () {
    window.location.reload();
  });

  var select_store_id = $('#select_store_id');
  select_store_id.on('change', function (item) {
    var store_id = select_store_id[0].value;
    $.post('/session_setting/store_id', {store_id: store_id}, function () {
      window.location.reload();
    });
  });

  var options = {
    lines: 9,
    length: 2,
    width: 2,
    radius: 10,
    corners: 1,
    rorate: 0,
    trail: 10,
    speed: 2.2,
    direction: 1,
    zIndex: 2e9,
    top: '50%',
    left: '50%'
  };
  var $spiner = $('#spiner');
  var spiner = new Spinner(options).spin();

  $(document).ajaxStart(function () {
    $spiner.append(spiner.el);
  }).ajaxStop(function () {
    $spiner.empty();
  });

  $(".chosen-select").chosen({
    no_results_text: "没有匹配的选项",
    search_contains: true
  });
});