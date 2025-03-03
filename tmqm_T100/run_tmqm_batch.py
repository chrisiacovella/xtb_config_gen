from xtb_config_gen import load_config, run_xtb_calc
from time import time
import h5py
import json
from sqlitedict import SqliteDict
from loguru import logger

filepath = "/home/cri/datasets/hdf5_files/tmqm_dataset_v0.hdf5"
from utils import OpenWithLock

data_input = None
with OpenWithLock(f"../status.lockfile", "w") as lock_file:
    with SqliteDict("../tmqm.db", tablename="status", autocommit=True) as status_db:
        for key in status_db.keys():

            if status_db[key] == "not_submitted":
                with h5py.File(filepath, "r") as f:
                    data_input = load_config(f, key)

                status_db[key] = "submitted"
                break

logger.debug(f"starting: {data_input.name}")
logger.debug(f"n_atoms:  {data_input.geometry.shape[1]}")

start = time()
xtb_properties = run_xtb_calc(data_input, number_of_repeats=10)
end = time()

logger.debug(f"name: {data_input.name}")
logger.debug(f"n_atoms:  {data_input.geometry.shape[1]}")
logger.info(f"Time taken: {end - start}")

with SqliteDict("../tmqm.db", tablename="results", autocommit=True) as results_db:
    results_db[data_input.name] = xtb_properties

with OpenWithLock(f"../status.lockfile", "w") as lock_file:
    with SqliteDict("../tmqm.db", tablename="status", autocommit=True) as status_db:

        status_db[data_input.name] = "completed"
