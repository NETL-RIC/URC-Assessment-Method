Introduction
============

Unconventional Rare-earth elements & Critical minerals (URC) {cite}`osti_1891489` are crucial to a growing number of 
industries worldwide {cite}`BALARAM20191285`. Critical Minerals (CM) are minerals used in manufacturing which are essential 
to economic and national security while being vulnerable to supply disruption through any number of external factors 
{cite}`osti_1891489`. _Unconventional_ CM resources contrast with conventional CM resources in that they are sourced from 
geologic or byproduct hosts distinctly separate from the mechanisms which establish conventional CM deposits; such 
unconventional sources include _in situ_ geologic deposits and byproducts of industrial extraction 
{cite}`osti_1891489`.
 
The extraction and recovery of conventional CM is a complex process traditionally involving strip mining, 
which is both expensive and environmentally destructive {cite}`BALARAM20191285`. Recent research has revealed that 
coaliferous sediments may act as unconventional CM sources containing REE in significant concentrations 
{cite}`SEREDIN201267`; determining the likelihood and location of these resources in sedimentary basins, however, is both
complex and challenging. To address this, a new method of evaluating the potential occurrence of URC resources using a 
series of validated heuristics has been developed {cite}`CREASON2022`. 

The URC Resource Assessment Tool is used for executing the URC method step 3, the calculation of the potential 
enrichment score, on extant datasets generated from steps 1 & 2 of the URC method. For description of how to use this 
tool, see the [Usage](usage/index.rst) section.


Statement of need
=================

The **URC Resource Assessment Method** applies the data analysis methods outlined in {cite:t}`CREASON2022`, the 
tool's 
companion paper. This tool is a complete application written in Python and built on top of several open-source 
libraries. No other Python packages are known to contain the combination of geospatial information systems (GIS) and 
fuzzy logic support required to directly implement the method defined in {cite:t}`CREASON2022`. The intended users for 
this tool are geologists and geospatial scientists who are looking to better understand the mode and spatial 
distribution of potential URC resource occurrences in sedimentary basins.

There are several ways that the **URC Resource Assessment Method** can be configured to run, but fundamentally the tool 
takes in a collection of spatial domains which fall under the Lithological, Structural, and Secondary Alteration 
categories defined by the Subsurface Trend Analysis (STA) method {cite}`sta2019`. These domains are combined, clipped 
to a researcher-defined boundary, and grided to cells of a research-specified dimension.

From this point, a Data Availability (DA) and / or a Data Supporting (DS) analysis can be undertaken by the tool; both 
analyses will operate on a vector-based spatial dataset describing the target formation, following the labelling scheme 
specified in the supplementary material in {cite:t}`CREASON2022`. These data are rasterized according to the grid 
specification of the aforementioned domains with each cell tagged with the appropriate set of indices. In the case of a 
DA analysis, each pixel in the rasterized data is evaluated by applying Equation (1) as described in 
{cite:t}`CREASON2022`, producing a DA score for each cell that is unique to each geologic resource type. For the DS 
analysis, the Spatial Implicit Multivariate Probability Assessment (SIMPA) method {cite}`simpa2019` is applied using a 
series of predefined Fuzzy Logic statements, encapsulating the logic of Equations (2), (3), and (4) in 
{cite:t}`CREASON2022`.

The **URC Resource Assessment Method** can be run either using the standalone GUI, or as a command-line tool. The 
former 
configuration is useful for a guided approach to executing the URC mineral-related analyses and previewing the results 
in the tool itself, whereas the latter is useful for integration of the tool into a workflow as part of a batch 
process. Regardless of how it is run, the results of the requested analyses are written to GeoTIFF files, which can be 
imported into most GIS analysis tools. Optionally, when run from the GUI the results of an analysis can be previewed 
within the tool itself.
