chartsHelper = {};

chartsHelper.drawStandardSplineChart = function (id, width, categoriesData, seriesData, title, seriesName) {
    $(id).highcharts({
        chart: {
            width: width,
            height: 350
        },
        title: {
            text: title
        },
        xAxis: {
            categories: categoriesData
        },
        yAxis: {
            min: 0,
            title: {
                text: seriesName + ' (%)'
            }
        },
        tooltip: {
            valueSuffix: '%'
        },
        series: [{
            name: seriesName,
            data: seriesData
        }]
    });
};

chartsHelper.drawStandardColumnChart = function (id, width, categoriesData, seriesData, title, seriesName) {
    $(id).highcharts({
        chart: {
            type: 'column',
            width: width,
            height: 400
        },
        title: {
            text: title
        },
        xAxis: {
            categories: categoriesData
        },
        yAxis: {
            min: 0,
            title: {
                text: title
            },
            labels: {
                format: '{value}%'
            }
        },
        tooltip: {
            valueSuffix: '%'
        },
        plotOptions: {
            column: {
                pointPadding: 0.2,
                borderWidth: 0
            }
        },
        series: [{
            name: seriesName,
            data: seriesData
        }]
    });
};

chartsHelper.calcPer = function (target, total) {
    if (total == 0) {
        return 0
    } else {
        return Math.round(target * 1000 / total) / 10
    }
};


