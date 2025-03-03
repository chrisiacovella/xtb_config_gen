import h5py
import numpy as np

filepath = "/home/cri/mf_datasets/hdf5_files/tmqm_dataset_v1.0.hdf5"
from sqlitedict import SqliteDict

# include Pd, Zn, Fe, Cu, Ni, Pt, Ir, Rh, Cr, Ag
primary_and_secondary_tm_to_extract = [46, 30, 26, 29, 28, 78, 77, 45, 24, 47]

# C, H, P, S O, N, F Cl, Br
organics_to_include = [6, 1, 15, 16, 8, 7, 9, 17, 35]

elements_to_include = np.array(
    primary_and_secondary_tm_to_extract + organics_to_include
)

total = 0

status = {}
with SqliteDict("../tmqm.db", tablename="status", autocommit=True) as tmqm_db:
    with h5py.File(filepath, "r") as f:
        keys = list(f.keys())
        from tqdm import tqdm

        for i in tqdm(range(len(keys))):
            key = keys[i]
            atomic_numbers = f[key]["atomic_numbers"][()]
            status = set(atomic_numbers.flatten()).issubset(elements_to_include)

            if status:
                # status[key] = False
                tmqm_db[key] = "not_submitted"
                total += 1
            else:
                tmqm_db[key] = "not_included"

print(f"Total records: {total}")
