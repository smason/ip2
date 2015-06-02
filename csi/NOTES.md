# Developer Notes for CSI #

I'll try to keep notes relevant to the translation of CSI to Python in
this document.

## Data from the DREAM challenge ##

Test data for CSI from the DREAM project is in `Input/Demo_DREAM.csv`.
It contains two header rows, the first defines the 5 "Treatments"
while the second row the 21 evenly spaced X values for the timeseries.
The first column contains the 10 gene names and the remaining 10 by
(21*5) cells contain the data values.

# Files #

## Control Flow ##

`csi` is the entry point of the program, starts the GUI and responds
to button presses.  `panelfuncs` contains a list of panels to display,
all subdirectories are added to Matlab's search path.  The data is
loaded, parsed, genes and transcription factors selected and finally a
structure is passed to `run_CSI`.  This structure contains:

 * `data` a double matrix, as per demo data file
 * `genenames` a cell array
 * `genedesc` a cell array
 * `orig_startingCols` not sure
 * `startingCols` matrix describing which columns of the data refer to
   which treatment
 * `replicatenames` a cell array
 * `filename` string
 * `time_values` double vector, as per demo data
 * `toplot` single numeric value
 * `tf` double vector, indicies of genes to treat as transcription factors
 * `gene_idx` as per `tf`
 * `params`: has members
   *  `type` either `CSI` or `Hierarchical CSI`
   * `Pr` priors for hyper parameters
   * `inference` 1 for EM or 2 for MCMC (only for CSI).
   * `sparse` optimisation (only for EM)
   * `N` number of MC steps (only for MCMC or Hierarchical)
   * `temp` temp for Hierarchical
   * `fixtemp` boolean for Hierarchical?
   * `indegree` where to truncate the in-degree
   * `dirname` output directory
   * `parEnv` not sure, empty matrix!
