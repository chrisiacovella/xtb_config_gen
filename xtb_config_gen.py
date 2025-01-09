from loguru import logger
import numpy as np
from typing import List
import h5py
from dataclasses import dataclass
from openff.units import unit
from utils import OpenWithLock

# from nist
ev_to_joules = 1.602176634e-19


@dataclass
class DataPointFromHDF5:
    name: str
    n_configs: int
    spin_multiplicity: np.ndarray
    stoichiometry: str
    atomic_numbers: np.ndarray
    geometry: unit.Quantity
    total_charge: unit.Quantity


@dataclass
class DataPoint:
    name: str
    n_configs: int
    spin_multiplicity: np.ndarray
    stoichiometry: str
    atomic_numbers: np.ndarray
    geometry: unit.Quantity
    total_charge: unit.Quantity
    energy: unit.Quantity
    partial_charges: unit.Quantity
    dipole_moment: unit.Quantity
    forces: unit.Quantity


def load_config(file_handle, key: str):
    """
    Load the data for a give key from the HDF5 file.

    parameters
    ----------
    key: str, required
        The key to load from the HDF5 file.
    """
    data_raw = file_handle[key]

    n_configs = data_raw["n_configs"][()]
    spin_multiplicity = data_raw["spin_multiplicity"][()]
    stoichiometry = data_raw["stoichiometry"][()]
    atomic_numbers = data_raw["atomic_numbers"][()]
    geometry = data_raw["geometry"][()] * unit.Unit(data_raw["geometry"].attrs["u"])
    total_charge = data_raw["total_charge"][()] * unit.Unit(
        data_raw["total_charge"].attrs["u"]
    )

    return DataPointFromHDF5(
        name=key,
        n_configs=n_configs,
        spin_multiplicity=spin_multiplicity,
        stoichiometry=stoichiometry,
        atomic_numbers=atomic_numbers,
        geometry=geometry,
        total_charge=total_charge,
    )


from ase import Atoms


@dataclass
class XTBProperties:
    geometry: unit.Quantity
    potential_energy: unit.Quantity
    forces: unit.Quantity
    partial_charges: unit.Quantity
    dipole_moment: unit.Quantity


def get_xtb_properties(mol: Atoms):

    geometry = mol.get_positions() * unit("angstrom")
    potential_energy = mol.get_potential_energy() * ev_to_joules * unit("joule")
    forces = mol.get_forces() * ev_to_joules * unit("joule/angstrom")
    partial_charges = mol.get_charges() * unit("e")
    dipole_moment = mol.get_dipole_moment() * unit("e*angstrom")

    return XTBProperties(
        geometry, potential_energy, forces, partial_charges, dipole_moment
    )


def run_xtb_calc(
    data_input: DataPointFromHDF5,
    number_of_steps: int = 100,
    number_of_repeats: int = 10,
    temperature: unit.Quantity = unit.Quantity(400.0, "K"),
    friction: unit.Quantity = unit.Quantity(0.01, "1/fs"),
    timestep: unit.Quantity = unit.Quantity(1.0, "fs"),
    output_trajectory: bool = False,
    output_log: bool = False,
):
    from ase import Atoms
    from tblite.ase import TBLite
    from ase.optimize import BFGS
    from ase.md import Langevin
    import ase.units as ase_units
    from ase.io.trajectory import Trajectory

    datapoints = []

    # For embedding in modelforge, total charge is initialized as a vector/tensor
    # but this expects a scalar, so we just need to reshape it and drop the units
    total_charge = float(data_input.total_charge.magnitude.reshape(-1)[0])
    spin_multiplicity = float(data_input.spin_multiplicity.reshape(-1)[0])

    # Create two calculators, using the GFN2-xTB method
    # The first will have a higher accuracy; the second less as it will be cheaper for md
    # We will only store properties that come from accuracy = 1
    calc_a1 = TBLite(
        method="GFN2-xTB",
        max_iterations=250,
        charge=total_charge,
        accuracy=1,
        verbosity=0,
        # multiplicity=spin_multiplicity,
    )
    calc_a2 = TBLite(
        method="GFN2-xTB",
        max_iterations=250,
        charge=total_charge,
        accuracy=2,
        verbosity=0,
        # multiplicity=spin_multiplicity,
    )
    n_atoms = data_input.geometry.shape[1]

    # Create the Atoms object to house the molecule
    # note this expects geometry in angstroms
    mol = Atoms(
        numbers=data_input.atomic_numbers.reshape(-1),
        positions=data_input.geometry.to("angstrom").magnitude.reshape(n_atoms, 3),
    )

    mol.calc = calc_a1

    data_point = get_xtb_properties(mol)
    datapoints.append(data_point)

    # Now we will set up an MD simulation using the Langevin integrator
    # note, since we are not using shake constraints, as is the default if running MD via the xtb software directly
    # we need to take a timestep of 1 fs, rather than 4 fs.
    # Since we want to get some fluctuations in bond lengths, not only just different configurations, running without constraints is better.

    mol.calc = calc_a2

    if output_trajectory:
        traj = Trajectory(f"{data_input.name}.traj", "w", mol)

    if output_log and output_trajectory:
        dyn = Langevin(
            mol,
            timestep=timestep.to("fs").m * ase_units.fs,
            temperature_K=temperature.to("K").m,  # temperature in K
            friction=friction.to("1/fs").m / ase_units.fs,
            # trajectory=f"{data_input.name}.traj",
            trajectory=traj,
            logfile=f"{data_input.name}_md.log",
        )
    if output_log and not output_trajectory:
        dyn = Langevin(
            mol,
            timestep=timestep.to("fs").m * ase_units.fs,
            temperature_K=temperature.to("K").m,  # temperature in K
            friction=friction.to("1/fs").m / ase_units.fs,
            logfile=f"{data_input.name}_md.log",
        )
    if not output_log and output_trajectory:
        dyn = Langevin(
            mol,
            timestep=timestep.to("fs").m * ase_units.fs,
            temperature_K=temperature.to("K").m,  # temperature in K
            friction=friction.to("1/fs").m / ase_units.fs,
            trajectory=traj,
        )
    if not output_log and not output_trajectory:
        dyn = Langevin(
            mol,
            timestep=timestep.to("fs").m * ase_units.fs,
            temperature_K=temperature.to("K").m,  # temperature in K
            friction=friction.to("1/fs").m / ase_units.fs,
        )

    for i in range(0, number_of_repeats):
        dyn.run(number_of_steps)

        # use the last snapshot to get the properties
        # run with accuracy = 1
        mol_for_prop = Atoms(
            numbers=mol.get_atomic_numbers(),
            positions=mol.get_positions(),
        )
        # We will only store properties that come from accuracy = 1
        mol_for_prop.calc = calc_a1
        data_point = get_xtb_properties(mol_for_prop)
        datapoints.append(data_point)
        logger.info(f"Completed repeat {i} of {number_of_repeats}")

    # process all the invididual data points into a single record
    geometry = datapoints[0].geometry.reshape(1, n_atoms, 3)
    energy = datapoints[0].potential_energy.reshape(1, 1)
    forces = datapoints[0].forces.reshape(1, n_atoms, 3)
    partial_charges = datapoints[0].partial_charges.reshape(1, n_atoms)
    dipole_moment = datapoints[0].dipole_moment.reshape(1, 3)
    total_charge = data_input.total_charge
    spin_multiplicity = data_input.spin_multiplicity
    for i in range(1, number_of_repeats):
        geometry = np.vstack((geometry, datapoints[i].geometry.reshape(1, n_atoms, 3)))
        energy = np.vstack((energy, datapoints[i].potential_energy.reshape(1, 1)))
        forces = np.vstack((forces, datapoints[i].forces.reshape(1, n_atoms, 3)))
        partial_charges = np.vstack(
            (partial_charges, datapoints[i].partial_charges.reshape(1, n_atoms))
        )
        dipole_moment = np.vstack(
            (dipole_moment, datapoints[i].dipole_moment.reshape(1, 3))
        )
        total_charge = np.vstack((total_charge, data_input.total_charge))
        spin_multiplicity = np.vstack((spin_multiplicity, data_input.spin_multiplicity))

    from utils import chem_context

    data_output = DataPoint(
        name=data_input.name,
        n_configs=len(datapoints),
        stoichiometry=data_input.stoichiometry,
        atomic_numbers=data_input.atomic_numbers,
        geometry=geometry.to("nanometer"),
        energy=energy.to("kilojoule_per_mole", "chem"),
        partial_charges=partial_charges.to("e"),
        dipole_moment=dipole_moment.to("e*nanometer"),
        forces=forces.to("kilojoule_per_mole/nanometer", "chem"),
        spin_multiplicity=spin_multiplicity,
        total_charge=total_charge.to("e", "chem"),
    )
    if output_trajectory:
        from ase.io import write, read

        traj = read(f"{data_input.name}.traj", ":")
        write(f"{data_input.name}.xyz", traj, format="xyz")
    return data_output
