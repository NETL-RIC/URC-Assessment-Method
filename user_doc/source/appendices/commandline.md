Command Line Interface
======================

The **URC Method Tool** has a command line interface, which allows for individual tasks to be 
executed without invoking the graphical user interface.

When using the command line, the first argument is always `-h` or `--help` (to display the top level help text), or the 
identifier for the _task_ to be executed. The following tasks are available:

* `create_grid`: Selects the [Create Grid Task](../usage/create_grid_task.md).
* `pe_score`: Selects the [PE Score Task](../usage/pe_score_task.md).

Create Grid Arguments
---------------------

The following information is also accessible by running:

```sh
urc_tool.py create_grid -h
```

### Usage

```sh
urc_tool.py create_grid [-h] [-W GRIDWIDTH] [-H GRIDHEIGHT] [--SD_input_file IN_SD_INPUT_FILE]
                               [--LD_input_file IN_LD_INPUT_FILE] [--SA_input_file IN_SA_INPUT_FILE]
                               [--prj_file IN_PRJ_FILE] [--prj_epsg PRJ_EPSG] [--ld_raster OUT_LD]
                               [--lg_raster OUT_LG] [--sd_raster OUT_SD] [--ud_raster OUT_UD] [--sa_raster OUT_SA]
                               workspace out_workspace
```

### Positional Arguments

`workspace`
: Path to the root input/workspace directory.

`out_workspace`
: Path to the root output/workspace directory.


### Optional Arguments

`-W, --gridwidth`
: Set the width of a grid cell; defaults to 1000 in projection units.

`-H, --gridheight`
: Set height of a grid cell; defaults to 1000 in projection units.

#### Input File Overrides

`--SD_input_file`
: Structural Domain input file. Defaults to `SD_input_file.shp` in **`out_workspace`**.

`--LD_input_file`
: Lithological Domain input file. Defaults to `LD_input_file.shp` in **`out_workspace`**.

`--SA_input_file`
: Secondary Alteration Domain input file. Optional; omitted from grid creation if absent.

`--prj_file`
: The projection to apply to the output data provided as a `*.prj` file. Defaults to the projection of the first input
  file received. Cannot be passed with **`--prj_epsg`**.

`--prj_epsg`
: The projection to apply to the output data provided as an EPSG code. Defaults to the projection of the first input
  file received. Cannot be passed with **`--prj_file`**.

#### Output Filename Overrides

The following arguments can pass in absolute paths, or paths relative to ***outworkspace***.

`--ld_raster` 
: Raster containing LD indices. Defaults to `ld_inds.tif`.
  
`--lg_raster`
: Raster containing LG indices. Defaults to `lg_inds.tif`.

`--sd_raster` 
: Raster containing SD indices. Defaults to `sd_inds.tif`.

`--ud_raster`
: Raster containing UD indices. Defaults to `ud_inds.tif`. 

`--sa_raster`
: Raster containing SA indices. Defaults to `sa_inds.tif`. Ignored if ***`--SA_input_file`*** is not provided.

---

PE Score Arguments
------------------

The following information is also accessible by running:

```sh
urc_tool.py pe_score -h
```


### Usage

```sh
 urc_tool.py pe_score [-h] [--clip_layer IN_CLIP_LAYER] [--no_da] [--no_ds] [--ld_raster IN_LD_INDS]
                            [--lg_raster IN_LG_INDS] [--sd_raster IN_SD_INDS] [--ud_raster IN_UD_INDS]
                            [--sa_raster IN_SA_INDS] [--raster_dump_dir OUT_RASTER_DIR] [--exit_on_raster_dump]
                            gdb_path workspace output_dir
```

### Positional Arguments

`gdb_path`
: Path to the `*.gdb` file to process.

`workspace`
: Path to the root input/workspace directory.

`output_dir`
: Path to the directory where results are to be saved.

### Optional Arguments

`--clip_layer`
: Optional vector layer to apply as a clipping mask for the final results.

`--no_da`
: Skip DA calculation. Cannot be supplied with **`--no_ds`**.

`--no_ds`
: Skip DS calculation. Cannot be supplied with **`--no_da`**.

`--ld_raster`
: Raster containing LD indices. Defaults to `ld_inds.tif` in **`workspace`**.

`--lg_raster`
: Raster containing LG indices. Defaults to `lg_inds.tif` in **`workspace`**.

`--sd_raster`
: Raster containing SD indices. Defaults to `sd_inds.tif` in **`workspace`**.

`--ud_raster`
: Raster containing UD indices. Defaults to `ud_inds.tif` in **`workspace`**.

`--sa_raster`
: Raster containing SA indices. These indices will be omitted from the analysis if not explicitly provided.

`--raster_dump_dir`
: If a directory path is provided, intermediate raster data will be written to it.

`--exit_on_raster_dump`
: If this flag is provided, program will exit after the intermediate rasters have been dumped; this has no effect if 
  **`--raster_dump_dir`** is not present in the argument list.
