# CSI Results Visualisation #

A results visualisation tool has been developed in order to help you
explore some common features output from the CSI model.  Roughly, the
tool allows you to visualise the resulting marginal and MAP networks,
applying thresholds as appropriate.  One can also view the model
predictions wile comparing them to the input data.

The main display is broken into three main sections; the top right of
the page displays the network, the top left shows a table of genes and
various attributes associated with them, at the bottom of the page a
series of plots show a selected gene and its parents.  The menu-bar at
the top of the page allows some other operations to be performed.

## Network Graph ##

The top right of the page displays a directed graph showing all the
selected genes with arrows pointing from "parental" genes to their
targets.  The plot can be dragged after clicking with the mouse and
zoomed by "scrolling".  Hovering over a node displays its name, while
clicking on it allows it to be rearranged within the graph.

The actual nodes and edges displayed within the graph is a
representation of the graph with the current options applied, with a
number of controls in other sections controlling what's displayed.

## Table of Genes ##

The table in the top right of the page displays a list of genes and
various attributes associated with them.  The checkbox shows which
genes are selected to be displayed within the network graph and can be
toggled individually or across all genes by clicking on different
checkboxes.  The other columns show results from the model that are
helpful in extracting information from its fit.

All columns can be sorted by clicking on the their title, clicking on
the same column a second time will reset the sort.  Sorting by any
column and then inspecting the top and bottom genes can be
informative, either of biologically relevant information or of the
model misinterpreting the input data and further preprocessing.

### Number of Parents and Children ###

The columns titled `Prnt` and `Chld` 

# Manual Result Extraction #

In order to open CsiVis the HDF5 results from CSI need to be
transformed into a JSON file.  This is process is happens
automatically within the iPlant App, but can be triggered manually by
running a command like:

    python csi-postprocess.py output.h5 -v > output.json

This command executes the Python script `csi-postprocess.py`, telling
it to take the complete results from the HDF5 formatted file
`output.h5`, extract the *better* models and predictions and write
them out to `output.json`.  The `-v` option causes output to be
*verbose*, that is it display some progress messages.

A few options exist to control this extraction process, and these can
be seen by running:

    python csi-postprocess.py --help

A more complete set of results can be viewed by running:

    python csi-postprocess.py -v output.h5 \
        --weight 1e-6 --predict 1e-3 > output.json

will cause models with even lower probabilities to be written to the
JSON file, as well as more predictions.  The trade off is larger JSON
file size which can cause issues when loading CsiVis in a web browser.
