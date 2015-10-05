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

    var collectAllEdges = function() {
        edges = [];
        angular.forEach(Items, function(item) {
            angular.forEach(item.parents, function(mp) {
                // filter these out early, can't see them anyway
                if (mp.prob < 1e-2)
                    return;
                var it = {
                    source: mp.parent.node,
                    target: mp.target.node,
                    mpar: mp,
                    selected: function() {
                        return (mp.parent.selected &&
                                mp.target.selected &&
                                mp.prob > $scope.weightthresh);
                    }
                };
                edges.push(it);
                mp.edge = it;
            });
        });
    };

    collectAllEdges();

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

    nodes
        .append("svg:title")
        .text(function(d) { return d.item.name; });


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

    $scope.$on('weightchanged', function() {
        collectAllEdges();
        runWithIt();
    });

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
            .data([muvar])
	    .enter();

	l.append("path")
	    .attr("class", "line gpestimate")
	    .style("stroke-width",width)
            .attr("d",function(d) {
                var s = "";
                for (var i = 0; i < d.mu.length; i++) {
                    var sd = Math.sqrt(d.var[i])*2,
                        ti = time[i+1],
                        y0 = yscale(d.mu[i]);
                    s += ("M"+(ti-3)+","+y0+
                          "L"+(ti+2)+","+y0+
                          "M"+ti+","+yscale(d.mu[i]-sd)+
                          "L"+ti+","+yscale(d.mu[i]+sd))
                }
                return s;
	    });

	l.append("path")
	    .attr("class", "line gpestimate")
	    .style("stroke-width",0.5*width)
            .attr("d",function(d,i) {
                var s = "";
                for (var i = 0; i < d.mu.length; i++) {
                    var sd = Math.sqrt(d.var[i]+lik)*2;
                    s += ("M"+time[i+1]+","+yscale(d.mu[i]-sd)+
                          "L"+time[i+1]+","+yscale(d.mu[i]+sd));
                }
                return s;
	    });
    })};
    plot.width = function(x) {
	width = +x;
	return plot;
    };
    return plot;
};

var initialisePlots = function($scope, Reps, Items) {
    var outmargin = {top: 15, right: 5, bottom: 10, left: 40};
    var inmargin  = {top: 5, right: 5, bottom: 5, left: 5};

    var parent = d3.select("#parentplots"),
        cwidth = parent.node().clientWidth,
        nreps = Reps.length,
        width   = (cwidth-outmargin.left-outmargin.right-inmargin.right)/nreps,
        iwidth  = width-inmargin.right-inmargin.left;

    var color = d3.scale.category10();

    var rangeScale = function (r, m) {
        var d = (r[1] - r[0]) * m;
        return [r[0] + d, r[1] - d]
    }

    var xs = d3.scale.linear()
        .range(rangeScale([0, iwidth], 0.02))
        .domain([
            d3.min(Reps, function(rep) { return d3.min(rep.time); }),
            d3.max(Reps, function(rep) { return d3.max(rep.time); })])

    var ys = d3.scale.linear()
        .domain([
            d3.min(Reps, function(rep) { return d3.min(rep.data, function(it) { return d3.min(it); })}),
            d3.max(Reps, function(rep) { return d3.max(rep.data, function(it) { return d3.max(it); })})
        ])

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

    var plotItem = function(item) {
        var mparents = [];
        var preds = [];

        angular.forEach(item.parents, function(par) {
            if(par !== undefined && par.prob > $scope.weightthresh)
                mparents.push(par)
        });
        mparents.sort(function(a,b) { return b.prob - a.prob; })

        angular.forEach(item.result.models, function(mod) {
            if (mod.predict !== undefined && mod.weight > 0.02)
                preds.push(mod)
        });
        preds.sort(function(a,b) { return b.weight - a.weight; })

        var nrows = mparents.length+1,
            cheight = (70+inmargin.top+inmargin.bottom)*nrows+outmargin.top+outmargin.bottom,
            height  = (cheight-outmargin.top-outmargin.bottom-inmargin.bottom)/nrows,
            iheight = height-inmargin.bottom-inmargin.top;

        svg.attr("height", cheight)

        ys.range(rangeScale([iheight, 0], 0.02))

        svg.selectAll(".subplot").remove();

        var plots = [];
        for (var y = 0; y < nrows; y++) {
            for (var x = 0; x < nreps; x++) {
                plots.push({x:x,y:y})
            }
        }

        svg.selectAll(".subplot")
            .data(plots)
            .enter()
            .append("g")
              .attr("class", "subplot")
            .each(function(d,i) {
                var plt = d3.select(this),
                    x = d.x, y = d.y;

                var top  = height*y+outmargin.top+inmargin.top,
                    left = width*x+outmargin.left+inmargin.left;

                plt.attr("transform", "translate(" + left + "," + top + ")")

                var clipid="gpclip"+x+"."+y;
                plt.append("clipPath")
                    .attr("id",clipid)
                    .append("rect")
                    .attr("width",iwidth)
                    .attr("height",iheight);

                var plot = plt.append("g")
                    .attr("class","plotarea")
                    .attr("clip-path", "url(#"+clipid+")")

                var time   = Reps[x].time.map(function(d) { return xs(d) }),
                    target = Reps[x].data[item.ord];

                plot.call(plotLine(time,target.map(ys))
                          .color(color(x))
                          .width(1))

                if (y == 0) {
                    var numpred = preds.length;
                    for (var i = 0; i < preds.length; i++) {
                        var mod = preds[i],
                            pred = mod.predict,
                            off = i-numpred/2,
                            time2 = time.map(function(d) { return d+off });
                        plot.call(plotGpEst(time2, pred[x], item.result.hyperparams[2], ys)
                                  .width(mod.weight))
                    }
                } else {
                    var mp = mparents[y-1];
                    var parent = Reps[x].data[mp.parent.ord];

                    plot.call(plotLine(time,
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

                plt.append("g")
                    .attr("class", "x y axis")
                    .append("path")
                    .attr("d",
                          "M0,0L"+
                          [[0,iheight],[iwidth,iheight]].join("L"))
            });
    }

    var curItem;
    $scope.$on('mouseenter', function(evt,item) {
        plotItem(item);
        curItem = item;
    });

    $scope.$on('weightchanged', function() {
        console.log("fred")
        if (curItem !== undefined) {
            console.log("in fred")
            plotItem(curItem)
        }
    })
}

app.controller('CSI', function ($scope) {
    var items =	[];
    angular.forEach(csires.items, function(name,i) {
        this.push({
            ord: i,
            name: name,
            selected: true,
            parents: []
        });
    }, items);

    $scope.marginalnetwork = function(item) {
        var mpars = [];
        angular.forEach(item.result.models, function(mod) {
            angular.forEach(mod.pset, function(parent) {
                if (parent in mpars) {
                    mpars[parent].prob += mod.weight;
                } else {
                    var it = {
                        target : item,
                        parent : items[parent],
                        prob   : mod.weight
                    };

                    mpars[parent] = it;
                }
            });
        });
        return mpars;
    };

    $scope.mapnetwork = function(item) {
        var mpars = [];
        if (item.result.models.length > 0) {
            mod = item.result.models[0]
            angular.forEach(mod.pset, function(parent) {
                if (parent in mpars) {
                    mpars[parent].prob += mod.weight;
                } else {
                    var it = {
                        target : item,
                        parent : items[parent],
                        prob   : mod.weight
                    };

                    mpars[parent] = it;
                }
            });
        }
        return mpars;
    };

    allmarginals = [];
    angular.forEach(csires.results, function(res) {
        var item = items[res.target];
        item.result = res;
        item.parents = $scope.marginalnetwork(item);
        angular.forEach(item.parents, function (it) {
            if (it !== undefined) {
                allmarginals.push(it)
            }
        })
    });

    $scope.weightthresh = 0.1;
    $scope.items = items;
    $scope.allmarginals = allmarginals;

    makeNetwork($scope, items);
    initialisePlots($scope, csires.reps, items);
});
