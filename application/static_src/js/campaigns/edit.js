/**
 * Created by daniel on 8/9/15.
 */

$('#campaign-time .input-daterange').datepicker({
    keyboardNavigation: false,
    forceParse: false,
    autoclose: true
});

$('#notify-time .input-group.date').datepicker({
    todayBtn: "linked",
    keyboardNavigation: false,
    forceParse: false,
    calendarWeeks: true,
    autoclose: true
});
$('button.btn-cancel').on('click', function () {
    window.history.back();
});
