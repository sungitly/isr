helper = {};

helper.dataurl = function (api, data) {
    return '/api/proxy_radar?surl=' + api + '&' + $.param(
        $.extend({
            start: $("#start").val(),
            end: $("#end").val(),
            store: $("#store_id").val()
        },
        data)
    );
};

helper.make_table = function (array) {
    var html = [];
    for (var i = 0, arr, l = array.length; i < l; i++) {

        html.push('<tr>');

        for (var j = 0, m = array[i].length; j < m; j++) {
            html.push('<td>', array[i][j], '</td>');
        }

        html.push('</tr>');

    }

    return html.join('');
};

helper.compareTimeString = function (a, b) {
    return a[0].split(':')[0] - b[0].split(':')[0];
};

helper.compareDateString = function (a, b) {
    return String(a[0]).localeCompare(b[0]);
};

helper.compareDateStringViaObject = function (a, b) {
    return String(a.date).localeCompare(b.date);
};

helper.drawStandardSplineChart = function (id, title, subtitle, chartWidth, categories, series) {
    $(id).highcharts({
        chart: {
            type: 'spline',
            width: chartWidth
        },
        title: {
            text: title,
            margin: 20,
            style: {
                fontWeight: 'bold'
            }
        },
        subtitle: {
            text: subtitle,
            style: {
                fontWeight: 'bold'
            }
        },
        xAxis: {
            tickInterval: parseInt(series[0].data.length / (chartWidth / 150), 10),
            categories: categories
        },
        yAxis: {
            title: {
                text: ''
            }
        },
        tooltip: {
            crosshairs: true,
            shared: true
        },
        plotOptions: {
            spline: {
                lineWidth: 2,
                marker: {
                    radius: 4,
                    lineWidth: 1,
                    states: {
                        hover: {
                            radius: 5
                        }
                    }
                },
                dataLabels: {
                    enabled: false,
                    formatter: function () {
                        return this.y > 0 ? this.y : ''
                    },
                    y: -10,
                    style: {
                        fontWeight: 'bold'
                    }
                }
            }
        },
        series: series
    });
};

helper.drawStandardPieChart = function (id, chartWidth, data) {
    $(id).highcharts({
        chart: {
            plotBackgroundColor: null,
            plotBorderWidth: null,
            plotShadow: false,
            width: chartWidth
        },
        title: {
            text: $("#store option:selected").text(),
            margin: 20,
            style: {
                fontWeight: 'bold'
            }
        },
        subtitle: {
            text: $("#start").val() + ' ~ ' + $("#end").val(),
            style: {
                fontWeight: 'bold'
            }
        },
        tooltip: {
            pointFormat: '<b>{point.y} ({point.percentage:.1f}%)</b>'
        },
        plotOptions: {
            pie: {
                allowPointSelect: true,
                cursor: 'pointer',
                dataLabels: {
                    enabled: true,
                    color: '#000000',
                    connectorColor: '#000000',
                    format: '<b>{point.name}</b>: {point.y} ({point.percentage:.1f}%)',
                    style: {
                        fontWeight: 'bold'
                    }
                },
                showInLegend: true
            }
        },
        series: [
            {
                type: 'pie',
                data: data
            }
        ]
    });
};

helper.drawStandardSplinePieCombChart = function (id, chartWidth, ticksCount, maxYAxis, categories, series, shareTooltip, unit) {
    $(id).highcharts({
        chart: {
            width: chartWidth,
            plotBackgroundColor: null,
            plotBorderWidth: null,
            plotShadow: false
        },
        title: {
            text: $("#store option:selected").text(),
            margin: 20,
            style: {
                fontWeight: 'bold'
            }
        },
        subtitle: {
            text: $("#start").val() + ' ~ ' + $("#end").val(),
            style: {
                fontWeight: 'bold'
            }
        },
        xAxis: {
            tickInterval: parseInt(ticksCount / (chartWidth / 150), 10),
            categories: categories,
            startOnTick: false,
            type: 'datetime'
        },
        yAxis: {
            title: {
                text: ''
            },
            labels: {
                format: '{value} ' + unit
            },
            max: maxYAxis
        },
        tooltip: {
            crosshairs: true,
            shared: shareTooltip
        },
        plotOptions: {
            spline: {
                lineWidth: 2,
                marker: {
                    radius: 4,
                    lineWidth: 1,
                    states: {
                        hover: {
                            radius: 5
                        }
                    }
                },
                dataLabels: {
                    enabled: false,
                    formatter: function () {
                        return this.y > 0 ? this.y : ''
                    },
                    y: -10,
                    zIndex: 2,
                    style: {
                        fontWeight: 'bold'
                    }
                }
            },
            pie: {
                allowPointSelect: true,
                cursor: 'pointer',
                dataLabels: {
                    enabled: false,
                    format: '<b>{point.name}</b>: {point.y} ({point.percentage:.1f}%)'
                }
            },
            column: {
                pointPadding: 0.15
            }
        },
        series: series
    });
};

helper.drawCarTrendBarChart = function (id, chartWidth, categories, series, colors, totals, events) {
    $(id).highcharts({
        chart: {
            type: 'bar',
            width: chartWidth,
            height: 450
        },
        colors: colors,
        title: {
            text: $("#store option:selected").text(),
            margin: 20,
            style: {
                fontWeight: 'bold'
            }
        },
        subtitle: {
            text: $("#start").val() + ' ~ ' + $("#end").val(),
            style: {
                fontWeight: 'bold'
            }
        },
        tooltip: {
            formatter: function () {
                var totalCount = 0;
                if (this.series.name == '非首次客流车型关注度') {
                    totalCount = totals['oldCount'];
                } else {
                    totalCount = totals['newCount'];
                }

                var titleLine = this.x + this.series.name + '<br>';
                var line1 = '<span style="color:' + this.series.color + '">\u25CF</span> ' + '客流' + ': <b>' + this.y +'</b><br>';
                var line2 = '<span style="color:' + this.series.color + '">\u25CF</span> ' + '占比' + ': <b>' + (this.y / totalCount * 100).toFixed(1) + '%' + '</b>';
                return titleLine + line1 + line2;
            },
            followPointer: true
        },
        xAxis: {
            categories: categories,
            title: {
                text: null
            }
        },
        yAxis: {
            min: 0,
            title: {
                text: ''
            },
            labels: {
                enabled: false
            }
        },
        plotOptions: {
            bar: {
                dataLabels: {
                    enabled: true,
                    formatter: function () {
                        var totalCount = 0;
                        if (this.series.name == '非首次客流车型关注度') {
                            totalCount = totals['oldCount'];
                        } else {
                            totalCount = totals['newCount'];
                        }
                        return  this.y + ' ('+ (this.y/totalCount *100).toFixed(1) + '%)';
                    },
                    style: {
                        "fontWeight": "bold"
                    },
                    overflow: 'none',
                    crop: false,
                    y: -2
                },
                events: events
            },
            series: {
                groupPadding: 0.2
            }
        },
        legend: {
            reversed: true
        },
        credits: {
            enabled: false
        },
        series: series
    });
};

helper.drawStoreCompareChart = function (id, chartWidth, title, categories, colors, data, avgValue, threshold) {
    $(id).highcharts({
        chart: {
            type: 'column',
            width: chartWidth
        },
        title: {
            text: '',
            margin: 20,
            style: {
                fontWeight: 'bold'
            }
        },
        subtitle: {
            text: title,
            style: {
                fontWeight: 'bold'
            }
        },
        xAxis: {
            categories: categories,
            labels: {
                enabled: true
            }
        },
        plotOptions: {
            column: {
                pointPadding: 0.25,
                borderWidth: 0,
                grouping: false,
                colors: colors,
                colorByPoint: true,
                showInLegend: false
            }
        },
        tooltip: {
            enabled: false
        },
        yAxis: {
            title: {
                text: null
            },
            labels: {
                enabled: false
            },
            maxPadding: 0.2,
            gridLineWidth: 0,
            plotLines: [
                {
                    color: '#6888E1',
                    value: avgValue,
                    width: '2',
                    dashStyle: 'ShortDot',
                    zIndex: 2,
                    label: {
                        text: '平均值: ' + (avgValue >= 1 ? avgValue : ((avgValue * 100).toFixed(1) + '%')),
                        style: {
                            fontWeight: 'bold',
                            fontSize: '14px'
                        },
                        x: -50
                    }
                }
            ],
            offset: 50
        }, series: [
            {
                name: '当月数据',
                type: 'column',
                data: data,
                dataLabels: {
                    enabled: true,
                    color: 'white',
                    inside: true,
                    formatter: function () {
                        return (this.y / avgValue * 100).toFixed(1) + '%';
                    },
                    style: {
                        fontWeight: 'bold',
                        fontSize: '14px'
                    }
                },
                showInLegend: true
            },
            {
                name: '当月数据',
                type: 'column',
                data: data,
                dataLabels: {
                    enabled: true,
                    style: {
                        fontWeight: 'bold',
                        fontSize: '14px'
                    },
                    formatter: function () {
                        if (this.y < 1) {
                            return (this.y * 100).toFixed(1) + '%'
                        } else {
                            return this.y;
                        }
                    }
                }
            }
        ]
    });
};

helper.drawStandardColumnChartWithAvg = function (id, chartWidth, ticksCount, maxYAxis, categories, series, avgValue) {
    $(id).highcharts({
        chart: {
            width: chartWidth,
            plotBackgroundColor: null,
            plotBorderWidth: null,
            plotShadow: false
        },
        title: {
            text: $("#store option:selected").text(),
            margin: 20,
            style: {
                fontWeight: 'bold'
            }
        },
        subtitle: {
            text: $("#start").val() + ' ~ ' + $("#end").val(),
            style: {
                fontWeight: 'bold'
            }
        },
        xAxis: {
            tickInterval: parseInt(ticksCount / (chartWidth / 150), 10),
            categories: categories,
            startOnTick: false,
            type: 'datetime'
        },
        yAxis: {
            title: {
                text: ''
            },
            labels: {
                enabled: false
            },
            max: maxYAxis,
            plotLines: [
                {
                    color: '#6888E1',
                    value: avgValue,
                    width: '2',
                    dashStyle: 'ShortDot',
                    zIndex: 1,
                    label: {
                        text: '平均值: ' + avgValue,
                        style: {
                            fontWeight: 'bold',
                            fontSize: '12px'
                        },
                        x: -40
                    }
                }
            ],
            gridLineWidth: 0,
            offset: 50
        },
        plotOptions: {
            column: {
                pointPadding: 0.15
            }
        },
        series: series
    });
};
