Put library.meam and CoNiCrFeMn.meam in this folder.
Double-click RUN_ALL_6CORE.bat.
If your executable is lmp_mpi, change set LMP=lmp to set LMP=lmp_mpi.

Scientific limitation:
The paper reports 10,000 CMC steps but does not publish the exact MC-step
definition or source code. This package uses 10,000 total canonical
pair-swap attempts across all ten element pairs while NPT permits atomic
vibration and box change at 1073 K.
