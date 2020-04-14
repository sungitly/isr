require('./helper.js');
$(function () {
    var $tabContainer = $('#tab-container'),
        $alertMsg = $('.alert');

    $tabContainer.hide();

    var CHART_WIDTH = $alertMsg.width();

    $('#filter-date-form > .btn-submit').on('click', function (e) {
        e.preventDefault();

        var totalTrendUrl = helper.dataurl('storeStatics/totalTrend'),
            detailsTrendUrl = helper.dataurl('storeStatics/detailsTrend');


        $.when($.post(totalTrendUrl), $.post(detailsTrendUrl)).then(function (totalDataRaw, detailsDataRaw) {
            totalDataRaw = totalDataRaw[0].content;
            detailsDataRaw = detailsDataRaw[0].content.dataList;

            // render the content of field #data-2-funnel
            renderData2Funnel(totalDataRaw);
            renderData22(detailsDataRaw);

            renderData23(totalDataRaw);
            renderData24(totalDataRaw);

            $alertMsg.hide();
            $tabContainer.show()
        }, function () {
            $alertMsg.html('数据异常，请重试。').addClass('alert alert-danger').show();
            $tabContainer.hide();
        })

    });

    function makeFunnel(data) {

        $("#funnel-totalCount").html(data.totalCount === 0 ? "N/A" : data.totalCount);
        $("#funnel-effectiveCount").html(data.effectiveCount === 0 ? "N/A" : data.effectiveCount);
        $("#funnel-newCount").html(data.newCount === 0 ? "N/A" : data.newCount);
        $("#funnel-oldCount").html(data.oldCount === 0 ? "N/A" : data.oldCount);
        $("#funnel-intentCount").html(data.intentCount === 0 ? "N/A" : data.intentCount);
        var driveCount = data.oldDriveCount + data.newDriveCount;
        $("#funnel-driveCount").html(driveCount === 0 ? "N/A" : driveCount);

    }

    function renderData2Funnel(data) {
        var count = 0;
        for (var key in data) {
            if (data.hasOwnProperty(key)) {
                count += parseFloat(data[key]);
            }
        }
        if (count !== 0) {
            makeFunnel(data);
            $('#funnel-chart-title').html($("#store option:selected").text());
            $('#funnel-chart-subtitle').html($("#start").val() + ' ~ ' + $("#end").val());
        } else {
            $('#data-2-funnel').html('没有数据。').addClass('alert alert-danger');
        }
    }

    function renderData22(detailsDataRaw) {
        // refine details data structure
        var detailsDataList = []; // used to generate data table
        var detailsDataTrend = []; // used to make series for data-2-2 chart
        for (var dateKey in detailsDataRaw) {
            if (detailsDataRaw.hasOwnProperty(dateKey)) {
                detailsDataList.push([
                    dateKey,
                    detailsDataRaw[dateKey].effectiveCount,
                    detailsDataRaw[dateKey].newCount,
                    detailsDataRaw[dateKey].oldCount,
                    detailsDataRaw[dateKey].intentCount === 0 ? "N/A" : detailsDataRaw[dateKey].intentCount
                ]);
                detailsDataRaw[dateKey].date = dateKey;
                detailsDataTrend.push(detailsDataRaw[dateKey]);
            }
        }

        detailsDataList.sort(helper.compareDateString);
        $('#tb-2-2').html(helper.make_table(detailsDataList));

        detailsDataTrend.sort(helper.compareDateStringViaObject);

        var categories22 = [];
        var series22 = [
            {name: "总客流", data: []},
            {name: "首次进店客流", data: []},
            {name: "非首次进店客流", data: []},
            {name: "高意向客流", data: []}
        ];

        for (var i = 0, l = detailsDataTrend.length; i < l; i++) {
            var item = detailsDataTrend[i];

            categories22.push(item.date);
            series22[0].data.push(item.effectiveCount);
            series22[1].data.push(item.newCount);
            series22[2].data.push(item.oldCount);
            series22[3].data.push(item.intentCount);

        }

        helper.drawStandardSplineChart('#data-2-2', $("#store option:selected").text(), $("#start").val() + ' ~ ' + $("#end").val(), CHART_WIDTH, categories22, series22);
    }

    function renderData23(totalTrendDataRaw) {
        if (totalTrendDataRaw && (totalTrendDataRaw.newCount + totalTrendDataRaw.oldCount > 0)) {
            var newOldDataCount = [
                ['首次进店', totalTrendDataRaw.newCount],
                ['非首次进店', totalTrendDataRaw.oldCount]
            ];
            helper.drawStandardPieChart('#data-2-3', CHART_WIDTH, newOldDataCount);
        } else {
            $('#data-2-3').html('<div class="alert alert-danger">没有数据。</div>');
        }
    }


    function renderData24(data) {
        helper.drawStandardPieChart('#data-2-4', CHART_WIDTH, [
            {
                name: '高意向客流',
                y: data.intentCount,
                sliced: false,
                dataLabels: {
                    enabled: true,
                    format: '<b>{point.name}</b>: {point.y} ({point.percentage:.1f}%)',
                }
            },
            {
                name: '非高意向客流',
                y: data.effectiveCount - data.intentCount,
                dataLabels: {
                    enabled: false
                }
            }
        ]);
    }
});