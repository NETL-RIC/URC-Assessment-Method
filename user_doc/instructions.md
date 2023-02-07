Documentation instructions
==========================

What follows are several bits of info for previewing and contributing to the User documentation for this project.


Building the documentation
--------------------------


### Prerequisites

There are several packages that need to be present in your python environment prior to attempting to build. They are as 
follows:

* [sphinx][1] - The tool that's build the documentation.
* [myst-parser][2] - The parser for markdown files; very expansive.
* [sphinxcontrib-bibtex][3] - Sphinx extension for compiling bibtex files (*.bib) into a references list and auto 
                              linking in-text citations.
* [sphinx_rtd_theme][4] - Read the docs style.

These can be installed in one fell swoop with `pip`:

```sh
pip install sphinx myst-parser sphinxcontrib-bibtex sphinx_rtd_theme
```


### Building

Open a terminal connected to your python environment (such as an Anaconda prompt), and move to the directory where this 
document is located. From there you can use the `make.bat` (Windows) or `make.sh` (Linux, MacOs) with the `html` 
argument:

```sh
make.bat html
```

or

```sh
./make.sh html
```

Once the script completes, you should be able to view the results by opening the `index.html` file in the `build/` 
directory.


Adding Content
--------------

For existing files, there are two formats: *.md and *.rst; **stick with \*.md where possible**; they are more 
intuitive to format (index files have to be *.rst, but should only require the occasional modification). 

*.md files are interpreted by [myst-parser][2], which supports an extensive formatting syntax following 
[common markdown][5]; there are [several syntax extensions][6] that can be enabled in the `myst_enable_extensions` list
in the `source/conf.py` file.

There are several tools for editing markdown text files alongside a real time preview; both [PyCharm][7] and [VSCode][8] 
(via plugin) have great support for editing markdown, but any text editor will do.

[Here is a good primer on common-markdown][10].


### Images

Images/figures deserve special mention. Image files (such as PNG or JPEG) can be embedded in the output document. Any 
image to be included should be placed in the `build/_static/` folder. Standard markdown text should include a relative
path from the document to the file.

For example, if a document in the build directory is referencing _blam.png_, The markdown would look something like 
this:

```markdown
    ![image label](_static/blam.png)
```

If finer granularity is required for embedded images, there is a [markdown extension][6] that provides some more 
options.


### Equations

The [amsmath][9] extension is enabled in the `build/conf.py` for the myst-parser. This allows for using laTeX-style
math formulations to produce nice equations. See the provided link for more details.


### Reference citations

Any citations should be placed in the `lit_references.bib` file, following [BibTeX formatting][11]. 
In-text citations can then reference BibTeX entry identifiers.

For example, the following entry for GDAL:

```bibtex
@software{gdal2022,
    title = {{GDAL/OGR} Geospatial Data Abstraction software Library},
    author = {{GDAL/OGR contributors}},
    organization = {Open Source Geospatial Foundation},
    year = {2022},
    url = {https://gdal.org},
    doi = {10.5281/zenodo.5884351},
}
```

Would look something like this:

```markdown
{cite}`gdal2022`
```


Adding a new document to an existing directory
----------------------------------------------

To add a new document (page) to a directory, simply save the document in the directory, and add its name (minus 
extension) to the `index.rst` file somewhere below `.. toctree::` ***at the same indent level as other entries 
underneath*** `.. toctree::`.


Adding a new directory
----------------------

The page structure for the compiled documentation mirrors the directory structure. The following steps will get Sphinx
to recognize it:

1. Create the new directory in an existing directory containing an `index.rst`.
2. Copy the `index.rst` to the new file.
3. Edit the Copied `index.rst`. At the very least you'll want to change the title and remove any existing entries.
4. In the `index.rst` in the **parent directory**, add an entry for the new directory. This will look something like
   `<directory_name>/index`.
5. Proceed to add new files and content as outlined in the previous section.





[1]: https://www.sphinx-doc.org/en/master/
[2]: https://myst-parser.readthedocs.io/en/latest/
[3]: https://sphinxcontrib-bibtex.readthedocs.io/en/latest/quickstart.html
[4]: https://sphinx-rtd-theme.readthedocs.io/en/stable/
[5]: https://myst-parser.readthedocs.io/en/latest/syntax/syntax.html#syntax-core
[6]: https://myst-parser.readthedocs.io/en/latest/syntax/optional.html
[7]: https://www.jetbrains.com/pycharm/
[8]: https://code.visualstudio.com/
[9]: https://myst-parser.readthedocs.io/en/latest/syntax/optional.html#syntax-amsmath
[10]: https://www.markdownguide.org/basic-syntax/
[11]: https://www.bibtex.com/g/bibtex-format/