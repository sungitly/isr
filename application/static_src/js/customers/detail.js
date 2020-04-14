/**
 * Created by daniel on 8/16/15.
 */

require('jquery.zeroclipboard');
require('bootstrap');

$(document).ready(function () {
    $('#reassign-btn').on('click', function () {
        var currentSalesId = parseInt($('#currentSalesId').val());
        var customerName = $('#customerName').val();
        var newSalesId = parseInt($('#saleses_list').val());

        if (newSalesId && newSalesId != currentSalesId) {
            $('#message #message-title').html('提示');
            var newSalesName = $('#saleses_list option:selected').text();
            $('#message #message-body').html('是否确认将客户' + customerName + '重新分配给销售顾问' + newSalesName);
            $('#message .btn-confirm').show();
            $('#message').modal();
            $('#message .btn-confirm').on('click', function () {
                $('#reassign-form').submit();
            });
        } else if (newSalesId) {
            $('#message #message-title').html('提示');
            $('#message #message-body').html('选择的销售顾问与当前所属销售顾问相同，无需重新分配。');
            $('#message .btn-confirm').hide();
            $('#message').modal();
        } else {
            $('#message #message-title').html('提示');
            $('#message #message-body').html('请选择新销售顾问');
            $('#message .btn-confirm').hide();
            $('#message').modal();
        }
    });

    //$.ZeroClipboard.config({swfPath: "static/images/ZeroClipboard.swf"});
    $.event.special.copy.options.swfPath = '/static/images/ZeroClipboard.swf';
    $("body")
        .on("copy", ".copy", function (e) {
            e.clipboardData.clearData();
            e.clipboardData.setData("text/plain", $(this).data('zclip-text'));
            e.preventDefault();
        });
});