def lock_file(file_handle):
    """
    Locks the file stream for exclusive access using fcntl.

    Parameters
    ----------
    file_handle: file stream, required
        File stream to lock.

    Examples
    --------
    >>> with open('test.txt', 'r') as f:
    >>>    lock_file(f)
    """

    import fcntl

    fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX)


def unlock_file(file_handle):
    """
    Unlocks the file stream using fcntl.

    Parameters
    ----------
    file_handle: file stream, required
        File stream to unlock.

    Examples
    --------
    >>> with open('test.txt', 'r') as f:
    >>>    unlock_file(f)
    """

    import fcntl

    fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)


def check_file_lock(file_handle):
    """
    Checks if the file stream is locked using fcntl.

    Parameters
    ----------
    file_handle: file stream, required
        File stream to check.

    Returns
    -------
    bool
        True if the file is locked, False if the file is unlocked.

    Examples
    --------
    >>> with open('test.txt', 'r') as f:
    >>>    is_locked = check_file_lock(f)
    """

    import fcntl

    try:
        fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except:
        return True

    return False


class OpenWithLock:
    """
    Context manager for opening a file that also locks the file for exclusive access.

    This will automatically check if the file is locked by another process and wait until the lock is released.

    Parameters
    ----------
    file_path: str, required
        Path to the file to open.
    mode: str, optional, default='r'
        Specifies how to open the file, matching the python open function.
        Options are 'r', 'w', 'a', 'r+', 'w+', 'a+', 'rb', 'wb', 'ab', 'r+b', 'w+b', 'a+b'

    Examples
    --------
    >>>
    >>> with OpenWithLock('test.txt', 'r') as f:
    >>>    print(f.read())

    """

    def __init__(self, file_path: str, mode: str = "r"):
        self._file_path = file_path
        self._mode = mode
        self._file_handle = None

    def __enter__(self):
        # open the file
        self._file_handle = open(self._file_path, self._mode)

        # check to see if the file is already locked
        if check_file_lock(self._file_handle):
            logger.debug(
                f"{self._file_path} in locked by another process; waiting until lock is released."
            )

        # try to lock the file; if the file is already locked, this will wait
        # until the file is released. I added helper function definitions that
        # call fcntl, as we might not always want to use a context manager and
        # to test the function in isolation

        lock_file(self._file_handle)

        # return the opened file stream
        return self._file_handle

    def __exit__(self, *args):
        # unlock the file and close the file stream
        unlock_file(self._file_handle)
        self._file_handle.close()


from openff.units import unit

# Define a chemical context for unit transformations
# This allows conversions between energy units like hartree and kJ/mol
__all__ = ["chem_context"]
chem_context = unit.Context("chem")

# Add transformations to handle conversions between energy units per substance
# (mole) and other forms
chem_context.add_transformation(
    "[force] * [length]",
    "[force] * [length]/[substance]",
    lambda unit, x: x * unit.avogadro_constant,
)
chem_context.add_transformation(
    "[force] * [length]/[substance]",
    "[force] * [length]",
    lambda unit, x: x / unit.avogadro_constant,
)
chem_context.add_transformation(
    "[force] * [length]/[length]",
    "[force] * [length]/[substance]/[length]",
    lambda unit, x: x * unit.avogadro_constant,
)
chem_context.add_transformation(
    "[force] * [length]/[substance]/[length]",
    "[force] * [length]/[length]",
    lambda unit, x: x / unit.avogadro_constant,
)

chem_context.add_transformation(
    "[force] * [length]/[length]/[length]",
    "[force] * [length]/[substance]/[length]/[length]",
    lambda unit, x: x * unit.avogadro_constant,
)
chem_context.add_transformation(
    "[force] * [length]/[substance]/[length]/[length]",
    "[force] * [length]/[length]/[length]",
    lambda unit, x: x / unit.avogadro_constant,
)

# Register the custom chemical context for use with the unit system
unit.add_context(chem_context)
