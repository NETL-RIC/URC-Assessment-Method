# REE_PE_Score
A collection of scripts to calculate the potential for emplacement of REE's (PE score) for the REE-Sed assessment method. 

Scripts were developed in Jupyter Notebook.  Since arcPy is used, it is recommended to execute these scripts using the ArcGIS Pro instance of Jupyter Notebook.

### Create_PE_Grid_v1
Creates an empty grid with attribute fields for the STA domains.
  * LG: local grid
  * LD: lithologic domain
  * SD: structural domain
  * SA: secondary alteration domain

### Calculate_PE_Score_DA
Takes the empty PE_Grid and calculates a DA. 

**NOTE**: This script does not yet calculate DS and PE score...
