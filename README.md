# URC Assessment Method

_Latest Release: 1.0.1_

Logic for running **Unconventional Rare-Earth & Critical Minerals (URC)** analyses on structured data, wrapped into a
tool.

The tool documentation can be built using Sphinx with the content in the `user_doc` folder. Alternately, a compiled 
version of the documentation is mirrored on ReadTheDocs.io 
[here](https://urc-assessment-method.readthedocs.io/en/latest/).

The [license](./LICENSE) and [contribution instructions](./CONTRIBUTING.md) are also included as part of this 
distribution.

---
## Statement of Need

The **URC Resource Assessment Method** applies the data analysis methods outlined in [Creason et al.][1] This tool 
is a complete application written in Python and built on top of several [open-source libraries](#package-dependencies). 
No other Python packages are known to contain the combination of geospatial information systems (GIS) and fuzzy logic 
support required to directly implement the method defined in [Creason et al.][1] The intended users for this tool are 
geologists and geospatial scientists who are looking to better understand the mode and spatial distribution of potential
URC resource occurrences in sedimentary basins.

There are several ways that the **URC Resource Assessment Method** can be configured to run, but fundamentally the tool 
takes in a collection of spatial domains which fall under the Lithological, Structural, and Secondary Alteration 
categories defined by the [Subsurface Trend Analysis (STA) method][2]. These domains are combined, clipped to a 
researcher-defined boundary, and grided to cells of a research-specified dimension.

From this point, a Data Availability (DA) and / or a Data Supporting (DS) analysis can be undertaken by the tool; both 
analyses will operate on a vector-based spatial dataset describing the target formation, following the labelling scheme 
specified in the supplementary material in [Creason et. al.][1] These data are rasterized according to the grid 
specification of the aforementioned domains with each cell tagged with the appropriate set of indices. In the case of a 
DA analysis, each pixel in the rasterized data is evaluated by applying Equation (1) as described in 
[Creason et. al.][1], producing a DA score for each cell that is unique to each geologic resource type. For the DS 
analysis, the [Spatial Implicit Multivariate Probability Assessment (SIMPA) method][3] is applied using a series of 
predefined Fuzzy Logic statements, encapsulating the logic of Equations (2), (3), and (4) in [Creason et. al.][1]

The **URC Resource Assessment Method** can be run either using the standalone GUI, or as a command-line tool. The 
former configuration is useful for a guided approach to executing the URC mineral-related analyses and previewing the 
results in the tool itself, whereas the latter is useful for integration of the tool into a workflow as part of a batch
process. Regardless of how it is run, the results of the requested analyses are written to GeoTIFF files, which can be
imported into most GIS analysis tools. Optionally, when run from the GUI the results of an analysis can be previewed 
within the tool itself.

[1]: https://doi.org/10.1007/s11053-023-10163-x
[2]: https://doi.org/10.1190/INT-2019-0019.1
[3]: https://edx.netl.doe.gov/dataset/simpa-tool


---

## Installation

Installation will require downloading/cloning this respository.

Ensure that all the packages in the [Package Dependencies](#package-dependencies) section of this document are installed in the environment under which the **URC Assessment Method** is to be run. Provided this requirement is met, the code in in this distribution 
can be run as-is by following the instructions in the [How To Run](#how-to-run) section.

If challenges are encountered when attempting to download and install the required packages, see the [Installation 
Tips and Troubleshooting](#installation-tips-and-troubleshooting) section, below.

---

## How To Run

The tool can be launched by running the `urc_assessment_method.py` script. Running with no arguments will launch the Graphical User
Interface (GUI). Launching with command line arguments will run the tool in ___batch execution___ mode. To see the
arguments for the command line interface (CLI), launch with `urc_assessment_method.py <task> -h`, where `<task>` is one of the labels
provided in the next section.

An Example Tutorial can be found in the user documentation, or at the [ReadtheDocs.io mirror](https://urc-assessment-method.readthedocs.io/en/latest/example.html).

### Available Processes Tasks

 * **Create Grid**: Generate index files for the various domain types which is scaled to a specific grid cell size.
   This task can be invoked using the CLI by specifying the `create_grid` task.
 * **Calculate PE Score**: Utilize the outputs from the **Create Grid** task and apply to a specified, structured
   dataset to calculate the PE Score for various mechanisms. This task can be invoked from the CLI by specifying the
   `pe_score` task.

### Running Unit Tests

Unit Tests exist for the core utility functions within the `urclib` package, namely `common_utils.py` and 
`urc_common.py`. These tests can be run using [pytest](https://docs.pytest.org/), namely by opening a terminal in the
root directory of the repository, and running:

```shell
pytest
```

---
## Package Dependencies

The code in this repository targets [Python](https://www.python.org) version _3.7_ or _greater_.

The following packages are necessary for running the URC tool; optional dependencies are marked with an asterisk (__*__):

* [NumPy](https://numpy.org): Any recent version should do, but tested against _1.20.3_.
* [pandas](https://pandas.pydata.org/): Tested with _1.2.5_.
* [GDAL](https://gdal.org): Tested with version _3.3.0_, and should work with more recent versions.
* [PyQt5](https://riverbankcomputing.com/software/pyqt/intro) __*__: Tested against _5.15.2_, but any _5.15.x_ version should
  work. Only required if running `urc_assessment_method.py` with the GUI active. Based on the [Qt](https://doc.qt.io/qt-5/) library.
* [PyOpenGL](https://pyopengl.sourceforge.net/) __*__: Only required if `urc_assessment_method.py` is run with GUI active. Version 
  _3.1.6_.
* [PyOpenGL-accelerate](https://pyopengl.sourceforge.net/) __*__: strictly optional; improves performance of OpenGL 
  operations invoked by PyOpenGL; version should match with PyOpenGL: _3.1.6_.
* [PyGLM](https://github.com/Zuzu-Typ/PyGLM) __*__: Only required if `urc_assessment_method.py` is run with GUI active. Version _2.2.0_.

---

## Installation Tips and Troubleshooting

### Virtual Environments

It is recommended to run this software under a freshly created virtual environment. To this end, a pair of _ad hoc_ 
requirements files are provided, one for using Python's standard [venv](https://docs.python.org/3/library/venv.html) 
package, and one for 
[virtual environments using Anaconda](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html).

To build an environment using `venv`:

```shell
python3 -mvenv urc_env
source urc_env/bin/activate

python -mpip install -r requirements.txt
```

To build an environment using `conda`:
```shell
conda env create -n URC --file environment.yml
```

### Notes on installing GDAL

GDAL can be tricky to install. For ___Windows___, it is recommended using Anaconda with 
the following install command:

```shell
conda install -c conda-forge gdal
```

For ___Linux___ it is recommended to use `pip` with the following steps:

1. Install the GDAL developer and binary files using the package manager and packages appropriate for your Linux 
   distribution. For ___Ubuntu___, this would look something like:
   ```shell
   sudo apt update
   sudo apt install libgdal-dev gdal-data
   ```
2. Install the GDAL python bindings using `pip`, ensuring that the bindings version matches the previously installed 
   libraries. This can be done through the clever use of `gdal-config`:
   ```shell
   pip install gdal==$(gdal-config --version)
   ```
   
Further information on installing GDAL and working within Python can be found in the 
[Binaries](https://gdal.org/download.html#binaries) 
and [Python Bindings](https://gdal.org/api/python_bindings.html) sections of the official 
[GDAL website](https://gdal.org).
