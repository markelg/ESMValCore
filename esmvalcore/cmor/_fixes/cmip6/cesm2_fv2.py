"""Fixes for CESM2-FV2 model."""
from .cesm2 import Cl as BaseCl
from .cesm2 import Tas as BaseTas
from ..fix import Fix
from ..shared import (add_scalar_depth_coord, add_scalar_height_coord,
                      add_scalar_typeland_coord, add_scalar_typesea_coord)

Cl = BaseCl


Cli = Cl


Clw = Cl


Tas = BaseTas

class Fgco2(Fix):
    """Fixes for fgco2."""

    def fix_metadata(self, cubes):
        """Add depth (0m) coordinate.

        Parameters
        ----------
        cubes : iris.cube.CubeList
            Input cubes.

        Returns
        -------
        iris.cube.CubeList

        """
        cube = self.get_cube_from_list(cubes)
        add_scalar_depth_coord(cube)
        return cubes
