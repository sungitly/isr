/**
 * Created by daniel on 8/1/15.
 */

$(document).ready(function (){
    var searchForm = $('#search-form');
    $('.campaign-types').on('change', 'input:radio', function () {
        searchForm.submit();
    });
    var sort_ths = {
        2: 'start',
        3: 'end',
        4: 'notify_date'
    };
    var sort_by_field = $('#sort_by_field');
    var sort_by_order = $('#sort_by_order');
    var field = sort_by_field.attr('value');
    var order = sort_by_order.attr('value');
    var init = {};
    if (field && order){
        order = (+order | 0) % 3;
        init[field]= order;
    }
    $('#table_campaigns').sort_table({init:init, ids: sort_ths, callback:function(id, order, field){
        sort_by_field.attr('value', field);
        sort_by_order.attr('value', order);
        searchForm.submit();
    }});
});