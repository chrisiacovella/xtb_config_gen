from xtb_config_gen import load_config, run_xtb_calc
from time import time
import h5py
import json
from sqlitedict import SqliteDict


filepath = "/home/cri/datasets/hdf5_files/tmqm_dataset_v0.hdf5"
from utils import OpenWithLock

with OpenWithLock(f"status.lockfile", "w") as lock_file:
    with SqliteDict("tmqm.db", tablename="status", autocommit=True) as status_db:
        for key in status_db.keys():

            if not status_db[key]:
                with h5py.File(filepath, "r") as f:
                    data_input = load_config(f, key)

            status_db[key] = True
            break

start = time()
xtb_properties = run_xtb_calc(data_input)
end = time()

print("name: ", data_input.name)
print("n_atoms: ", xtb_properties.geometry.shape[1])
print(f"Time taken: {end-start}")

with SqliteDict("tmqm.db", tablename="results", autocommit=True) as results_db:
    results_db[data_input.name] = xtb_properties


# with OpenWithLock(f"{filepath}.lockfile", "w") as lock_file:
#
#     with h5py.File(filepath, "r") as f:
#         keys = list(f.keys())

#     with SqliteDict(
#             "tmqm.db",
#             tablename="tmqm",
#             autocommit=True,
#     ) as tmqm_db:
#         for key in keys:
#             if key not in tmqm_db:
#                 data_input = load_config(f, key)
#
#                 xtb_properties = run_xtb_calc(data_input)
#                 tmqm_db[key] = xtb_properties
# data_input = load_config(f, keys[0])
#
# start = time()
# xtb_properties = run_xtb_calc(data_input)
# end = time()
#
# print("n_atoms: ", xtb_properties.geometry.shape[1])
# print(f"Time taken: {end-start}")
