Welcome to the URC Assessment Method contributing guide
=======================================================

Thank you for your interests in contributing to this project! There are several ways one can contribute below; see the 
sections below.


Code Contributions
------------------

This project welcomes public submissions through the use of Github's [pull request](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests)
mechanism.

Please be detailed in your pull request for the reason for your submission, noting the numbers of any relevant open issues.

Python source code should conform to [PEP 8](https://peps.python.org/pep-0008/) standards where possible. All functions,
methods, classes, and modules should be fully documented using [Google-style Docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).
Typing-hinting is optional.

Please ensure that any submissions can pass all unit tests present in the `tests/` directory.


Testing and bug hunting
-----------------------

No software is perfect; no doubt you will come across a bug or two when using this software. If you think you've
encountered a bug, please submit an issue to the [Github repository](https://github.com/NETL-RIC/URC-Assessment-Method/issues)
with the "bug" label applied.

When submitting a bug report, please include the following:

* Steps or actions to take in the tool to reproduce the bug.
* Any console output produced by the tool, particularly stacktraces, if any. This information will be immediately available
  when running directly from the unbundled scripts. For the bundled/executable version, the popup terminal may disappear
  too quickly if the bug results in a crash. To capture this information, you can launch the \*.exe from a console 
  or terminal window, copying the output from it after the crash event occurs.
* Any settings (\*.jurc) or input files that may be involved in producing the bug, if possible.
* Any other information you think is pertinent.


User Documentation
------------------

The user documentation for this software is produced from source code using [Sphinx](https://www.sphinx-doc.org/).
The source code for the documentation can be found in `user_doc/source`. Content can be provided in the form of 
[reStructuredText](https://docutils.sourceforge.io/rst.html) ( \*.rst), [markdown](https://www.markdownguide.org/basic-syntax/)
(\*.md), and plain (\*.txt) files. Media to be embedded in the documentation (images, videos, and similar) should be placed
in `user_doc/source/_static`.

Documentation edits can be submitted using the instructions as outlined in the [Code Contributions](#code-contributions)
section. Please ensure that the documentation can be successfully compiled into html by Sphinx prior to submitting a
pull request.


Examples and Tutorials
----------------------

There is always a need for more user examples and tutorials. Please consider submitting written tutorials and/or examples
to aid others using this tool.