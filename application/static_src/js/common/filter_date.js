require("moment");

var DATE_FORMAT = "YYYY-MM-DD";
var cookie_name_date_start = "date-start";
var cookie_name_date_end = "date-end";
var date_start = $.cookie(cookie_name_date_start);
var date_end = $.cookie(cookie_name_date_end);

var YESTERDAY = moment().add(-1, "d").format(DATE_FORMAT);
var TODAY = moment().format(DATE_FORMAT);
var NOW = new Date();

$('#date_filter #start').val(date_start || TODAY);
$('#date_filter #end').val(date_end || TODAY);
$('#date_filter .input-daterange').datepicker({
    keyboardNavigation: false,
    forceParse: false,
    autoclose: true,
    format: "yyyy-mm-dd",
    endDate: NOW
}).on('changeDate', function () {
    $.cookie(cookie_name_date_start, $('#date_filter #start').val());
    $.cookie(cookie_name_date_end, $('#date_filter #end').val());
});



