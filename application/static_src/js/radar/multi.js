require('./helper.js');
$(function () {
    var $tabContainer = $('#tab-container'),
        $alertMsg = $('.alert');
    $tabContainer.hide();

    var CHART_WIDTH = $alertMsg.width();

    $('#filter-date-form > .btn-submit').on('click', function (e) {
        e.preventDefault();

        var carTrendUrl = helper.dataurl('storeStatics/carTrend'),
            stayTimeUrl = helper.dataurl('storeStatics/stayTimeStatics'),
            totalTrendUrl = helper.dataurl('storeStatics/totalTrend');

        $.when(
            $.post(carTrendUrl), $.post(stayTimeUrl), $.post(totalTrendUrl)
        ).then(function (carTrendDataRaw, stayTimeRawData, totalDataRaw) {
            carTrendDataRaw = carTrendDataRaw[0].content.dataList;
            stayTimeRawData = stayTimeRawData[0].content.dataList;
            totalDataRaw = totalDataRaw[0].content;

            renderData41(carTrendDataRaw);
            renderData42(stayTimeRawData);
            renderData43(totalDataRaw);

            $alertMsg.hide();
            $tabContainer.show();

        }, function () {
            $tabContainer.hide();
            $alertMsg.html("数据异常，请重试。").addClass("alert-danger").show();
        })


    });

    function renderData41(carTrendDataRaw) {
        var categories = [];
        var totals = [];
        var series = [
            {
                name: '非首次客流车型关注度',
                data: [],
                visible: false
            },
            {
                name: '首次客流车型关注度',
                data: []
            }
        ];

        var totalNewCount = 0;
        var totalOldCount = 0;
        $.each(carTrendDataRaw, function (carType, data) {
            totalNewCount += data.newCount;
            totalOldCount += data.oldCount;
        });

        totals['newCount'] = totalNewCount;
        totals['oldCount'] = totalOldCount;


        $.each(carTrendDataRaw, function (carType, data) {
            categories.push(carType);
            series[0].data.push(data.oldCount);
            series[1].data.push(data.newCount);
        });

        helper.drawCarTrendBarChart("#data-4-1", CHART_WIDTH, categories, series, ["#b1eafa", "#19b1d8"], totals, {
            click: function (e) {

                var carTrendUrl = helper.dataurl('storeStatics/carTrendDetails', {
                    car_name: e.point.category
                });

                $.when($.post(carTrendUrl)).then(function (carTrendDetailsRaw) {
                    $('#data-4-1').hide();
                    $('#detail-trend-4-1').show();

                    carTrendDetailsRaw = JSON.parse(carTrendDetailsRaw).content.dataList;
                    var categories22 = [];
                    var series22 = [
                        {name: "首次进店客流", data: []},
                        {name: "非首次进店客流", data: []}
                    ];

                    var detailsDataTrend = []; // used to make series for data-2-4 chart
                    for (var dateKey in carTrendDetailsRaw) {
                        if (carTrendDetailsRaw.hasOwnProperty(dateKey)) {
                            carTrendDetailsRaw[dateKey].date = dateKey;
                            detailsDataTrend.push(carTrendDetailsRaw[dateKey]);
                        }
                    }

                    detailsDataTrend.sort(helper.compareDateStringViaObject);

                    $.each(detailsDataTrend, function (i, item) {
                        categories22.push(item.date);
                        series22[0].data.push(item.newCount);
                        series22[1].data.push(item.oldCount);
                    });
                    helper.drawStandardSplineChart('#data-4-1-1', e.point.category, $("#start").val() + ' ~ ' + $("#end").val(), CHART_WIDTH, categories22, series22);
                });
            }
        });
    }

    $('#btn-back').click(function (e) {
        $('#detail-trend-4-1').hide();
        $('#data-4-1').show();
        e.stopPropagation();
    });

    function renderData42(stayTimeRawData) {
        // refine details data structure
        var stayTimeData = []; // used to make series for data-2-4 chart
        for (var dateKey in stayTimeRawData) {
            if (stayTimeRawData.hasOwnProperty(dateKey)) {
                stayTimeRawData[dateKey].date = dateKey;
                stayTimeData.push(stayTimeRawData[dateKey]);
            }
        }

        stayTimeData.sort(helper.compareDateStringViaObject);

        var categories42 = [];
        var series42 = [
            {name: "高意向客流平均停留时间 (分钟)", data: []}
        ];
        var totalValue = 0;

        for (var i = 0, l = stayTimeData.length; i < l; i++) {
            var item = stayTimeData[i];

            categories42.push(item.date);
            series42[0].data.push(+item.intentAvgMin.toFixed(2));
            totalValue += item.intentAvgMin;
        }

        helper.drawStandardColumnChartWithAvg("#data-4-2", CHART_WIDTH, series42[0].data.length, null, categories42, [
            {
                type: 'column',
                name: series42[0].name,
                data: series42[0].data,
                color: Highcharts.getOptions().colors[0],
                dataLabels: {
                    enabled: true,
                    style: {
                        fontWeight: 'bold'
                    }
                }
            }
        ], +(totalValue / stayTimeData.length).toFixed(2));
    }

    function renderData43(totalTrendDataRaw) {
        if (totalTrendDataRaw && (totalTrendDataRaw.intentNewCount + totalTrendDataRaw.intentOldCount > 0)) {
            var newOldDataCount = [
                ['首次进店', totalTrendDataRaw.intentNewCount],
                ['非首次进店', totalTrendDataRaw.intentOldCount]
            ];
            helper.drawStandardPieChart('#data-4-3', CHART_WIDTH, newOldDataCount);
        } else {
            $('#data-4-3').html('<div class="alert alert-danger">没有数据。</div>');
        }
    }
});