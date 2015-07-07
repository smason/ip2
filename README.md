# iPlant Integration Project from Warwick's System Biology #

This repository contains the tools that will be ported into the iPlant
project.  As a starting point, the tools consist of:

* GP2S: A robust Bayesian two-sample test for detecting intervals of
  differential gene expression in microarray time series.
  doi:10.1089/cmb.2009.0175

* CSI: Causal structure identification algorithm for inferring gene
  regulatory networks.  How to infer gene networks from expression
  profiles, revisited. doi:10.1098/rsfs.2011.0053

* HCSI: Hierarchical variant of the CSI.  Nonparametric Bayesian
  inference for perturbed and orthologous gene regulatory
  networks. doi:10.1093/bioinformatics/bts222

* Wigwams: identifying gene modules co-regulated across multiple
  biological conditions. doi:10.1093/bioinformatics/btt728

* Apples: Analysis of Plant Promoter-Linked Elements.  http://www2.warwick.ac.uk/fac/sci/systemsbiology/staff/ott/tools_and_software/apples/

* Gradient Tool: not sure where this is from.  Looks for significant
changes in gradient of timeseries.

* VBSSM: A Bayesian approach to reconstructing genetic regulatory
  networks with hidden factors.  doi:10.1093/bioinformatics/bti014

* MVBSSM: not sure how this variant alters the above.

* MemeLab: motif analysis in clusters.
  doi:10.1093/bioinformatics/btt248

* Wellington: a novel method for the accurate identification of
  digital genomic footprints from DNase-seq data.
  doi:10.1093/nar/gkt850

Some of these projects are already written in languages compatible
with the iPlant infrastructure, but others are based in Matlab and
will be ported to Python and C++ for compatibility and performance.

# TODO #

## Gradient Tool ##

I need to get the output organised, currently it's callable from
Python, but there's no useful standalone script as useful for iPlant.

The existing Matlab code outputs the following:

* One PDF for each gene/row of the dataset

Each PDF contains: a plot of the data and a plot of the predicted
latent function, a plot of the gradient of the previous, and the
switch state.  No labels are present, but I presume in the third plot
red is the state given a cutoff of 1 sigma, blue is for 2sigma and
green is for 3sigma.

* `Gradients.txt`

CSV formatted data, with no row or column headers.  Looks like the
inferred mean of the gradient—nothing on the variance!

* `Switch_[123].txt`

CSV formatted as `Gradients.txt` but contains the switch states of
given the sigma from the filename.

# General Notes #

The file system used within iPlant is called *iRODS*.  It comes with
its own set of *iCommands* for performing `ftp` like operations at the
command line.  Alternatively there are GUI apps like iDrop and a
`fuse` plugin available.  There are also nice Python libraries
available for talking to iRODS servers, for example
[python-irodsclient](https://github.com/iPlantCollaborativeOpenSource/python-irodsclient).

To connect to the iPlant servers, you need the following details:

    host: data.iplantcollaborative.org
    port: 1247
    zone: iplant
    username: <iplant username>
    password: <iplant password>

## Python Dependencies ##

These are the minimal Python libraries that would need to be installed:

    pip install numpy scipy pandas matplotlib GPy

In order to run an interactive exploration in iPython, these are also
needed:

    pip install ipython pyzmq jinja2 tornado jsonschema
