"""Unit test for :func:`esmvalcore.preprocessor._multimodel`"""

from datetime import datetime

import iris
import numpy as np
import pytest
from cf_units import Unit
from iris.cube import Cube

import esmvalcore.preprocessor._multimodel as mm
from esmvalcore.preprocessor import multi_model_statistics

SPAN_OPTIONS = ('overlap', 'full')

FREQUENCY_OPTIONS = ('daily', 'monthly', 'yearly')  # hourly


def assert_array_almost_equal(this, other):
    """Assert that array `this` almost equals array `other`."""
    if np.ma.isMaskedArray(this) or np.ma.isMaskedArray(other):
        np.testing.assert_array_equal(this.mask, other.mask)

    np.testing.assert_array_almost_equal(this, other)


def timecoord(frequency,
              calendar='gregorian',
              offset='days since 1850-01-01',
              num=3):
    """Return a time coordinate with the given time points and calendar."""

    time_points = range(1, num + 1)

    if frequency == 'hourly':
        dates = [datetime(1850, 1, 1, i, 0, 0) for i in time_points]
    if frequency == 'daily':
        dates = [datetime(1850, 1, i, 0, 0, 0) for i in time_points]
    elif frequency == 'monthly':
        dates = [datetime(1850, i, 15, 0, 0, 0) for i in time_points]
    elif frequency == 'yearly':
        dates = [datetime(1850, 7, i, 0, 0, 0) for i in time_points]

    unit = Unit(offset, calendar=calendar)
    points = unit.date2num(dates)
    return iris.coords.DimCoord(points, standard_name='time', units=unit)


def get_cubes(frequency):
    """Set up cubes used for testing multimodel statistics."""

    # Simple 1d cube with standard time cord
    time = timecoord(frequency)
    cube1 = Cube([1, 1, 1], dim_coords_and_dims=[(time, 0)])

    # Cube with masked data
    cube2 = cube1.copy()
    cube2.data = np.ma.array([5, 5, 5], mask=[True, False, False])

    # Cube with deviating time coord
    time = timecoord(frequency,
                     calendar='360_day',
                     offset='days since 1950-01-01')[:2]
    cube3 = Cube([9, 9], dim_coords_and_dims=[(time, 0)])
    return [cube1, cube2, cube3]


VALIDATION_DATA_SUCCESS = (
    ('full', 'mean', (5, 5, 3)),
    ('full', 'std', (5.656854249492381, 4, 2.8284271247461903)),
    ('full', 'std_dev', (5.656854249492381, 4, 2.8284271247461903)),
    ('full', 'min', (1, 1, 1)),
    ('full', 'max', (9, 9, 5)),
    ('full', 'median', (5, 5, 3)),
    ('full', 'p50', (5, 5, 3)),
    ('full', 'p99.5', (8.96, 8.96, 4.98)),
    ('overlap', 'mean', (5, 5)),
    ('overlap', 'std', (5.656854249492381, 4)),
    ('overlap', 'std_dev', (5.656854249492381, 4)),
    ('overlap', 'min', (1, 1)),
    ('overlap', 'max', (9, 9)),
    ('overlap', 'median', (5, 5)),
    ('overlap', 'p50', (5, 5)),
    ('overlap', 'p99.5', (8.96, 8.96)),
    # test multiple statistics
    ('overlap', ('min', 'max'), ((1, 1), (9, 9))),
    ('full', ('min', 'max'), ((1, 1, 1), (9, 9, 5))),
)


@pytest.mark.parametrize('frequency', FREQUENCY_OPTIONS)
@pytest.mark.parametrize('span, statistics, expected', VALIDATION_DATA_SUCCESS)
def test_multimodel_statistics(frequency, span, statistics, expected):
    """High level test for multicube statistics function.

    - Should work for multiple data frequencies
    - Should be able to deal with multiple statistics
    - Should work for both span arguments
    - Should deal correctly with different mask options
    - Return type should be a dict with all requested statistics as keys
    """
    cubes = get_cubes(frequency)

    if isinstance(statistics, str):
        statistics = (statistics, )
        expected = (expected, )

    result = multi_model_statistics(cubes, span, statistics)

    assert isinstance(result, dict)
    assert set(result.keys()) == set(statistics)

    for i, statistic in enumerate(statistics):
        result_cube = result[statistic]
        expected_data = np.ma.array(expected[i], mask=False)
        assert_array_almost_equal(result_cube.data, expected_data)


VALIDATION_DATA_FAIL = (
    ('percentile', ValueError),
    ('wpercentile', ValueError),
    ('count', TypeError),
    ('peak', TypeError),
    ('proportion', TypeError),
)


@pytest.mark.parametrize('statistic, error', VALIDATION_DATA_FAIL)
def test_unsupported_statistics_fail(statistic, error):
    """Check that unsupported statistics raise an exception."""
    cubes = get_cubes('monthly')
    span = 'overlap'
    statistics = (statistic, )
    with pytest.raises(error):
        _ = multi_model_statistics(cubes, span, statistics)


def test_get_consistent_time_unit():
    """Test same calendar returned or default if calendars differ."""
    time1 = timecoord('monthly', '360_day')
    cube1 = Cube([1, 1, 1], dim_coords_and_dims=[(time1, 0)])
    time2 = timecoord('monthly', '365_day')
    cube2 = Cube([1, 1, 1], dim_coords_and_dims=[(time2, 0)])

    result1 = mm._get_consistent_time_unit([cube1, cube1])
    result2 = mm._get_consistent_time_unit([cube1, cube2])
    assert result1.calendar == '360_day'
    assert result2.calendar == 'gregorian'


def test_unify_time_coordinates():
    """Test whether the time coordinates are made consistent."""

    # # Check that monthly data have midpoints at 15th day
    # cube1 = Cube([1, 1, 1], )

    # hourly = {
    #     'input1': timecoord([datetime(1850, 1, 1, i, 0, 0) for i in [1, 2, 3]],
    #               calendar='standard'),
    #     'input2' timecoord([datetime(1850, 1, 1, i, 0, 0) for i in [1, 2, 3]]),
    #               calendar='gregorian'),
    #     'output': timecoord([datetime(1850, 1, 1, i, 0, 0) for i in [1, 2, 3]],
    #               calendar='gregorian')
    # }

    # daily = ([datetime(1850, 1, i, 0, 0, 0) for i in [1, 2, 3]],
    #          [datetime(1850, 1, i, 12, 0, 0) for i in [1, 2, 3]])
    # monthly = ([datetime(1850, i, 1, 0, 0, 0) for i in [1, 2, 3]],
    #            [datetime(1850, i, 15, 0, 0, 0) for i in [1, 2, 3]])
    # yearly = ([datetime(1850+i, 1, 7, 0, 0, 0) for i in [1, 2, 3]],
    #           [datetime(1850+i, 1, 1, 0, 0, 0) for i in [1, 2, 3]])

    # time_sets = [hourly, daily, monthly, yearly]
    # calendars_sets = [
    #     ('standard', 'gregorian'),
    #     ('360_day', '360_day'),
    #     ('365_day', 'proleptic_gregorian'),
    #     ('standard', 'standard'),
    # ]

    # for (time1, time2), (calendar1, calendar2) in zip(time_sets, calendar_sets):
    #     cube1 = [Cube([1, 1, 1], dim_coords_and_dims=[(timecoord(time1, calendar1), 0)])
    #     cube2 = [Cube([1, 1, 1], dim_coords_and_dims=[(timecoord(time2, calendar2), 0)])
    #     cubes = mm._unify_time_coordinates([cube1, cube2])

    # --> pass multiple cubes with all kinds of different calendars
    #     - Check that output cubes all have the same calendar
    #     - check that the dates in the output correspond to the dates in the input
    #     - do this for different time frequencies
    #     - check warning/error for (sub)daily data


def test_resolve_span():
    """Check that resolve_span returns the correct union/intersection."""
    span1 = [1, 2, 3]
    span2 = [2, 3, 4]
    span3 = [3, 4, 5]
    span4 = [4, 5, 6]

    assert all(mm._resolve_span([span1, span2], span='overlap') == [2, 3])
    assert all(mm._resolve_span([span1, span2], span='full') == [1, 2, 3, 4])

    assert all(mm._resolve_span([span1, span2, span3], span='overlap') == [3])
    assert all(
        mm._resolve_span([span1, span2, span3], span='full') ==
        [1, 2, 3, 4, 5])

    with pytest.raises(ValueError):
        mm._resolve_span([span1, span4], span='overlap')


@pytest.mark.parametrize('span', SPAN_OPTIONS)
def test_align(span):
    """Test _align function."""

    # TODO --> check that if a cube is extended,
    #          the extended points are masked (not NaN!)

    test_calendars = ('360_day', '365_day', 'gregorian', 'proleptic_gregorian',
                      'julian')
    data = [1, 1, 1]
    cubes = []

    for calendar in test_calendars:
        time_coord = timecoord('monthly', '360_day')
        cube = Cube(data, dim_coords_and_dims=[(time_coord, 0)])
        cubes.append(cube)

    result_cubes = mm._align(cubes, span)

    calendars = set(cube.coord('time').units.calendar for cube in result_cubes)

    assert len(calendars) == 1

    shapes = set(cube.shape for cube in result_cubes)

    assert len(shapes) == 1
    assert tuple(shapes)[0] == (len(data), )


@pytest.mark.parametrize('span', SPAN_OPTIONS)
def test_combine_same_shape(span):
    """Test _combine with same shape of cubes."""
    len_data = 3
    num_cubes = 5
    test_dim = 'test_dim'
    cubes = []
    time_coord = timecoord('monthly', '360_day')

    for i in range(num_cubes):
        cube = Cube([i] * len_data, dim_coords_and_dims=[(time_coord, 0)])
        cubes.append(cube)

    result_cube = mm._combine(cubes, dim=test_dim)

    dim_coord = result_cube.coord(test_dim)
    assert dim_coord.var_name == test_dim
    assert result_cube.shape == (num_cubes, len_data)

    desired = np.linspace((0, ) * len_data,
                          num_cubes - 1,
                          num=num_cubes,
                          dtype=int)
    np.testing.assert_equal(result_cube.data, desired)


def test_combine_different_shape_fail():
    """Test _combine with inconsistent data."""
    num_cubes = 5
    test_dim = 'test_dim'
    cubes = []

    for num in range(1, num_cubes + 1):
        time_coord = timecoord('monthly', '360_day', num=num)
        cube = Cube([1] * num, dim_coords_and_dims=[(time_coord, 0)])
        cubes.append(cube)

    with pytest.raises(iris.exceptions.MergeError):
        _ = mm._combine(cubes, dim=test_dim)


def test_combine_inconsistent_var_names_fail():
    """Test _combine with inconsistent var names."""
    num_cubes = 5
    test_dim = 'test_dim'
    data = [1, 1, 1]
    cubes = []

    for num in range(num_cubes):
        time_coord = timecoord('monthly', '360_day')
        cube = Cube(data,
                    dim_coords_and_dims=[(time_coord, 0)],
                    var_name=f'test_var_{num}')
        cubes.append(cube)

    with pytest.raises(iris.exceptions.MergeError):
        _ = mm._combine(cubes, dim=test_dim)


@pytest.mark.parametrize('span', SPAN_OPTIONS)
def test_edge_case_different_time_offsets(span):
    time1 = timecoord('monthly', '360_day', offset='days since 1888-01-01')
    cube1 = Cube([1, 1, 1], dim_coords_and_dims=[(time1, 0)])
    time2 = timecoord('monthly', '360_day', offset='days since 1899-01-01')
    cube2 = Cube([1, 1, 1], dim_coords_and_dims=[(time2, 0)])

    cubes = (cube1, cube2)
    statistic = 'min'
    statistics = (statistic, )

    result = multi_model_statistics(cubes, span, statistics)

    result_cube = result[statistic]

    time_coord = result_cube.coord('time')

    assert time_coord.units.calendar == 'gregorian'
    assert time_coord.units.origin == 'days since 1850-01-01'

    desired = np.array((14., 45., 73.))
    np.testing.assert_array_equal(time_coord.points, desired)

    # old coords are updated in-place
    np.testing.assert_array_equal(time1.points, desired)
    np.testing.assert_array_equal(time2.points, desired)


def generate_cube_from_dates(dates):
    """Generate cube from list of dates."""
    unit = Unit('days since 1850-01-01', calendar='gregorian')

    time = iris.coords.DimCoord(unit.date2num(dates),
                                standard_name='time',
                                units=unit)

    return Cube([1, 1, 1], dim_coords_and_dims=[(time, 0)])


def generate_cubes_with_non_overlapping_timecoords():
    """Generate sample data where time coords do not overlap."""
    time_points = range(1, 4)
    dates1 = [datetime(1850, i, 15, 0, 0, 0) for i in time_points]
    dates2 = [datetime(1950, i, 15, 0, 0, 0) for i in time_points]

    return (
        generate_cube_from_dates(dates1),
        generate_cube_from_dates(dates2),
    )


def test_edge_case_time_no_overlap_fail():
    """Test case when time coords do not overlap using span='overlap'.

    Expected behaviour: `multi_model_statistics` should fail if time
    points are not overlapping.
    """
    cubes = generate_cubes_with_non_overlapping_timecoords()

    statistic = 'min'
    statistics = (statistic, )

    with pytest.raises(ValueError):
        _ = multi_model_statistics(cubes, 'overlap', statistics)


def test_edge_case_time_no_overlap_success():
    """Test case when time coords do not overlap using span='full'.

    Expected behaviour: `multi_model_statistics` should use all
    available time points.
    """
    cubes = generate_cubes_with_non_overlapping_timecoords()

    statistic = 'min'
    statistics = (statistic, )

    result = multi_model_statistics(cubes, 'full', statistics)
    result_cube = result[statistic]

    assert result_cube.coord('time').shape == (6, )


def generate_cubes_with_time_not_in_middle_of_month():
    """Generate sample data where time coords do not overlap."""
    time_points = range(1, 4)
    dates1 = [datetime(1850, i, 12, 0, 0, 0) for i in time_points]
    dates2 = [datetime(1850, i, 25, 0, 0, 0) for i in time_points]

    return (
        generate_cube_from_dates(dates1),
        generate_cube_from_dates(dates2),
    )


@pytest.mark.parametrize('span', SPAN_OPTIONS)
def test_edge_case_time_not_in_middle_of_months(span):
    """Test case when time coords are not on 15th for monthly data.

    Expected behaviour: `multi_model_statistics` will set all dates to
    the 15th.
    """
    cubes = generate_cubes_with_time_not_in_middle_of_month()

    statistic = 'min'
    statistics = (statistic, )

    result = multi_model_statistics(cubes, span, statistics)
    result_cube = result[statistic]

    time_coord = result_cube.coord('time')

    desired = np.array((14., 45., 73.))
    np.testing.assert_array_equal(time_coord.points, desired)

    # input cubes are updated in-place
    for cube in cubes:
        np.testing.assert_array_equal(cube.coord('time').points, desired)


@pytest.mark.parametrize('span', SPAN_OPTIONS)
def test_edge_case_sub_daily_data_fail(span):
    """Test case when cubes with sub-daily time coords are passed."""
    time_points = range(1, 4)
    dates = [datetime(1850, 1, 1, i, 0, 0) for i in time_points]

    cube = generate_cube_from_dates(dates)
    cubes = (cube, cube)

    statistic = 'min'
    statistics = (statistic, )

    with pytest.raises(ValueError):
        _ = multi_model_statistics(cubes, span, statistics)
