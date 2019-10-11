"""Derivation of variable `wue`."""

import iris
from ._baseclass import DerivedVariableBase


class DerivedVariable(DerivedVariableBase):
    """Derivation of variable `wue` (Water Use Efficiency)."""

    # Required variables
    required = [{'short_name': 'gpp',
                 'short_name': 'evspsblsoi',
                 'short_name': 'evspsblpot', }]

    # et = evapotranspiration
    # gpp = gross primary production
    # evspsblsoi = Water evaporation from soil (including sublimation).")
    # evspsblpot = Canopy evaporation and sublimation
    @staticmethod
    def calculate(cubes):
        """Compute Water Use Efficiency.
        """
        gpp_cube = cubes.extract_strict(
            iris.Constraint(short_name='gpp'))
        et_cube = cubes.extract_strict(
            iris.Constraint(short_name='evspsblsoi'))
        et_cube = cubes.extract_strict(
            iris.Constraint(short_name='evspsblpot'))

        return et_cube/gpp_cube