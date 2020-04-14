require('./helper.js');
$(function () {
    var $tabContainer = $('#tab-container'),
        $alertMsg = $('.alert');

    $tabContainer.hide();

    var CHART_WIDTH = $alertMsg.width();

    $('#filter-date-form > .btn-submit').on('click', function (e) {
        e.preventDefault();

        var customerTrendUrl = helper.dataurl('storeStatics/customerTrend'),
            timeTrendUrl = helper.dataurl('storeStatics/timeSectionTrend'),
            timesTrendsUrl = helper.dataurl('storeStatics/manyTimesTrends'),
            stayTimeUrl = helper.dataurl('storeStatics/stayTimeStatics');

        $.when($.post(customerTrendUrl),
            $.post(timeTrendUrl),
            $.post(timesTrendsUrl),
            $.post(stayTimeUrl)
        ).then(function (customerTrendDataRaw, timeTrendDataRaw, timesTrendsDataRaw, stayTimeRawData) {
            customerTrendDataRaw = customerTrendDataRaw[0].content.dataList;
            timeTrendDataRaw = timeTrendDataRaw[0].content.sections;
            timesTrendsDataRaw = timesTrendsDataRaw[0].content.dataList;
            stayTimeRawData = stayTimeRawData[0].content.dataList;

            renderData31(customerTrendDataRaw);
            renderData32(timesTrendsDataRaw);
            renderData33(timeTrendDataRaw);
            renderData34(stayTimeRawData);

            $alertMsg.hide();
            $tabContainer.show();
        }, function () {
            $alertMsg.html("数据异常，请重试。").addClass('alert-danger').show();
            $("#tab-container").hide();
        })

    });

    function renderData31(customerTrendDataRaw) {
        if (customerTrendDataRaw.length !== 0) {
            var customerTrendList = [];
            var customerTrendData = []; // refined data used to construct series for data 3-3 chart.
            for (var date in customerTrendDataRaw) {
                if (customerTrendDataRaw.hasOwnProperty(date)) {
                    customerTrendList.push([date, customerTrendDataRaw[date].displayCount, customerTrendDataRaw[date].driveCount]);
                    customerTrendDataRaw[date].date = date;
                    customerTrendData.push(customerTrendDataRaw[date]);
                }
            }

            customerTrendData.sort(helper.compareDateStringViaObject);

            var categories = [];
            var series = [
                {name: "展厅客流", data: []},
                {name: "试乘试驾客流", data: []}
            ];

            // max value for y axis
            var maxCount = 0;
            var totalDisplayCount = 0;
            var totalDriveCount = 0;
            for (var i = 0, l = customerTrendData.length; i < l; i++) {
                categories.push(customerTrendData[i].date);

                var displayCount = customerTrendData[i].displayCount;
                totalDisplayCount += displayCount;
                var driveCount = customerTrendData[i].driveCount;
                totalDriveCount += driveCount;

                series[0].data.push(displayCount);
                series[1].data.push(driveCount);

                maxCount = Math.max(maxCount, displayCount, driveCount);
            }

            // offset 30% of y axis for the pie chart
            maxCount = maxCount > 0 ? maxCount * 1.3 : null;
            helper.drawStandardSplinePieCombChart("#data-3-1", CHART_WIDTH, series[0].data.length, maxCount, categories, [
                {
                    type: 'spline',
                    name: series[0].name,
                    data: series[0].data,
                    color: Highcharts.getOptions().colors[0]

                },
                {
                    type: 'spline',
                    name: series[1].name,
                    data: series[1].data,
                    color: Highcharts.getOptions().colors[1]
                },
                {
                    type: 'pie',
                    name: '客流结构',
                    data: [
                        {
                            name: series[0].name,
                            y: totalDisplayCount,
                            color: Highcharts.getOptions().colors[0]
                        },
                        {
                            name: series[1].name,
                            y: totalDriveCount,
                            color: Highcharts.getOptions().colors[1]
                        }
                    ],
                    center: [100, 50],
                    size: 100,
                    showInLegend: false,
                    tooltip: {
                        pointFormat: '<b>{point.y} ({point.percentage:.1f}%)</b>'
                    },
                    dataLabels: {
                        enabled: true,
                        format: '{point.y} ({point.percentage:.1f}%)',
                        style: {
                            "fontWeight": "bold"
                        }
                    }
                }
            ], true, '');

            customerTrendList.sort(helper.compareDateString);
            $('#tb-3-1').html(helper.make_table(customerTrendList));
        } else {
            $('#data-3-1').html('<div class="alert alert-danger">没有数据。</div>');
        }
    }

    function renderData32(timesTrendsDataRaw) {
        if (timesTrendsDataRaw.length !== 0) {
            var timesTrendsData = []; // refined data used to construct series for data 3-4 chart.
            var timesTrendsList = [];
            for (var date in timesTrendsDataRaw) {
                if (timesTrendsDataRaw.hasOwnProperty(date)) {
                    timesTrendsList.push([date, timesTrendsDataRaw[date].multipleCount, timesTrendsDataRaw[date].singleCount])
                    timesTrendsDataRaw[date].date = date;
                    timesTrendsData.push(timesTrendsDataRaw[date]);
                }
            }

            timesTrendsData.sort(helper.compareDateStringViaObject);

            var categories = [];
            var series = [
                {name: "多店非首次进店", data: []},
                {name: "单店非首次进店", data: []}
            ];

            // max value for y axis
            var maxCount = 0;
            var totalMultiCount = 0;
            var totalSingleCount = 0;
            for (var i = 0, l = timesTrendsData.length; i < l; i++) {
                categories.push(timesTrendsData[i].date);

                var mulCount = timesTrendsData[i].multipleCount;
                totalMultiCount += mulCount;
                var singleCount = timesTrendsData[i].singleCount;
                totalSingleCount += singleCount;

                series[0].data.push(mulCount);
                series[1].data.push(singleCount);

                maxCount = Math.max(maxCount, mulCount, singleCount);
            }

            // offset 30% of y axis for the pie chart
            maxCount = maxCount > 0 ? maxCount * 1.3 : null;
            helper.drawStandardSplinePieCombChart("#data-3-2", CHART_WIDTH, series[0].data.length, maxCount, categories, [
                {
                    type: 'spline',
                    name: series[0].name,
                    data: series[0].data,
                    color: Highcharts.getOptions().colors[0]

                },
                {
                    type: 'spline',
                    name: series[1].name,
                    data: series[1].data,
                    color: Highcharts.getOptions().colors[1]
                },
                {
                    type: 'pie',
                    name: '单店非首次与多店非首次',
                    data: [
                        {
                            name: series[0].name,
                            y: totalMultiCount,
                            color: Highcharts.getOptions().colors[0]
                        },
                        {
                            name: series[1].name,
                            y: totalSingleCount,
                            color: Highcharts.getOptions().colors[1]
                        }
                    ],
                    center: [100, 50],
                    size: 100,
                    showInLegend: false,
                    dataLabels: {
                        enabled: true,
                        format: '{point.y} ({point.percentage:.1f}%)',
                        style: {
                            "fontWeight": "bold"
                        }
                    },
                    tooltip: {
                        pointFormat: '<b>{point.y} ({point.percentage:.1f}%)</b>'
                    }
                }
            ], true, '');

            timesTrendsList.sort(helper.compareDateString);
            $('#tb-3-2').html(helper.make_table(timesTrendsList));
        } else {
            $('#data-3-2').html('<div class="alert alert-danger">没有数据。</div>');
        }
    }

    function renderData33(timeTrendDataRaw) {
        var categories = [];
        var series = [
            {name: "总客流", data: []}
        ];
        var timeTrendList = [];
        for (var index in timeTrendDataRaw) {
            if (timeTrendDataRaw.hasOwnProperty(index)) {
                if (index >= 8 && index <= 20) {
                    timeTrendList.push([(index + ':00'), timeTrendDataRaw[index]]);
                    categories.push(index + ':00');
                    series[0].data.push(timeTrendDataRaw[index]);
                }
            }
        }

        helper.drawStandardSplineChart('#data-3-3', $("#store option:selected").text(), $("#start").val() + ' ~ ' + $("#end").val(), CHART_WIDTH, categories, series);
        timeTrendList.sort(helper.compareTimeString);
        $('#tb-3-3').html(helper.make_table(timeTrendList));
    }

    function renderData34(stayTimeRawData) {
        // refine details data structure
        var stayTimeData = []; // used to make series for data-2-4 chart
        for (var dateKey in stayTimeRawData) {
            if (stayTimeRawData.hasOwnProperty(dateKey)) {
                stayTimeRawData[dateKey].date = dateKey;
                stayTimeData.push(stayTimeRawData[dateKey]);
            }
        }

        stayTimeData.sort(helper.compareDateStringViaObject);

        var categories34 = [];
        var series34 = [
            {name: "客户单店平均停留时间", data: []}
        ];

        var totalValue = 0;
        for (var i = 0, l = stayTimeData.length; i < l; i++) {
            var item = stayTimeData[i];
            categories34.push(item.date);
            series34[0].data.push(+item.totalAvgMin.toFixed(2));
            totalValue += item.totalAvgMin;

        }

        helper.drawStandardColumnChartWithAvg("#data-3-4", CHART_WIDTH, series34[0].data.length, null, categories34, [
            {
                type: 'column',
                name: series34[0].name,
                data: series34[0].data,
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
});
