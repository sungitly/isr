require('jquery');
require('bootstrap');
require("jquery.cookie");
require("jquery.metisMenu");
require("jquery.slimscroll");
require("inspinia");
require("pace");
require("jquery.ui");
require('jsGrid');

$(document).ready(function () {
  $("#jsGrid").jsGrid({
    height: "auto",
    width: "100%",

    filtering: true,
    editing: true,
    autoload: true,
    sorting: true,
    paging: true,
    selecting: true,
    pageSize: 20,

    pagerFormat: "页码: {first} {prev} {pages} {next} {last}    {pageIndex} of {pageCount}",
    pagePrevText: "上一页",
    pageNextText: "下一页",
    pageFirstText: "首页",
    pageLastText: "末页",

    noDataContent: "没有库存信息",
    rowClick: function (arg) {
      showDetailsDialog(arg.item);
    },

    controller: {
      loadData: function (filter) {
        var d = $.Deferred();

        $.ajax({
          url: "/api/inventories",
          dataType: "json",
          data: filter
        }).done(function (response) {
          d.resolve(response);
        });

        return d.promise();
      },
      updateItem: function (item) {
        var filteredItem = {};

        $.each(item, function (key, value) {
          var attr_visible = false;
          try {
            attr_visible = $("#jsGrid").jsGrid('fieldOption', key, 'visible');
          }
          catch (e) {
            attr_visible = false;
          }
          if (attr_visible) {
            filteredItem[key] = value;
          }
        });
        return $.ajax({
          type: "POST",
          url: "/api/inventories/" + item.id,
          dataType: "json",
          contentType: "application/json",
          data: JSON.stringify(item)
        });
      }
    },

    fields: [
      {name: "vin", type: "text", title: "车架号", width: "auto", align: "center", editing: false, css: "break-word"},
      {name: "car_type", type: "text", title: "车型", width: "auto", align: "center", editing: false, css: "break-word"},
      {
        name: "car_subtype",
        type: "text",
        title: "细分车型",
        width: "auto",
        align: "center",
        editing: false,
        css: "break-word"
      },
      {
        name: "color_name",
        type: "text",
        title: "车身色",
        width: "auto",
        align: "center",
        editing: false,
        css: "break-word"
      },
      {
        name: "color_attribute",
        type: "text",
        title: "内饰色",
        width: "auto",
        align: "center",
        editing: false,
        css: "break-word"
      },
      {
        name: "inv_status",
        type: "select",
        title: "状态",
        width: "auto",
        align: "center",
        items: inv_status_items,
        valueField: "id",
        textField: "name",
        css: "break-word"
      },
      {
        name: "out_factory_date",
        type: "text",
        title: "出厂日期",
        width: "auto",
        align: "center",
        editing: false,
        css: "break-word"
      },
      {
        name: "stockin_date",
        type: "text",
        title: "入库日期",
        width: "auto",
        align: "center",
        editing: false,
        css: "break-word"
      },
      {
        name: "mrsp", type: "text", title: "建议售价(万)", width: "auto", align: "center", itemTemplate: function (value) {
        return value / 10000;
      }, editing: false, css: "break-word"
      },
      {
        name: "rebate_amt",
        type: "text",
        title: "折扣",
        width: "auto",
        align: "center",
        editing: true,
        css: "break-word",
        itemTemplate: function (value) {
          var amt = parseFloat(value).toFixed(2);
          if (amt && !isNaN(amt)) {
            return amt;
          } else {
            return null;
          }
        }
      }, {
        name: "remark",
        type: "textarea",
        title: "备注",
        width: "auto",
        align: "left",
        editing: true,
        css: "break-word",
        itemTemplate: function (value) {
          var maxLength = 25;
          if (value && value.length >= maxLength) {
            return value.substring(0, maxLength) + '...';
          } else {
            return value;
          }
        }
      },
      {
        type: "control",
        deleteButton: false,
        editing: false,
        editButtonTooltip: "编辑",
        searchButtonTooltip: "搜索",
        clearFilterButtonTooltip: "清空", css: "break-word"
      }
    ]
  });

  var showDetailsDialog = function (inventory) {
    $.ajax({
      url: "/api/inventories/" + inventory.id + "/repr",
      dataType: "json",
    }).success(function (datas, textStatus, jqXHR) {
      $('#update-form').empty();
      $.each(datas, function (index, value) {
        var fieldName = value.name;
        var fieldValue = value.value;
        fieldValue = fieldValue == null ? '' : fieldValue;

        var telStr = $('#detail-template').html();
        telStr = telStr.replace(/placeholderName/, fieldName);
        telStr = telStr.replace(/placeholderValue/, fieldValue);

        $('#update-form').append(telStr);

        $('#edit-modal-form').modal();
      });
    });
  };

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
});