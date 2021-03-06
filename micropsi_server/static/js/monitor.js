
$(function(){

    var viewProperties = {
        height: 420,
        padding: 20,
        xvalues: 100
    };

    var container = $('#graph');
    var svg = null;

    var nodenetMonitors = {};
    var currentMonitors = [];

    var currentSimulationStep = 0;
    var currentNodenet = null;

    var capturedLoggers = {
        'system': false,
        'world': false,
        'nodenet': false
    };

    if($.cookie('capturedLoggers')){
        capturedLoggers = JSON.parse($.cookie('capturedLoggers'));
    }
    if($.cookie('currentMonitors')){
        currentMonitors = JSON.parse($.cookie('currentMonitors'));
    }

    var last_logger_call = 0;

    var log_container = $('#logs');

    init();

    $(document).on('monitorsChanged', function(evt, new_monitor){
        currentMonitors.push(new_monitor)
        refreshMonitors();
    });
    $(document).on('nodenetChanged', function(data, newNodenet){
        refreshMonitors(newNodenet);
    });

    function init() {
        bindEvents();
        if (currentNodenet = $.cookie('selected_nodenet')) {
            api.call('load_nodenet', {
                nodenet_uid: currentNodenet,
                coordinates: {
                    x1: 0,
                    x2: 0,
                    y1: 0,
                    y2: 0
                }
            }, function(data) {
                refreshMonitors();
            },
            function(data) {
                if(data.status == 500){
                    api.defaultErrorCallback(data);
                } else {
                    currentNodenet = null;
                    $.cookie('selected_nodenet', '', { expires: -1, path: '/' });
                    dialogs.notification(data.data, "Info");
                }
            });
        }
    }

    function getPollParams(){
        var poll = [];
        for(var logger in capturedLoggers){
            if(capturedLoggers[logger]){
                poll.push(logger);
            }
        }
        return {
            logger: poll,
            after: last_logger_call
        }
    }

    function setData(data){
        setMonitorData(data);
        setLoggingData(data);
        currentSimulationStep = data.current_step;
    }

    register_stepping_function('monitors', getPollParams, setData);

    function refreshMonitors(newNodenet){
        params = getPollParams();
        if(newNodenet || currentNodenet){
            params.nodenet_uid = newNodenet || currentNodenet;
            api.call('get_monitoring_info', params, setData);
        }
    }

    function setMonitorData(data){
        updateMonitorList(data.monitors);
        nodenetMonitors = data.monitors;
        var m = {};
        for (var uid in nodenetMonitors) {
            if (currentMonitors.indexOf(uid) >= 0) {
                m[uid] = nodenetMonitors[uid];
            }
        }
        drawGraph(m);
    }

    function setLoggingData(data){
        var height = log_container.height();
        var scrollHeight = log_container[0].scrollHeight;
        var st = log_container.scrollTop();
        var doscroll = (st >= (scrollHeight - height));
        last_logger_call = data.logs.servertime;
        for(var idx in data.logs.logs){
            log_container.append($('<span class="logentry log_'+data.logs.logs[idx].level+'">'+data.logs.logs[idx].logger+' | ' + data.logs.logs[idx].msg +'</span>'));
        }
        if(doscroll){
            log_container.scrollTop(log_container[0].scrollHeight);
        }
    }

    function bindEvents(){
        $('.log_switch').on('change', function(event){
            var el = $(event.target);
            capturedLoggers[el.attr('data')] = el.attr('checked')
            $.cookie('capturedLoggers', JSON.stringify(capturedLoggers), {path:'/', expires:7})
        });
        $('.log_level_switch').on('change', function(event){
            var el = $(event.target);
            var data = {}
            data[el.attr('data')] = el.val();
            api.call('set_logging_levels', data);
        });
        $('.log_switch').each(function(idx, el){
            if(capturedLoggers[$(el).attr('data')]){
                el.checked=true;
            }
        });
    }

    function updateMonitorList(monitors){
        var list = $('#monitor_selector');
        var html = '';
        for(var uid in monitors){
            html += '<li><input type="checkbox" class="monitor_checkbox" value="'+uid+'" id="'+uid+'"';
            if(currentMonitors.indexOf(uid) > -1){
                html += ' checked="checked"';
            }
            html += ' /> <label for="'+uid+'" style="display:inline;color:#'+uid.substr(2,6)+'"><strong>' + monitors[uid].name + '</strong></label> <a href="#" class="delete_monitor" title="delete monitor" data="'+uid+'"><i class="icon-trash"></i></a></li>';
        }
        list.html(html);
        $('.monitor_checkbox', list).on('change', updateMonitorSelection);
        $('.delete_monitor', list).on('click', function(event){
            event.preventDefault();
            api.call(
                'remove_monitor',
                {nodenet_uid: currentNodenet, monitor_uid: $(event.delegateTarget).attr('data')},
                function(){
                    delete monitors[uid];
                    refreshMonitors();
                }
            );
        });
    }

    function updateMonitorSelection() {
        currentMonitors = [];
        $.each($('.monitor_checkbox'), function(idx, el) {
            if (el.checked) {
                currentMonitors.push(el.value);
            }
        });
        $.cookie('currentMonitors', JSON.stringify(currentMonitors), {path:'/', expires:7})
        drawGraph(currentMonitors);
    }

    function drawGraph(currentMonitors) {

        var customMonitors = false;
        container.html(''); // TODO: come up with a way to redraw
        var margin = {
                top: 20,
                right: 50,
                bottom: 30,
                left: 50
            },
            width = container.width() - margin.left - margin.right - viewProperties.padding,
            height = viewProperties.height - margin.top - margin.bottom - viewProperties.padding;

        var xmax = Math.max(viewProperties.xvalues, currentSimulationStep);
        var x = d3.scale.linear()
            .domain([xmax - viewProperties.xvalues, xmax])
            .range([0, width]);
        var xstart = xmax - viewProperties.xvalues;

        var y1values = [];
        var y2values = [];
        var y1max = 1.0;
        var y1min = 0;
        var y2max = 1.0;
        var y2min = 0;
        for (var uid in currentMonitors) {
            for (var step in currentMonitors[uid].values) {
                if(currentMonitors[uid].classname == 'CustomMonitor'){
                    customMonitors = true;
                    y2values.push(currentMonitors[uid].values[step]);
                    if (step >= xstart) {
                        y2max = Math.max(y2max, currentMonitors[uid].values[step]);
                        y2min = Math.min(y2min, currentMonitors[uid].values[step]);
                    }
                } else {
                    y1values.push(currentMonitors[uid].values[step]);
                    if (step >= xstart) {
                        y1max = Math.max(y1max, currentMonitors[uid].values[step]);
                        y1min = Math.min(y1min, currentMonitors[uid].values[step]);
                    }
                }
            }
        }

        var y1 = d3.scale.linear().domain([y1min, y1max]).range([height, 0]);
        var y2 = d3.scale.linear().domain([y2min, y2max]).range([height, 0]);

        var x_axis_pos = (y1max / (y1max - y1min)) * height;

        var xAxis = d3.svg.axis()
            .scale(x)
            .orient("bottom");

        var y1Axis = d3.svg.axis()
            .scale(y1)
            .orient("left");
        var y2Axis = d3.svg.axis()
            .scale(y2)
            .orient("right");

        svg = d3.select("#graph").append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        svg.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + x_axis_pos + ")")
            .call(xAxis)
            .append("text")
            .attr("dx", width - 100)
            .attr("dy", -5)
            .style("text-anchor", "start")
            .text("Nodenet step");
        svg.append("g")
            .attr("class", "y axis")
            .call(y1Axis)
            .append("text")
            .attr("transform", "rotate(-90)")
            .attr("y", 6)
            .attr("dy", ".71em")
            .style("text-anchor", "end")
            .text("Activation");
        if(customMonitors){
            svg.append("g")
                .attr("class", "y axis")
                .call(y2Axis)
                .attr("transform", "translate(" + width + " ,0)")
                .append("text")
                .attr("transform", "rotate(-90)")
                .attr("y", 6)
                .attr("dy", ".71em")
                .style("text-anchor", "end")
                .text("Value");
        }

        for (var uid in currentMonitors) {
            var data = [];
            if(currentMonitors[uid].classname == 'CustomMonitor'){
                var line = d3.svg.line()
                    .x(function(d) {
                        return x(d[0]);
                    })
                    .y(function(d) {
                        return y2(d[1]);
                    })
                    .defined(function(d){ return d[1] == 0 || Boolean(d[1])});
                for (var step in currentMonitors[uid].values) {
                    data.push([parseInt(step, 10), parseFloat(currentMonitors[uid].values[step])]);
                }
                var points = svg.selectAll(".point")
                    .data(data)
                    .enter().append("svg:circle")
                     .attr("stroke", "black")
                     .attr("fill", function(d, i) { return '#' + uid.substr(2, 6); })
                     .attr("cx", function(d, i) { return x(d[0]); })
                     .attr("cy", function(d, i) { return y2(d[1]); })
                     .attr("r", function(d, i) { return 2 });

            } else {
                var line = d3.svg.line()
                    .x(function(d) {
                        return x(d[0]);
                    })
                    .y(function(d) {
                        return y1(d[1]);
                    })
                    .defined(function(d){ return d[1] == 0 || Boolean(d[1])});
                for (var step in currentMonitors[uid].values) {
                    data.push([parseInt(step, 10), parseFloat(currentMonitors[uid].values[step])]);
                }
                var points = svg.selectAll(".point")
                    .data(data)
                    .enter().append("svg:circle")
                     .attr("fill", function(d, i) { return '#' + uid.substr(2, 6); })
                     .attr("cx", function(d, i) { return x(d[0]); })
                     .attr("cy", function(d, i) { return y1(d[1]); })
                     .attr("r", function(d, i) { return 2 });

            }


            var len = data.length;
            data.splice(0, len - viewProperties.xvalues - 1);
            var color = '#' + uid.substr(2, 6);
            svg.append("path")
                .datum(data)
                .attr("class", "line")
                .attr("stroke", color)
                .attr("d", line);
        }
    }

});
