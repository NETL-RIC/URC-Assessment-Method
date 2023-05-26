Example Tutorial
================

A bundled version of the [URC Assessment Method tool can be downloaded from EDX](https://edx.netl.doe.gov/dataset/urc-assessment-method).

For this tutorial, we'll be using the supplementary data for {cite:p}`CREASON2022`, which can be downloaded directly 
from its [EDX submission page](https://edx.netl.doe.gov/dataset/urc-assessment-method-publication-supplementary-files). 
Specifically, you will want to download and unzip the file **esm_3.zip**; you will also need to unzip the file 
**ecm_3/PRB- URC Asessment data/DA & DS databases/DA & DS vector database.zip**


Initial Setup
-------------

![Initial view](_static/example_init.png)

Launch the ***URC Assessment Method*** tool:
    
* If using the Bundled version of the tool, double-click on **URC_Assessment_Method.exe**.
* If running from source, run `urc_assessment_method.py` with no arguments.

Once the tool is loaded, you should see a window similar to the image above.

Leave the **Display Results** box checked.

Configuring the Create Grid Task
--------------------------------

![Create Grid Settings](_static/example_cg_settings.png)

Check the box next to **Create Grid**; a series of options should appear on the right side.

We will set two of the fields in the _Inputs_ box to some of the files provided in **esm.zip**:

* Click on the **Select...** button to the right of the _Structural Domains_ field. Choose the file
  **ecm_3/PRB- URC Asessment data/Domains/PRB_structural_domains.shp** and click on the **Open** button.
* Click on the **Select...** button to the right of the _Lithological Domains_ field. Choose the file
  **ecm_3/PRB- URC Asessment data/Domains/PRB_lithologic_domains.shp** and click on the **Open** button.

In the _Outputs_ box, we will modify the first field:

* Click on the **Select...** to the right of the _Output Directory_. Choose a directory to store the generated index
  (*.tif) files, and click on **Select Folder**.

Leave the rest of the fields set to their defaults.


Configuring the PE Score Task
-----------------------------

![PE Score Settings](_static/example_pes_settings.png)

Check the box next to **PE Score**; once again, a series of options should appear on the right side.

For the _inputs_ dialog we will set a single field:

* To the right of the _Source File_ label, click on the **Select...** button, and choose the **.gdb file** option in the 
  menu. Navigate to **esm_3/PRB- URC Asessment data/DA & DS databases/DA & DS vector database/DA & DS vector database/PRB_URC_DA_DS_Database.gdb**
  and click **Select Folder**.


Executing the Tasks
-------------------

![Progress dialog](_static/example_prog_dlg.png)

At the bottom of the main window, click on the **Run Tasks** button. A new dialog should popup and proceed to display
log messages.

The _Create Grid_ task should finish quickly; the _PE Score_ task may take up to a few hours to complete.

Previewing the Results
----------------------

![Results Dialog](_static/example_results.png)

The Raster Geotiff (*.tif) files are intended to be further evaluated in GIS software suites such as ESRI's 
_[ArcGIS](https://www.arcgis.com/index.html)_ or the free and Open Source _[QGIS](https://qgis.org/)_. However, 
the results can optionally be previewed once the tasks completed if the **Display Results** check box in the main window
remains checked.

The output files that were created are sorted by task in a list on the left side of the result dialog. Select **PE_max**;
this will bring up a black and white display of the output file, _PE_max.tif_. To change the coloring, click on the 
gradient at the bottom of the dialog. This will bring up a gradient editor.

![Gradient Dialog](_static/example_gradient.png)

To the right of the table row with the _Start_ Anchor value, click on the **Select...** dropdown menu and select **Add 
Below**; do this twice. Set the Color and Position values to match the image above (or whatever color values you prefer).
Click **OK**. This will update the color applied to the values for **PE_max** as displayed in the Results Preview dialog.

This concludes the example tutorial. More information on the controls, widgets, and inputs can be found in the [Usage](usage/index.rst)
section of this user documentation.