The main window provides two tasks to execute the Unconventional Resource Assessment (URC) tool. The first task is Create Grid. 

Select Create Grid to provide inputs for the URC assessment grid, define the grid cell size, and produce raster outputs for use as inputs in the PE Score Task. 

*Inputs*

File types should be shapefile (.shp), except if adding a Projection Override (.prj). 
Structural Domain inputs are required, user-defined spatially-constrained domains for structural geology.  
Lithologic Domain inputs are required, user-defined spatially-constrained geologic domains for lithology. 
Secondary Alteration Domain inputs are optional, user-defined spatially-constrained geologic domains for secondary alteration. 
(CHECK THIS) Projection Override allows the user to upload the preferred projection for the grid outputs. 

*Grid Cell Dimensions*

The user may enter the grid cell dimensions for the grid outputs. A standard grid size of 1000 x 1000 is provided. The cell unit of measurement will be defined per the input spatial file(s)' units. 
_Note_ smaller grid cell dimensions will potentially increase processing time. 

*Outputs*

The user will define an output directory for the grid output rasters in TIFF format. File names for the output grid rasters (indices) are predefined but can be altered by the user. 

Once the user has completed Inputs, Grid Cell Dimensions, and Outputs, the user may select "Run Tasks". To show results, check "Display Results" and the raster outputs will be shown after processing is complete. 
