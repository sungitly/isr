require('jquery');
require('bootstrap');
// require("bootstrap.datepicker");
require("jquery.cookie");
require("jquery.metisMenu");
require("jquery.slimscroll");
require("inspinia");
require("pace");
require("jquery.ui");

require("jsGrid");

$(document).ready(function() {
    $('.btn-refresh').on('click', function () {
        window.location.reload();
    });

    var select_store_id = $('#select_store_id');
    select_store_id.on('change', function(item){
        var store_id = select_store_id[0].value;
        $.post('/session_setting/store_id', {store_id: store_id}, function(){
            window.location.reload();
        });
    });
});