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

