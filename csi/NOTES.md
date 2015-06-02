# Developer Notes for CSI #

I'll try to keep notes relevant to the translation of CSI to Python in
this document.

## Data from the DREAM challenge ##

Test data for CSI from the DREAM project is in `Input/Demo_DREAM.csv`.
It contains two header rows, the first defines the 5 "Treatments"
while the second row the 21 evenly spaced X values for the timeseries.
The first column contains the 10 gene names and the remaining 10 by
(21*5) cells contain the data values.
