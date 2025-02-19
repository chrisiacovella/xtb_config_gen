import h5py
from xtb_config_gen import load_config
from matplotlib import pyplot as plt

filepath = "/home/cri/datasets/hdf5_files/tmqm_dataset_v0.hdf5"

sizes = []
with h5py.File(filepath, "r") as f:
    keys = list(f.keys())

    for key in keys:
        data_input = load_config(f, key)
        sizes.append(data_input.geometry.shape[1])


plt.hist(sizes, bins=100)
plt.savefig("size_dist.png")
