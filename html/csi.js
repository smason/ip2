var app = angular.module("CsiResults",[]);

app.filter('weight', function() {
    return function(w) {
	return w.toPrecision(3);
    }
});

app.filter('parents', function() {
    return function(ps) {
	return ps.join(", ");
    }
});

app.filter('ParentalSetFilter', function() {
    return function(input, thresh) {
	var out = [];
	for (var i = 0; i < input.length; i++){
            if(input[i].target.selected && input[i].prob > thresh)
		out.push(input[i]);
	}
	return out;
    };
});

var makeNetwork = function ($scope, Items) {
    var parent = d3.select("#graph");

    var width  = parent.node().clientWidth,
	height = parent.node().clientHeight;

    var xScale = d3.scale.linear()
        .domain([0,width]).range([0,width]);
    var yScale = d3.scale.linear()
        .domain([0,height]).range([0, height]);

    var svg = parent
        .attr("tabindex", 1)
        .append("svg")
          .attr("width", width)
          .attr("height", height);

    // build the arrow
    svg.append("svg:defs")
	.append("marker")    // This section adds in the arrows
	.attr("id", "arrow")
	.attr("viewBox", "0 -5 10 10")
	.attr("refX", 15)
	.attr("refY", 0)
	.attr("markerWidth", 6)
	.attr("markerHeight", 6)
	.attr("orient", "auto")
      .append("path")
	.attr("d", "M0,-5L10,0L0,5");

    var items = [], edges = [];
    angular.forEach(Items, function(item) {
        var it = {
	    item: item,
	    selected: function() {
		return item.selected;
	    }
	};
	items.push(it)
	item.node = it;
    });

    angular.forEach(Items, function(item) {
        angular.forEach(item.marginalparents, function(mp) {
            var it = {
                source: mp.parent.node,
                target: mp.target.node,
                mpar: mp,
                selected: function() {
                    return (mp.parent.selected &&
                            mp.target.selected &&
                            mp.prob > 0.01);
                }
            };
            edges.push(it);
            mp.edge = it;
        });
    });

    var selectedItems = function() {
	var out = [];
	angular.forEach(items, function(it) {
	    if (it.selected())
		out.push(it);
	})
	return out;
    };

    var selectedEdges = function() {
	var out = [];
	angular.forEach(edges, function(it) {
	    if (it.selected())
		out.push(it);
	})
	return out;
    };

    var force = d3.layout.force()
        .charge(-500)
        .linkDistance(function(l) { return 100 / (0.1+l.mpar.prob); })
	.linkStrength(function(l) { return l.mpar.prob });

    var vis = svg.append("g");

    var links = vis.append("g")
        .attr("class", "link")
	.selectAll()
        .data(edges).enter().append("path")
        .style("marker-end", "url(#arrow)")
        .style("stroke-width", function(l) { return 2 * l.mpar.prob; });

    var nodes = vis.append("g")
	.attr("class", "node")
	.selectAll()
	.data(items)
	.enter().append("circle")
	  .attr("r", 4);

    force.on("tick", function () {
        links.attr("d", function(d) {
            var dx = d.target.x - d.source.x,
		dy = d.target.y - d.source.y,
                dr = Math.sqrt(400+dx * dx + dy * dy)*2;
            return "M" +
                d.source.x + "," +
                d.source.y + "A" +
                dr + "," + dr + " 0 0,1 " +
                d.target.x + "," +
                d.target.y;
        });

        nodes
	    .attr('cx', function(n) { return n.x; })
            .attr('cy', function(n) { return n.y; });
    });

    var setStyles = function() {
	// show/hide the nodes and edges as appropriate
	nodes.attr('class', function(n) {
	    var str = '';
	    if (n.item.mouseover)
		str += ' mouseover';
	    if (n.selected())
		str += ' selected';
	    return str;
	});
	nodes.attr('r', function(a) {
	    return a.item.mouseover ? 6 : 4;
	});

	links.attr('class', function(l) {
	    var str = '';
	    if (l.selected())
		str += ' selected';
	    if (l.mpar.prob > 0.01) {
		if(l.source.item.mouseover && l.target.selected())
		    str += ' mouseovertarget';
		else if (l.target.item.mouseover && l.source.selected())
		    str += ' mouseoverparent';
	    }
	    return str;
	});
    };

    var runWithIt = function () {
	setStyles();

	force
            .nodes(selectedItems())
            .links(selectedEdges())
            .size([width, height])
            .start();
    };

    $scope.$on('mouseenter', function(evt,item) {
	item.mouseover = true;
	setStyles();
    });

    $scope.$on('mouseleave', function(evt,item) {
	item.mouseover = false;
	setStyles();
    });

    $scope.$on('itemchanged', runWithIt);

    runWithIt();
}

var plotLine = function(x,y) {
    var stroke, width = 1;
    function plot(g) { g.each(function() {
	d3.select(this).append("path")
	    .attr("class", "line")
	    .attr("d", "M"+d3.zip(x,y).join("L"))
	    .style("stroke-width", width)
	    .style("stroke", stroke)
    })};
    plot.color = function(x) {
	stroke = x;
	return plot;
    };
    plot.width = function(x) {
	width = +x;
	return plot;
    };
    return plot;
};

var plotGpEst = function(time, muvar, lik, yscale) {
    var stroke = "black", width = 1;
    function plot(g) { g.each(function() {
	var g = d3.select(this);
	var l = g.append("g").selectAll("path")
	    .data(muvarlik)
	    .enter();

	l.append("path")
	    .attr("class", "line gpestimate")
	    .style("stroke-width",width)
	    .attr("d",function(d,i) {
		var sd = Math.sqrt(d.var)*2,
		    ti = time[i],
		    y0 = yscale(d.mu);
		return ("M"+(ti-3)+","+y0+
			"L"+(ti+2)+","+y0+
			"M"+ti+","+yscale(d.mu-sd)+
			"L"+ti+","+yscale(d.mu+sd))
	    });

	l.append("path")
	    .attr("class", "line gpestimate")
	    .style("stroke-width",0.5*width)
	    .attr("d",function(d,i) {
		var sd = Math.sqrt(d.var+d.lik)*2;
		return ("M"+time[i]+","+yscale(d.mu-sd)+
			"L"+time[i]+","+yscale(d.mu+sd));
	    });
    })};
    plot.width = function(x) {
	width = +x;
	return plot;
    };
    return plot;
};

var makePlots = function($scope, Reps, Items) {
    var outmargin = {top: 15, right: 5, bottom: 10, left: 40};
    var inmargin  = {top: 5, right: 5, bottom: 5, left: 5};

    var parent = d3.select("#parentplots"),
        cwidth = parent.node().clientWidth,
        width   = (cwidth-outmargin.left-outmargin.right-inmargin.right)/5,
        iwidth  = width-inmargin.right-inmargin.left;

    var color = d3.scale.category10();

    var rangeScale = function (r, m) {
        var d = (r[1] - r[0]) * m;
        return [r[0] + d, r[1] - d]
    }

    var xs = d3.scale.linear()
        .range(rangeScale([0, iwidth], 0.02));

    xs.domain([0,1000])

    var ys = d3.scale.linear();

    var xAxis = d3.svg.axis()
        .scale(xs)
        .ticks(5)
        .orient("bottom");

    var yAxis = d3.svg.axis()
        .scale(ys)
        .ticks(4)
        .orient("left");

    var svg = parent
        .attr("tabindex", 3)
        .append("svg")
        .attr("width", cwidth);

    $scope.$on('mouseenter', function(evt,item) {
        console.log(item)

        var mparents = item.marginalparents;
        var preds = [];

        angular.forEach(item.result.models, function(mod) {
            if (mod.predict !== undefined)
                preds.push(mod.predict)
        })
        preds.sort(function(a,b) { return b.prob - a.prob; })
        var numpred = preds.length;

        var nrows = mparents.length+1,
            cheight = (70+inmargin.top+inmargin.bottom)*nrows+outmargin.top+outmargin.bottom,
            height  = (cheight-outmargin.top-outmargin.bottom-inmargin.bottom)/nrows,
            iheight = height-inmargin.bottom-inmargin.top;

        svg.attr("height", cheight)

        ys.range(rangeScale([iheight, 0], 0.02))

        function createPlot(plt, x, y) {
            var top  = height*y+outmargin.top+inmargin.top,
                left = width*x+outmargin.left+inmargin.left;

            var time   = Reps[x].time,
                target = Reps[x].data[item.ord];

            plt.attr("transform", "translate(" + left + "," + top + ")")

            var clipid="gpclip"+x+"."+y;
            plt.append("clipPath")
                .attr("id",clipid)
                .append("rect")
                .attr("width",iwidth)
                .attr("height",iheight);

            var clip = plt.append("g")
                .attr("class","plotarea")
                .attr("clip-path", "url(#"+clipid+")")

            clip.call(plotLine(time.map(xs),target.map(ys))
                      .color(color(x))
                      .width(1))

            if (y == 0) {
                for (var i = 0; i < preds.length; i++) {
                    var pred = preds[i],
                        off = i-numpred/2,
                        time = pred[x].mu.map(function(d) {
                            return xs(d.time)+off;
                        });
                    clip.call(plotGpEst(time, pred[x], ys)
                              .width(pred.weight))
                }
            } else {
                var mp = mparents[y-1],
                    parent = Reps[x].data[mp.parent.ord];
                clip.call(plotLine(time.map(xs),
                                   parent.map(ys))
                          .width(2*mp.prob))

                if (x == 0) {
                    plt.append("text")
                        .attr("class","axis label")
                        .attr("x",-iheight/2)
                        .attr("y",-10)
                        .attr("dy", "-1.71em")
                        .style("text-anchor", "middle")
                        .attr("transform", "rotate(-90)")
                        .text(mp.parent.name+" : "+d3.format(".2f")(mp.prob))
                }
            }

            plt.append("g")
                .attr("class", "x y axis")
                .append("path")
                .attr("d",
                      "M0,0L"+
                      [[0,iheight],[iwidth,iheight]].join("L"))

            if (y == 0) {
                plt.append("text")
                    .attr("x",iwidth/2)
                    .text(Reps[x].name)
                    .style("text-anchor","middle")
            }

            if (y == nrows-1) {
                plt.append("g")
                    .attr("class", "x axis")
                    .attr("transform", "translate(0," + iheight + ")")
                    .call(xAxis)
            }

            if (x == 0) {
                plt.append("g")
                    .attr("class", "y axis")
                    .call(yAxis)
            }
        }

        svg.selectAll(".subplot").remove();

        var plots = [];
        for (var y = 0; y < nrows; y++) {
            for (var x = 0; x < 5; x++) {
                plots.push({x:x,y:y})
            }
        }

        svg.selectAll(".subplot")
            .data(plots)
            .enter()
            .append("g")
              .attr("class", "subplot")
            .each(function(d,i) {
                createPlot(d3.select(this), d.x, d.y)
            });
    })
}

app.controller('CSI', function ($scope) {
    var items =	[];
    angular.forEach(csires.items, function(name,i) {
        this.push({
            ord: i,
            name: name,
            selected: true,
            marginalparents: []
        });
    }, items);

    var allmarginals = []
    angular.forEach(csires.results, function(res) {
        var item = items[res.target];

        var mpars = item.marginalparents;

        angular.forEach(res.models, function(mod) {
            angular.forEach(mod.pset, function(parent) {
                if (parent in mpars) {
                    mpars[parent].prob += mod.weight;
                } else {
                    var it = {
                        target : items[res.target],
                        parent : items[parent],
                        prob   : mod.weight
                    };

                    mpars[parent] = it;
                    allmarginals.push(it);
                }
            });
        });

        item.result = res;
    });

    $scope.weightthresh = 0.1;
    $scope.items = items;
    $scope.allmarginals = allmarginals;

    makeNetwork($scope, items);
    makePlots($scope, csires.reps, items);
});
