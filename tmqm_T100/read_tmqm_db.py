import h5py
import sqlitedict
from openff.units import unit


class XTBProperties:
    geometry: unit.Quantity
    potential_energy: unit.Quantity
    forces: unit.Quantity
    partial_charges: unit.Quantity
    dipole_moment: unit.Quantity


from tqdm import tqdm

dt = h5py.special_dtype(vlen=str)

tmqm_db_filepath = "/home/cri/mf_datasets/tmqm_xtb_dataset/tmqm.db"
dump_to_hdf5_name = "/home/cri/mf_datasets/tmqm_xtb_dataset/tmqm_dataset_xtb_T400.hdf5"
with sqlitedict.SqliteDict(
    tmqm_db_filepath, tablename="results", autocommit=True
) as tmqm_db:

    keys = list(tmqm_db.keys())

    with h5py.File(dump_to_hdf5_name, "w") as f:
        for key in tqdm(keys):
            xtb_properties = tmqm_db[key]
            # print(xtb_properties)

            record = f.create_group(key)
            record.create_dataset(
                "atomic_numbers",
                data=xtb_properties.atomic_numbers,
                shape=xtb_properties.atomic_numbers.shape,
            )
            record.create_dataset(
                "geometry",
                data=xtb_properties.geometry.m,
                shape=xtb_properties.geometry.shape,
            )
            record["geometry"].attrs["u"] = str(xtb_properties.geometry.u)

            record.create_dataset(
                "energy",
                data=xtb_properties.energy.m,
                shape=xtb_properties.energy.shape,
            )
            record["energy"].attrs["u"] = str(xtb_properties.energy.u)

            record.create_dataset(
                "forces",
                data=xtb_properties.forces.m,
                shape=xtb_properties.forces.shape,
            )
            record["forces"].attrs["u"] = str(xtb_properties.forces.u)

            record.create_dataset(
                "partial_charges",
                data=xtb_properties.partial_charges.m,
                shape=xtb_properties.partial_charges.shape,
            )
            record["partial_charges"].attrs["u"] = str(xtb_properties.partial_charges.u)

            record.create_dataset(
                "dipole_moment",
                data=xtb_properties.dipole_moment.m,
                shape=xtb_properties.dipole_moment.shape,
            )
            record["dipole_moment"].attrs["u"] = str(xtb_properties.dipole_moment.u)

            record.create_dataset(
                "total_charge",
                data=xtb_properties.total_charge.m,
                shape=xtb_properties.total_charge.shape,
            )
            record["total_charge"].attrs["u"] = str(xtb_properties.total_charge.u)

            record.create_dataset(
                "spin_multiplicity",
                data=xtb_properties.spin_multiplicity,
                shape=xtb_properties.spin_multiplicity.shape,
            )

            record.create_dataset("n_configs", data=xtb_properties.n_configs)

            record.create_dataset(
                "stoichiometry", data=xtb_properties.stoichiometry, dtype=dt
            )

            # f.create_dataset(key, data=xtb_properties)
