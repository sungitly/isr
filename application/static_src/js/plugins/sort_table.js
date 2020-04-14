/**
 * Created by gujiandong on 2015/9/18.
 */
/*table中加入可排序功能
* options中参数有
*    init:   初始的排序
*    ids:    哪些项加入排序功能
*    callback: 回调函数
*/
jQuery.fn.sort_table = function(options){
    var default_options = {
        init: {},
        ids: {},
        callback: function(id, order, field){}
    };
    var order2class = {
        0 : 'table_sort_normal',
        1: 'table_sort_asc',
        2: 'table_sort_desc'
    };
    var order2order_num = {
        'normal': 0,
        'asc': 1,
        'desc': 2
    };

    options = jQuery.extend(default_options, options);
    init = options.init;
    ids = options.ids;
    callback = options.callback;

    var ths = $('th', this);
    ths.each(function (i) {
        if (i in ids) {
            (function(self){
                var th = $(self);
                var field = ids[i];
                var order = 0;
                if (field in init) {
                    order = init[field];
                }
                th.attr('sort_by_order', order);
                th.addClass(order2class[order]);

                th.addClass('table-sortable');
                th.append('<span class="sort-indicator"></span>');

                th.attr('sort_by_field', field);
                th.click(function () {
                    var cur_order = th.attr('sort_by_order'),
                        new_order = (+cur_order + 1) % 3;
                    th.attr('sort_by_order', new_order);
                    th.removeClass(order2class[cur_order]);
                    th.addClass(order2class[new_order]);
                    callback(i, new_order, th.attr('sort_by_field'));
                });
            }(this));
        }
    });
    return this;
};
