"""Fixes for CMIP6 MIROC-ES2L."""
from ..fix import Fix
from ..common import ClFixHybridPressureCoord


Cl = ClFixHybridPressureCoord


Cli = ClFixHybridPressureCoord


Clw = ClFixHybridPressureCoord

class Fgco2(Fix):
    """Fixes for fgco2."""

    def fix_data(self, cube):
        """
        Fix data.

        Reported in kg of CO2 rather than kg of carbon.

        Parameters
        ----------
        cube: iris.cube.Cube

        Returns
        -------
        iris.cube.Cube

        """
        metadata = cube.metadata
        cube *= 12./44.
        cube.metadata = metadata
        return cube
