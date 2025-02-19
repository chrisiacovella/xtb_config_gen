xtb_config_gen
===

This repository provides classes and datastructures to take a configuration and perform an MD simulation using gfn2-xtb.  This relies upon the [tblite](https://github.com/tblite/tblite) library to calculate the energetics , and the [Atomic Simulation Environment (ASE)](https://wiki.fysik.dtu.dk/ase/) to perform the MD simulation. 

this was specifically designed to be used with the modelforge curated version of the tmQM dataset, but most of the functions are general enough to be used with any configuration (loading from the hdf5 file may require modifications as the property keys may be different).

## Basic usage for tmqm

The files in the tmqm directory provide a basic example scripts of how to use the xtb_config_gen library to perform a MD simulation.  

The file "run_tmqm_single.py" will perform a single MD simulation on a single configuration (currently just the first key in the modelforge tmqm hdf5 file).

To allow large scale calculation of the entire dataset, first run "setup_job_tmqm.py" (note, this requires you to define the location of the hdf5 file).  This will generate an sqlite database that keeps track which configurations have been submitted, completed, as well as storing the final results. 

The "run_tmqm_batch.py" script will run a single calculation, but will query the sqlite database for any runs that have not been submitted.  In my workflows, this script was executed as a background process multiple times in a single batch submission script to allow for parallel execution of multiple calculations. Note, the best performance of the tblite calculation  was found when the number of threads is set to 1. 

To read the final database, use the "read_tmqm_db.py" script.  This will extract the results and save them to an hdf5 file.  Note, since I just simply saved the `xtb_properties` dataclass in the sqlite database, you'll need to execute this in an environment that has the xtb_config_gen library installed.  


