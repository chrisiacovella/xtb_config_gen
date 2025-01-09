import h5py
from utils import OpenWithLock

filepath = "/home/cri/datasets/hdf5_files/tmqm_dataset_v0.hdf5"
from sqlitedict import SqliteDict

status = {}
with SqliteDict("tmqm.db", tablename="status", autocommit=True) as tmqm_db:
    with h5py.File(filepath, "r") as f:
        keys = list(f.keys())
        from tqdm import tqdm

        for i in tqdm(range(len(keys))):
            key = keys[i]
            # status[key] = False
            tmqm_db[key] = "not_submitted"


# import json
#
# with open("status.json", "w") as f:
#     json.dump(status, f)
#
# print(len(status))
