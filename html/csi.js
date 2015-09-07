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

app.controller('DataItems', function($scope, Items) {
    $scope.items = Items;

    $scope.$on('itemchanged', function() {
	console.log('hello world');
    });
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

app.controller('ParentalSets', function($scope, Items) {
    $scope.Items = Items;

    var psets = [];
    angular.forEach(csires.results, function(res) {
	angular.forEach(res.parents, function(parent,j) {
	    item = Items[res.item];
	    psets.push({item:item, parents:parent,
			weight:res.weights[j], loglik:res.loglik[j]})
	})
    });
    $scope.parentalsets = psets;
    $scope.weightthresh = 0.1;
})


app.controller('NetworkGraph', function($scope, Items) {
    $scope.$on('itemchanged', function(event) {
	console.log('got item changed')
	console.log(event)
    });

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

    var borderPath = svg.append("rect")
        .attr("x", 0)
        .attr("y", 0)
        .attr("height", height)
        .attr("width", width)
        .style("stroke", 'black')
        .style("fill", "none")
        .style("stroke-width", 1);

    var items = [];
    angular.forEach(Items, function(item) {
	items.push({ item: item })
    })

    var force = d3.layout.force()
        .charge(-120)
        .linkDistance(30)
        .nodes(items)
        .links([])
        .size([width, height])
        .start();

    var vis = svg.append("svg:g");

    var link = vis.append("g")
        .attr("class", "link")
        .selectAll();

    var node = vis.append("g")
        .attr("class", "node")
        .selectAll()
	.data(items, function(i) {return i.item.ord; });

    node.enter()
	.append("circle")
	.attr("r", 4);

    force.on("tick", function () {
        link.attr("x1", function(l) { return l.source.x; })
            .attr("y1", function(l) { return l.source.y; })
            .attr("x2", function(l) { return l.target.x; })
            .attr("y2", function(l) { return l.target.y; });

        node.attr('cx', function(n) { return n.x; })
            .attr('cy', function(n) { return n.y; });
    });
})
