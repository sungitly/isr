/**
 * Created by daniel on 7/31/15.
 */

$(document).ready(function () {

    $(".btn-cancel-order").on('click', function (event) {
        var element = event.target;
        var orderId = parseInt($(element).attr('data'));

        $('#cancelOrderModel').show()
        //if (orderId > 0) {
        //    var url = "/orders/" + orderId;
        //    $.ajax({
        //            type: 'POST',
        //            url: url,
        //            contentType: 'application/json',
        //            data: JSON.stringify({"status": "cancelled"}),
        //            success: function (response) {
        //                $(element).siblings().remove();
        //                $(element).remove();
        //            },
        //            dataType: 'json'
        //        }
        //    )
        //}
    });
});