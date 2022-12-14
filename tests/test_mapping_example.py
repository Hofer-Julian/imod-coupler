#%%
from math import isclose
from pathlib import Path

import numpy as np
from numpy import float_
from numpy.typing import NDArray

from imod_coupler.drivers.dfm_metamod.mapping_functions import (
    calc_correction_dfm2mf,
    get_dflow1d_lookup,
    map_values_reweighted,
    mapping_active_mf_dflow1d,
    weight_from_flux_distribution,
)
from imod_coupler.utils import Operator, create_mapping


def test_mappers_general(
    dflow1d_mapping_file,
    mapping_file_mf6_river_to_dfm_1d_q,
    mapping_file_dfm_1d_waterlevel_to_mf6_river_stage,
) -> None:

    # Test exchange MF-DFLOW1D
    # create dummy arrays to exchange

    # mf riv1-flux to exchange
    mf_riv1_flux = np.array([3, 3, 4, 4, 4])
    # dflow1d flux and stage to exchange
    dflow1d_flux = np.array([6, 7, 8])
    dflow1d_stage = np.array([4, 5, 6])

    # get dflow-id based on xy-coordinates after initialisation (now as test from file)
    dflow1d_lookup = get_dflow1d_lookup(dflow1d_mapping_file)

    # create mapping for mf-dflow1d
    # there is no previous flux geven for weight distributed weights,
    # so DFLOW 1D stage -> MF RIV 1 exchange is not availble at this time
    map_active_mod_dflow1d, mask_active_mod_dflow1d = mapping_active_mf_dflow1d(
        mapping_file_mf6_river_to_dfm_1d_q,
        mapping_file_dfm_1d_waterlevel_to_mf6_river_stage,
        dflow1d_lookup,
    )

    # exchange in order of actual coupling

    # DFLOW 1D stage -> MF RIV 1 stage
    # weighted averaging based on input files:
    # dflow1d_nodes=((5,5),(25,15),(45,25))
    # riv-id  fm-x    fm-y   weight    dflow-stage
    #   1     5       5      0.9       4
    #   1     25      15     0.1       5
    #   2     5       5      0.450     4
    #   2     25      15     0.550     5
    #   3     5       5      0.950     4
    #   3     25      15     0.050     5
    #   4     25      15     0.40      5
    #   4     45      25     0.60      6
    #   5     25      15     0.1       5
    #   5     45      25     0.9       6

    mf_riv1_stage_receive_expected = np.array(
        [
            (0.9 * 4) + (0.1 * 5),
            (0.45 * 4) + (0.55 * 5),
            (0.95 * 4) + (0.05 * 5),
            (0.4 * 5) + (0.6 * 6),
            (0.1 * 5) + (0.9 * 6),
        ]
    )
    mf_riv1_stage_receive = np.array([0, 0, 0, 0, 0])
    mf_riv1_stage_receive = (
        mask_active_mod_dflow1d["dflow1d2mf-riv_stage"][:] * mf_riv1_stage_receive[:]
        + map_active_mod_dflow1d["dflow1d2mf-riv_stage"].dot(dflow1d_stage)[:]
    )
    np.testing.assert_allclose(
        mf_riv1_stage_receive_expected,
        mf_riv1_stage_receive,
        rtol=0.001,
        atol=0.0,
    )

    # MF RIV 1 -> DFLOW 1D flux
    # flux is always n:1, so values are summed
    dflow1d_flux_receive_expected = np.array([3 + 3, 4, 4 + 4])
    dflow1d_flux_receive = np.array([0, 0, 0])
    dflow1d_flux_receive = (
        mask_active_mod_dflow1d["mf-riv2dflow1d_flux"][:] * dflow1d_flux_receive[:]
        + map_active_mod_dflow1d["mf-riv2dflow1d_flux"].dot(mf_riv1_flux)[:]
    )
    np.testing.assert_allclose(
        dflow1d_flux_receive_expected, dflow1d_flux_receive, rtol=0.001, atol=0.0
    )

    # DFLOW 1D flux -> MF RIV 1 flux
    # flux is always 1:n, decomposition based on previous Mf -> DFLOW flux distribution

    # create new mapping based on  previous MF -> dflow flux exchange distribution
    # for now, all mappingfiles are read in again, this could be optimised in the future
    map_active_mod_dflow1d, mask_active_mod_dflow1d = mapping_active_mf_dflow1d(
        mapping_file_mf6_river_to_dfm_1d_q,
        mapping_file_dfm_1d_waterlevel_to_mf6_river_stage,
        dflow1d_lookup,
        mf_riv1_flux,
    )
    # expected results
    weights = np.array([3 / 6, 3 / 6, 1, 4 / 8, 4 / 8])
    mf_riv1_flux_receive_expected = np.array(
        [6 * weights[0], 6 * weights[1], 7 * weights[2], 8 * weights[3], 8 * weights[0]]
    )
    mf_riv1_flux_receive = np.array([0, 0, 0, 0, 0])
    mf_riv1_flux_receive = (
        mask_active_mod_dflow1d["dflow1d2mf-riv_flux"][:] * mf_riv1_flux_receive[:]
        + map_active_mod_dflow1d["dflow1d2mf-riv_flux"].dot(dflow1d_flux)[:]
    )
    np.testing.assert_allclose(
        mf_riv1_flux_receive_expected, mf_riv1_flux_receive, rtol=0.001, atol=0.0
    )


def test_weight_from_flux_distribution() -> None:
    # test calculated weights based on flux exchange
    # mf-riv1 elements=5
    # dfow1d  elements=3

    # set dummy variables
    # previous flux from MF-RIV1 to DFLOW1d
    dummy_flux_mf2dflow1d = np.array([1, 2, 3, 4, 5])
    # set connection sparse array for DFLOW1d --> MF
    target_index = np.array([0, 0, 1, 1, 2])
    source_index = np.array([0, 1, 2, 3, 4])

    # evaluate weight distribution
    expected_weight = np.array([1 / 3, 2 / 3, 3 / 7, 4 / 7, 1])
    calculated_weight = weight_from_flux_distribution(
        target_index, source_index, dummy_flux_mf2dflow1d
    )
    np.testing.assert_almost_equal(expected_weight, calculated_weight)


def test_calc_correction_dfm2mf() -> None:
    # test calculated mapped values based on mapping and re-weighting
    # with the estimated fluxes
    # mf-riv1 elements=5
    # dfow1d  elements=3

    # set dummy variables
    # previous flux from MF-RIV1 to DFLOW1d, used for reweighting
    q_demand_mf6 = np.array([1, 2, 3, 4, 5])

    # set connection sparse array for DFLOW1d --> MF
    dfm_index = np.array([0, 0, 1, 1, 2])
    mf6_index = np.array([0, 1, 2, 3, 4])

    mf6_to_dfm = create_mapping(mf6_index, dfm_index, 5, 3, Operator.SUM)
    #   q_realized_dfm = (1.1, 0.7, 0.2) * q_demand_dfm  # test corner cases
    q_demand_dfm = mf6_to_dfm[0].dot(q_demand_mf6)  # same as other test

    q_realized_dfm = q_demand_dfm - (34, 73, 666)
    target_values = calc_correction_dfm2mf(
        mf6_to_dfm[0], q_demand_mf6, q_demand_dfm, q_realized_dfm
    )

    # evaluate weight distribution
    expected_target_values = np.array(
        [34 * 1.0 / 3.0, 34 * 2.0 / 3.0, 73 * 3.0 / 7.0, 73 * 4.0 / 7.0, 666.0]
    )
    np.testing.assert_almost_equal(expected_target_values, target_values)


def test_mapping_from_flux_distribution() -> None:
    # test calculated mapped values based on mapping and re-weighting
    # with the estimated fluxes
    # mf-riv1 elements=5
    # dfow1d  elements=3

    # set dummy variables
    # previous flux from MF-RIV1 to DFLOW1d, used for reweighting
    dummy_flux_mf2dflow1d = np.array([1, 2, 3, 4, 5])
    source_values = np.array([34, 73, 666])
    # set connection sparse array for DFLOW1d --> MF
    source_index = np.array([0, 0, 1, 1, 2])
    target_index = np.array([0, 1, 2, 3, 4])

    mapping = create_mapping(source_index, target_index, 3, 5, Operator.SUM)
    target_values = map_values_reweighted(
        mapping[0], source_values, dummy_flux_mf2dflow1d
    )

    # evaluate weight distribution
    expected_target_values = np.array(
        [34 * 1.0 / 3.0, 34 * 2.0 / 3.0, 73 * 3.0 / 7.0, 73 * 4.0 / 7.0, 666.0]
    )
    np.testing.assert_almost_equal(expected_target_values, target_values)
