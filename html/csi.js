var app = angular.module("CsiResults",[]);

app.factory('Items', function () {
    var items =	{};
    angular.forEach(csires.items, function(item,i) {
	item.ord  = i;
	item.name = item.id;
	item.selected = true;

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
})

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
    $scope.weightthresh = 0.1;
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

    // build the arrow.
    svg.append("svg:defs").selectAll("marker")
      .data(["end"])      // Different link/path types can be defined here
    .enter().append("svg:marker")    // This section adds in the arrows
      .attr("id", String)
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 15)
      .attr("refY", -1)
      .attr("markerWidth", 6)
      .attr("markerHeight", 6)
      .attr("orient", "auto")
    .append("svg:path")
	.attr("d", "M0,-5L10,0L0,5")
	.style("fill","#f35");

    var borderPath = svg.append("rect")
        .attr("x", 0)
        .attr("y", 0)
        .attr("height", height)
        .attr("width", width)
        .style("stroke", 'black')
        .style("fill", "none")
        .style("stroke-width", 1);

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
    })

    angular.forEach(MarginalParents, function(mp) {
	var pn = mp.parent.node,
	    tn = mp.item.node;
	edges.push({
	    source: pn,
	    target: tn,
	    mpar: mp,
	    selected: function() {
		return pn.item.selected && tn.item.selected && mp.loglik > 0.1;
	    },
	})
    })

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
        .charge(-1000)
        .linkDistance(function(l) { return 100 / (0.1+l.mpar.loglik); })
	.linkStrength(function(l) { return 1 });

    var vis = svg.append("svg:g");

    var links = vis.append("g")
        .attr("class", "link")
	.selectAll()
        .data(edges).enter().append("path")
        .attr("marker-end", "url(#end)")
        .style("stroke", 'black')
	.style("fill", 'transparent')
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
                dr = Math.sqrt(500+dx * dx + dy * dy)*2;
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

    var	runWithIt = function () {
	nodes.style('visibility', function(n) {
	    return n.selected() ? 'visible' : 'hidden';
	});

	links.style('visibility', function(l) {
	    return l.selected() ? 'visible' : 'hidden';
	});

	force
            .nodes(selectedItems())
            .links(selectedEdges())
            .size([width, height])
            .start();
    };

    var unbind = $rootScope.$on('itemchanged', runWithIt);
    $scope.$on('$destroy', unbind);

    runWithIt();
})
