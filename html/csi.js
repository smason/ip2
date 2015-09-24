var app = angular.module("CsiResults",[]);

app.factory('Items', function () {
    var items =	{};
    var time = csires.replicates.map(function(d) {
	return d.time;
    });
    angular.forEach(csires.items, function(item,i) {
	item.ord  = i;
	item.name = item.id;
	item.selected = true;
	item.time = time;

	this[item.id] = item;
    }, items);
    return items;
});

app.factory('ParentalSets', function (Items) {
    var psets = [];
    angular.forEach(csires.results, function(res) {
	angular.forEach(res.parents, function(parent,j) {
	    item = Items[res.item];
	    psets.push({
		item    : item,
		parents : parent,
		weight  : res.weights[j],
		loglik  : res.loglik[j]})
	})
    });
    return psets;
});

app.factory('MarginalParents', function(Items, ParentalSets) {
    var	mpars = {};
    angular.forEach(ParentalSets, function(pset) {
	angular.forEach(pset.parents, function(pit) {
	    var key = [pit,pset.item.id];
	    if(key in mpars) {
		mpars[key].loglik += pset.weight;
	    } else {
		mpars[key] = {
		    item   : pset.item,
		    parent : Items[pit],
		    loglik : pset.weight};
	    }
	});
    });
    return mpars;
});

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

app.controller('ItemController', function($scope, Items) {
    $scope.items = Items;
});

app.filter('ParentalSetFilter', function() {
    return function(input, thresh) {
	var out = [];
	for (var i = 0; i < input.length; i++){
            if(input[i].item.selected && input[i].weight > thresh)
		out.push(input[i]);
	}
	return out;
    };
});

app.controller('ParentalSetController', function($scope, Items, ParentalSets) {
    $scope.Items        = Items;
    $scope.ParentalSets = ParentalSets;
    $scope.weightthresh = 0.01;
})

app.controller('NetworkController', function($scope, $rootScope, Items, MarginalParents) {
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

    // build the arrow (put on the end using CSS)
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

    angular.forEach(MarginalParents, function(mp) {
	var pn = mp.parent.node,
	    tn = mp.item.node;
	edges.push({
	    source: pn,
	    target: tn,
	    mpar: mp,
	    selected: function() {
		return pn.item.selected && tn.item.selected && mp.loglik > 0.01;
	    }
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
        .linkDistance(function(l) { return 100 / (0.1+l.mpar.loglik); })
	.linkStrength(function(l) { return l.mpar.loglik });

    var vis = svg.append("g");

    var links = vis.append("g")
        .attr("class", "link")
	.selectAll()
        .data(edges).enter().append("path")
        .style("stroke-width", function(l) { return 2 * l.mpar.loglik; });

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
	    if (l.mpar.loglik > 0.01 &&
		((l.source.item.mouseover && l.target.selected()) ||
		 (l.target.item.mouseover && l.source.selected())))
		str += ' mouseover';
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

    $rootScope.$on('mouseenter', function(evt,item) {
	item.mouseover = true;
	setStyles();
    });

    $rootScope.$on('mouseleave', function(evt,item) {
	item.mouseover = false;
	setStyles();
    });

    var unbind = $rootScope.$on('itemchanged', runWithIt);
    $scope.$on('$destroy', unbind);

    runWithIt();
})

app.controller('ExpressionController', function($scope, Items, MarginalParents) {
    var parent = d3.select("#expdata");

    var margin = {top: 0, right: 50, bottom: 20, left: 40},
	cwidth  = parent.node().clientWidth,  width  = cwidth - margin.left - margin.right,
	cheight = parent.node().clientHeight, height = cheight - margin.top - margin.bottom;

    var rangeScale = function (r, m) {
	var d = (r[1] - r[0]) * m;
	return [r[0] - d, r[1] + d]
    }

    var x = d3.scale.linear()
	.range(rangeScale([0, width],-0.02));

    var y = d3.scale.linear()
	.range(rangeScale([height, 0],-0.04));

    var color = d3.scale.category10();

    var xAxis = d3.svg.axis()
	.scale(x)
	.orient("bottom");

    var yAxis = d3.svg.axis()
	.scale(y)
	.orient("left");

    var svg = parent
        .attr("tabindex", 2)
        .append("svg")
          .attr("width", cwidth)
          .attr("height", cheight)
	.append("g")
	  .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    x.domain([
	d3.min(csires.replicates, function(r) { return d3.min(r.time); }),
	d3.max(csires.replicates, function(r) { return d3.max(r.time); })
    ]);
    y.domain([
	d3.min(csires.items, function(i) {return d3.min(i.data, function(x) { return d3.min(x); })}),
	d3.max(csires.items, function(i) {return d3.max(i.data, function(x) { return d3.max(x); })})
    ]);

    var	addDataSet = function(item) {
	data  = [];
	data2 = [];

	it = item.data;
	angular.forEach(csires.replicates, function(r, i) {
	    data2.push({rep:r.id, x:r.time, y:it[i]});
	    angular.forEach(r.time, function(t,j) {
		data.push({rep:r.id, x:t, y:it[i][j]})
	    });
	});

	var ds = svg.append("g")
	    .attr("class", "dataset")
	    .attr('clip-path', 'url(#plotAreaClip)')

	ds.selectAll(".dot")
	    .data(data)
	  .enter().append("circle")
	    .attr("class", "dot")
	    .attr("r", 3)
	    .attr("cx", function(d) { return x(d.x); })
	    .attr("cy", function(d) { return y(d.y); })
	    .attr("fill", function(d) { return color(d.rep); });

	var l = ds.selectAll(".line")
	    .data(data2)
	  .enter().append("path")
	    .attr("class", "line")
	    .attr("d", function(d) {
		var s = "M"+x(d.x[0])+","+y(d.y[0]);
		for (var i = 1; i < d.x.length; i++) {
		    s += "L"+x(d.x[i])+","+y(d.y[i]);
		}
		return s;
	    })
	    .style("stroke", function(d) { return color(d.rep); })
            .style("stroke-width", 2);

	var predidx = 0;
	preds = []
	angular.forEach(csires.results, function(res) {
	    if(res.item == item.name) {
		angular.forEach(res.weights, function(weight,pset) {
		    if (weight > 0.01) {
			predi = res.predictions[pset];
			angular.forEach(csires.replicates, function(rep,repn) {
			    for (var i = 1; i < rep.time.length; i++) {
				preds.push({rep:rep.id, weight:weight,
					    sn2: res.hyperparams[2],
					    predidx: predidx,
					    time:rep.time[i],
					    mu:predi.mu[repn][i-1],
					    var:predi.var[repn][i-1]})
			    }
			});
			predidx += 1;
		    }
		});
	    }
	});

	var predoff = -(predidx-1)/2

	var predSel = ds.selectAll().data(preds).enter();

	predSel.append("path")
	    .attr("class", "prediction")
	    .attr("d", function(d) {
		xt = x(d.time)+(d.predidx+predoff)*2
		return ("M"+xt+","+y(d.mu+2*Math.sqrt(d.var+d.sn2))+
			"L"+xt+","+y(d.mu-2*Math.sqrt(d.var+d.sn2)))
	    })
	    .style("stroke", function(d) { return color(d.rep); })
            .style("stroke-width", function(d) { return d.weight; });

	predSel.append("path")
	    .attr("class", "prediction")
	    .attr("d", function(d) {
		xt = x(d.time)+(d.predidx+predoff)*2
		return ("M"+(xt-3)+","+y(d.mu)+
			"L"+(xt+3)+","+y(d.mu)+
			"M"+xt+","+y(d.mu+2*Math.sqrt(d.var))+
			"L"+xt+","+y(d.mu-2*Math.sqrt(d.var)))
	    })
	    .style("stroke", function(d) { return color(d.rep); })
            .style("stroke-width", function(d) { return d.weight*2; });
    }

    svg.append("g")
	.attr("class", "x axis")
	.attr("transform", "translate(0," + height + ")")
      .call(xAxis)
	.append("text")
	.attr("class", "label")
	.attr("x", x.range()[1])
	.attr("y", -2)
	.style("text-anchor", "end")
	.text("Time");

    svg.append("g")
	.attr("class", "y axis")
	.call(yAxis)
      .append("text")
	.attr("class", "label")
	.attr("transform", "rotate(-90)")
	.attr("x", -y.range()[1])
	.attr("y", 4)
	.attr("dy", ".71em")
	.style("text-anchor", "end")
	.text("Expression");

    addDataSet(Items['Gene9'])

    svg.append('clipPath')
	.attr('id', 'plotAreaClip')
      .append('rect')
	.attr({ width: width, height: height });

    var legend = svg.selectAll(".legend")
	.data(color.domain())
      .enter().append("g")
	.attr("class", "legend")
	.attr("transform", function(d, i) { return "translate(0," + i * 20 + ")"; });

    legend.append("rect")
	.attr("x", width)
	.attr("width", 18)
	.attr("height", 18)
	.style("fill", color);

    legend.append("text")
	.attr("x", width+24)
	.attr("y", 9)
	.attr("dy", ".35em")
	.style("text-anchor", "start")
	.text(function(d) { return d; });
})

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

var plotGpEst = function(time, muvarlik, yscale) {
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
	    .style("stroke-width",width/2)
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

app.controller('PlotTargetParents', function($scope, Items, MarginalParents) {
    var item = Items['Gene9'];
    var mparents = [];
    angular.forEach(MarginalParents, function(mp) {
	if (item !== mp.item || mp.loglik < 0.1)
	    return;
	mparents.push(mp);
    });

    mparents.sort(function(a,b) { return a.loglik < b.loglik; })

    var preds = [], numpred = 0;
    angular.forEach(csires.results, function(res) {
	if(res.item == item.name) {
	    angular.forEach(res.weights, function(weight,pset) {
		if (weight > 0.01) {
		    predi = res.predictions[pset];
		    angular.forEach(csires.replicates, function(rep,repn) {
			x = []
			for (var i = 1; i < rep.time.length; i++) {
			    x.push({time:rep.time[i],
				    mu:predi.mu[repn][i-1],
				    var:predi.var[repn][i-1],
				    lik:res.hyperparams[2]})
			}
			x.weight = weight;
			x.rep    = repn;
			x.off    = numpred;
			preds.push(x);
		    });
		    numpred += 1;
		}
	    });
	}
    });

    var parent = d3.select("#parentplots");

    var outmargin = {top: 15, right: 5, bottom: 10, left: 35};
    var inmargin  = {top: 5, right: 5, bottom: 5, left: 10};

    var nrows = mparents.length+1,
	cwidth = parent.node().clientWidth,
	cheight = (70+inmargin.top+inmargin.bottom)*nrows+outmargin.top+outmargin.bottom;

    // cheight = parent.node().clientHeight;

    var svg = parent
        .attr("tabindex", 3)
      .append("svg")
        .attr("width", cwidth)
        .attr("height", cheight)

    var color = d3.scale.category10();

    var rangeScale = function (r, m) {
	var d = (r[1] - r[0]) * m;
	return [r[0] + d, r[1] - d]
    }

    var height  = (cheight-outmargin.top-outmargin.bottom-inmargin.bottom)/nrows,
	width   = (cwidth-outmargin.left-outmargin.right-inmargin.right)/5,
	iheight = height-inmargin.bottom-inmargin.top,
	iwidth  = width-inmargin.right-inmargin.left;

    var xs = d3.scale.linear()
	.range(rangeScale([0, iwidth], 0.02));

    var ys = d3.scale.linear()
	.range(rangeScale([iheight, 0], 0.02));

    xs.domain([0,1000])

    var xAxis = d3.svg.axis()
	.scale(xs)
	.ticks(5)
	.orient("bottom");

    var yAxis = d3.svg.axis()
	.scale(ys)
	.ticks(4)
	.orient("left");

    for (var y = 0; y < nrows; y++) {
	for (var x = 0; x < 5; x++) {
	    var top  = height*y+outmargin.top+inmargin.top,
		left = width*x+outmargin.left+inmargin.left;

	    var time   = item.time[x],
		target = item.data[x];

	    var plt = svg.append("g")
		.attr("transform", "translate(" + left + "," + top + ")");

	    var clipid="gpclip"+x+"."+y;
	    plt.append("clipPath")
		.attr("id",clipid)
		.append("rect")
		.attr("width",iwidth)
		.attr("height",iheight);

	    var	clip = plt.append("g")
		.attr("class","plotarea")
		.attr("clip-path", "url(#"+clipid+")")

	    clip.call(plotLine(time.map(xs),target.map(ys))
		      .color(color(x))
		      .width(1))

	    if (y == 0) {
		for (var i = 0; i < preds.length; i++) {
		    if (preds[i].rep !=	x)
			continue;
		    var off = preds[i].off-numpred/2;
		    var time = preds[i].map(function(d) {
			return xs(d.time)+off;
		    });
		    clip.call(plotGpEst(time, preds[i], ys)
			      .width(preds[i].weight))
		}
	    } else {
		var mp = mparents[y-1],
		    parent = mp.parent.data[x];
		clip.call(plotLine(time.map(xs),
				  parent.map(ys))
			  .width(2*mp.loglik))

		if (x == 0) {
		    plt.append("text")
			.attr("class","axis label")
			.attr("x",-iheight/2)
			.attr("y",-10)
			.attr("dy", "-1.71em")
			.style("text-anchor", "middle")
			.attr("transform", "rotate(-90)")
			.text(mp.parent.name+" : "+d3.format(".2f")(mp.loglik))
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
		    .text(csires.replicates[x].id)
		    .style("text-anchor","middle")
	    }

	    if (y == 4) {
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
    }
})
