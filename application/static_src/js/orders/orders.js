/**
 * Created by daniel on 8/16/15.
 */


$(document).ready(function() {
    $('#search-form').on('change', 'select', function () {
        $('#search-form').submit();
    });

    $('.btn-cancel').on('click', function (event) {
        var element = event.target;
        var data = $(element).attr('data');

        if (data){
            var orderId = parseInt(data);
            if (orderId > 0) {
                $('.modal #data').val(orderId);
                $('.modal #action').val('cancel_order');
                $('.modal').modal();
            }
        }
    });

    $('.modal').on('click', '.btn-confirm', function() {
        var action = $('.modal #action').val();

        if (action) {
            if (action == 'cancel_order') {
                var data = $('.modal #data').val();
                if (data) {
                    var orderId = parseInt(data);
                    if (orderId > 0){
                        $('#cancel_form #order_id').val(orderId);
                        $('#cancel_form').submit();
                    }
                }
            }
        }
        $('.modal').modal('hide');
    });

});