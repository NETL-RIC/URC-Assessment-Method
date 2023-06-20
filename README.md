# URC Analysis Tools

_Latest Release: 1.0.0_

Logic for running **Unconventional Rare-Earth & Critical Minerals (URC)** analyses on structured data, wrapped into a
tool.

The tool documentation can be built using Sphinx with the content in the `user_doc` folder. Alternately, a compiled version of the 
documentation is mirrored on ReadTheDocs.io [here](https://urc-assessment-method.readthedocs.io/en/latest/).

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
