from pathlib import Path
from typing import Any

import ribasim
import tomli_w
from imod.mf6 import Modflow6Simulation

from primod.coupledmodel import CoupledModel
from primod.driver_coupling.ribamod import RibaModDriverCoupling
from primod.driver_coupling.util import (
    _validate_time_window,
)


class RibaMod(CoupledModel):
    """Couple Ribasim and MODFLOW 6.

    Parameters
    ----------
    ribasim_model : ribasim.model
        The Ribasim model that should be coupled.
    mf6_simulation : Modflow6Simulation
        The Modflow6 simulation that should be coupled.
    coupling_list: list of DriverCoupling
        One entry per MODFLOW 6 model that should be coupled
    """

    _toml_name = "imod_coupler.toml"
    _ribasim_model_dir = "ribasim"
    _modflow6_model_dir = "modflow6"

    def __init__(
        self,
        ribasim_model: ribasim.Model,
        mf6_simulation: Modflow6Simulation,
        coupling_list: list[RibaModDriverCoupling],
    ):
        _validate_time_window(
            ribasim_model=ribasim_model,
            mf6_simulation=mf6_simulation,
        )
        self.ribasim_model = ribasim_model
        self.mf6_simulation = mf6_simulation
        self.coupling_list = coupling_list

    def write(
        self,
        directory: str | Path,
        modflow6_dll: str | Path,
        ribasim_dll: str | Path,
        ribasim_dll_dependency: str | Path,
        modflow6_write_kwargs: dict[str, Any] | None = None,
    ) -> None:
        """
        Write Ribasim and Modflow 6 model with exchange files, as well as a
        ``.toml`` file which configures the iMOD Coupler run.

        Parameters
        ----------
        directory: str or Path
            Directory in which to write the coupled models
        modflow6_dll: str or Path
            Path to modflow6 .dll. You can obtain this library by downloading
            `the last iMOD5 release
            <https://oss.deltares.nl/web/imod/download-imod5>`_
        ribasim_dll: str or Path
            Path to ribasim .dll.
        ribasim_dll_dependency: str or Path
            Directory with ribasim .dll dependencies.
        modflow6_write_kwargs: dict
            Optional dictionary with keyword arguments for the writing of
            Modflow6 models. You can use this for example to turn off the
            validation at writing (``validation=False``) or to write text files
            (``binary=False``)
        """

        if modflow6_write_kwargs is None:
            modflow6_write_kwargs = {}

        # force to Path
        directory = Path(directory)
        coupling_dict = self.write_exchanges(directory)

        self.mf6_simulation.write(
            directory / self._modflow6_model_dir,
            **modflow6_write_kwargs,
        )
        self.ribasim_model.write(directory / self._ribasim_model_dir / "ribasim.toml")
        self.write_toml(
            directory,
            coupling_dict,
            modflow6_dll,
            ribasim_dll,
            ribasim_dll_dependency,
        )

    def write_toml(
        self,
        directory: str | Path,
        coupling_dict: dict[str, Any],
        modflow6_dll: str | Path,
        ribasim_dll: str | Path,
        ribasim_dll_dependency: str | Path,
    ) -> None:
        """
        Write .toml file which configures the imod coupler run.

        Parameters
        ----------
        directory: str or Path
            Directory in which to write the .toml file.
        modflow6_dll: str or Path
            Path to modflow6 .dll. You can obtain this library by downloading
            `the last iMOD5 release
            <https://oss.deltares.nl/web/imod/download-imod5>`_
        ribasim_dll: str or Path
            Path to ribasim .dll.
        ribasim_dll_dependency: str or Path
            Directory with ribasim .dll dependencies.
        """
        # force to Path
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)

        toml_path = directory / self._toml_name
        coupler_toml = {
            "timing": False,
            "log_level": "INFO",
            "driver_type": "ribamod",
            "driver": {
                "kernels": {
                    "modflow6": {
                        "dll": str(modflow6_dll),
                        "work_dir": self._modflow6_model_dir,
                    },
                    "ribasim": {
                        "dll": str(ribasim_dll),
                        "dll_dep_dir": str(ribasim_dll_dependency),
                        "config_file": str(
                            Path(self._ribasim_model_dir) / "ribasim.toml"
                        ),
                    },
                },
                "coupling": [coupling_dict],
            },
        }

        with open(toml_path, "wb") as f:
            tomli_w.dump(coupler_toml, f)
