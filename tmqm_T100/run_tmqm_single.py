from xtb_config_gen import load_config, run_xtb_calc
from time import time
import h5py
import json
from sqlitedict import SqliteDict
from loguru import logger

filepath = "/home/cri/datasets/hdf5_files/tmqm_dataset_v0.hdf5"
from utils import OpenWithLock


with h5py.File(filepath, "r") as f:
    keys = list(f.keys())
    key = keys[0]
    data_input = load_config(f, key)

start = time()
xtb_properties = run_xtb_calc(data_input)
end = time()

logger.debug(f"name: {data_input.name}")
logger.debug(f"n_atoms:  {data_input.geometry.shape[1]}")
logger.info(f"Time taken: {end - start}")
