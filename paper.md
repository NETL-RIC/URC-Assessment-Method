
---
title: 'A Python Tool for Predicting and Assessing Unconventional Rare-Earth and Critical Mineral Resources'
tags:
  - Python
  - Rare-Earth Elements
  - Geology
  - Coal Formations
  - subsurface
authors:
  - name: Patrick Wingo
    orcid: 0000-0003-3934-7733
    corresponding: true
    affiliation: "1, 2"
  - name: Devin Justman
    affiliation: "1, 2"
  - name: C. Gabriel Creason
    orcid: 0000-0002-3440-1174
    affiliation: "1, 3"
  - name: Mackenzie Mark-Moser
    orcid: 0000-0001-5138-5527
    affiliation: "1, 2"
  - name: Scott Montross
    orcid: 0000-0002-6551-7700
    affiliation: "1, 2"
  - name: Kelly Rose
    orcid: 0000-0001-6130-4727
    affiliation: 1


affiliations:
 - name: National Energy Technology Laboratory (NETL), USA
   index: 1
 - name: NETL Support Contractor, USA
   index: 2
 - name: Oak Ridge Institute for Science and Education (ORISE), USA
   index: 3

date: 31 March 2023
bibliography: paper.bib

---

# Summary

[U]{.underline}nconventional [R]{.underline}are-earth elements & [C]{.underline}ritical minerals (URC) [@osti_1891489] 
are crucial to a growing number of industries worldwide [@BALARAM20191285]. Due to their use in manufacturing, Critical
Minerals (CM) are essential to economic and national security, yet have supply chains vulnerable to external 
disruptions [@osti_1891489]. _Unconventional_ CM are sourced from geologic or byproduct hosts distinctly separate from 
the mechanisms which establish conventional CM deposits [@osti_1891489]. Unconventional sources for CM include 
_in situ_ geologic deposits and byproducts of industrial extraction [@osti_1891489].
 
The extraction and recovery of conventional CM is a complex process traditionally involving strip mining, which is both 
expensive and environmentally destructive [@BALARAM20191285]. Recent research has revealed that coaliferous sediments
may act as unconventional CM sources containing Rare-Earth Elements (REE) in significant concentrations 
[@SEREDIN201267]. Determining the likelihood and location of REE resources in sedimentary basins is both 
complex and challenging. To address this, a new method of evaluating the potential occurrence of URC resources using 
a series of validated heuristics has been developed [@CREASON2023]. While the entire process can be carried out 
manually using a collection of tools, a new, standalone software tool has been developed to streamline and expedite 
the process: NETL's `URC Resource Assessment Tool`.


# Statement of need

The `URC Resource Assessment Tool` applies the data analysis methods outlined in @CREASON2023, the tool's companion 
paper. This tool is a complete application written in Python and built on top of several open-source libraries (see the 
[Support Libraries](#support-libraries) section). The intended users for this tool are geologists and geospatial 
scientists who are looking to better understand the mode and spatial distribution of potential URC resource occurrences 
in sedimentary basins.

There are several ways that the `URC Resource Assessment Tool` can be configured to run, but fundamentally the tool 
takes in a collection of spatial domains which fall under the Lithological, Structural, and Secondary Alteration 
categories defined by the Subsurface Trend Analysis (STA) method [@sta2019]. These domains are combined, clipped 
to a researcher-defined boundary, and grided to cells of a research-specified dimension (see \autoref{fig:cg_flow} for 
overview of the process).

From this point, a Data Availability (DA) and / or a Data Supporting (DS) analysis can be undertaken by the tool 
(\autoref{fig:pes_flow}); both analyses will operate on a vector-based spatial dataset describing the target formation,
following the labelling scheme specified in the supplementary material in @CREASON2023. These data are rasterized 
according to the grid specification of the aforementioned domains with each cell tagged with the appropriate set of 
indices. In the case of a DA analysis, each pixel in the rasterized data is evaluated by applying Equation (1) as 
described in @CREASON2023, producing a DA score for each cell that is unique to each geologic resource type. For the DS 
analysis, the Spatial Implicit Multivariate Probability Assessment (SIMPA) method [@simpa2019] is applied using a series
 of predefined Fuzzy Logic statements, encapsulating the logic of Equations (2), (3), and (4) in @CREASON2023.

The `URC Resource Assessment Tool` can be run either using the standalone GUI, or as a command-line tool. The former 
configuration is useful for a guided approach to executing the URC mineral-related analyses and previewing the results 
in the tool itself, whereas the latter is useful for integration of the tool into a workflow as part of a batch 
process. Regardless of how it is run, the results of the requested analyses are written to GeoTIFF files, which can be 
imported into most geospatial information systems analysis tools. Optionally, when run from the GUI the results 
of an analysis can be previewed within the tool itself (\autoref{fig:urc_out}).

# Implementation Details

The `URC Resource Assessment Tool` relies on several existing open source libraries to perform its analyses. The
[Geospatial Data Abstraction Library](https://www.gdal.org) (GDAL) is utilized for managing geospatial inputs 
and outputs, projection transformations, and converting vector layers into raster layers. 
Rasters are converted to two-dimensional [NumPy](https://numpy.org/) arrays, during arithmetic processing to both
reduce code complexity and potentially reduce time complexity through NumPy's hardware optimizations, such as 
Advanced Vector Extensions (AVX) utilization on Intel hardware [@npsimd].

Data analyses pertaining to DA were carried out using [Pandas](https://pandas.pydata.org/). Raster information is 
converted into a Pandas DataFrame object, with each column representing a layer, and each row representing a pixel 
location. Sums are calculated according to the DA scoring algorithm outlined in @CREASON2023, with the final results 
taken from the pandas Dataframe and converted into geospatial rasters.

The fuzzy logic statements driving the DS analysis are authored using the 
[SIMPA tool](https://edx.netl.doe.gov/dataset/simpa-tool), and then baked into the `URC Resource Assessment Tool` by 
using the embedded urclib.fuzzylogic package to convert the logic to Python. The collection of fuzzy logic statements 
are executed across all rasters on a per-pixel coordinate basis. This creates a Single Instruction, Multiple Data 
(SIMD) condition which is heavily parallelized using python's `multiprocessing` module, further reducing time complexity
and noticeably reducing overall processing time. 

For more information on how the fuzzy logic library works, see the SIMPA tool documentation [@simpa2019].


## Support Libraries

In addition to several core Python libraries, The following 3rd-party libraries were used to create this tool:

* [GDAL](https://www.gdal.org), _v3.1.4_: Used for general spatial data management and calculations [@gdal2022].
* [NumPy](https://numpy.org/), _v1.23.2_: Handled vector math and general numeric array management [@harris2020array]. 
* [Pandas](https://pandas.pydata.org/), _v1.2.5_: Utilized for statistical calculations for the _Data Available_ (DA) 
  scoring [@reback2020pandas].
* [SIMPA](https://edx.netl.doe.gov/dataset/simpa-tool), _v2.0.0_: Tool for processing spatially explicit raster data 
  using fuzzy logic statements. Used in _Data Supporting_ (DS) scoring [@simpa2019].
* [PyQt](https://riverbankcomputing.com/software/pyqt/), _v5.15.6_: Framework used to build the graphical user interface 
  (GUI) for the tool; built on [Qt](https://www.qt.io) [@pyqt2022; @qt2022].
* [PyOpenGL](https://pyopengl.sourceforge.net/), _v3.1.6_: Wrapper for [OpenGL](https://www.opengl.org/) API; used for 
  map visualization [@pyOGL2022; @openGL2017].
  * PyOpenGL-accelerate, _v3.1.6_: Optional library which can increase the performance of PyOpenGL [@pyOGL2022].
* [pyGLM](https://github.com/Zuzu-Typ/PyGLM), _v2.2.0_: Python port of the [GLM](https://glm.g-truc.net/0.9.9/) library; 
  used for graphic-specific mathematics [@pyglm2022;@glm2020].


# Figures

![High level overview of the tool workflow when carrying out the _Create Grid_ task. Domains created using the STA 
method [@sta2019] are rasterized using the provided width and height values for each pixel. If desired a geospatial 
projection can be specified to be assigned to the results by providing a projection or European Petroleum Survey 
Group (EPSG) code as a "projection override". This task produces a series of index rasters suitable as inputs to the 
_Potential Enrichment (PE) Score Task_. \label{fig:cg_flow}](fig_create_grid.png)


![High level overview of the tool workflow when carrying out the _Potential Enrichment (PE) Score_ task. Inputs for 
this task include index rasters generated from a previous execution of the _Create Grid Task_, a collection of site 
geologic data in the form of spatial vector layers, and an optional clipping mask. This information is used to produce 
analyses of both Data Available (DA) and Data Supporting (DS) layers provided as part of the site geologic data, 
providing insight into the likelihood of the presence of URC resources. \label{fig:pes_flow}](fig_pe_score.png)


![Example Result preview generated by URC Resource Assessment Method Tool; the selected output shows a map colored 
according to PE score for Meteoric Adsorption (MA). All spatially explicit outputs can be previewed with 
user-configurable color scales. \label{fig:urc_out}](fig_pe_ma_result.png)


# Acknowledgements & Disclaimer

Disclaimer:  This project was funded by the U.S. Department of Energy, National Energy Technology Laboratory, in part, 
through a site support contract. Neither the United States Government nor any agency thereof, nor any of their employees, 
nor the support contractor, nor any of their employees, makes any warranty, express or implied, or assumes any legal 
liability or responsibility for the accuracy, completeness, or usefulness of any information, apparatus, product, or 
process disclosed, or represents that its use would not infringe privately owned rights.  Reference herein to any 
specific commercial product, process, or service by trade name, trademark, manufacturer, or otherwise does not 
necessarily constitute or imply its endorsement, recommendation, or favoring by the United States Government or any 
agency thereof. The views and opinions of authors expressed herein do not necessarily state or reflect those of the 
United States Government or any agency thereof. 

Acknowledgement: Parts of this technical effort were performed in support of the National Energy Technology Laboratory’s 
(NETL) ongoing research under the Critical Minerals Field Work Proposal by NETL’s Research and Innovation Center. The 
authors are grateful for literature synthesis provided by Jenny DiGuilio, Nicole Rocco, Roy Miller III, and Emily Cameron 
early in the development of the URC resource assessment method. Technical discussions with Davin Bagdonas, Leslie “Jingle” 
Ruppert, and Paige Morkner aided development and led to the advancement of the assessment method. Development and 
validation of the URC method benefited from geologic core and coal samples provided by the University of Wyoming, U.S. 
Geologic Survey, West Virginia Geological and Economic Survey, and Ramaco Carbon. 

# References
