$(document).ready(function () {
    var searchForm = $('#search-form');
    searchForm.on('change', 'select', function () {
        searchForm.submit();
    });
    var sort_ths = {
            0: 'sales_id',
            2: 'status',
            3: '_intent_level',
            5: 'last_reception_date'
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
    $('#table_customers').sort_table({init:init, ids: sort_ths, callback:function(id, order, field){
        sort_by_field.attr('value', field);
        sort_by_order.attr('value', order);
        searchForm.submit();
    }});
});