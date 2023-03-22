import shutil
from pathlib import Path

import tomli
import tomli_w
from test_scripts.water_balance.combine import create_waterbalance_file
from test_utilities import fill_para_sim_template, numeric_csvfiles_equal

from imod_coupler.__main__ import run_coupler


def test_run_tmodel(
    tmp_path_dev: Path,
    tmodel_input_folder: Path,
    modflow_dll_devel: Path,
    dflowfm_dll: Path,
    metaswap_dll_devel: Path,
    metaswap_dll_dep_dir_devel: Path,
    metaswap_lookup_table: Path,
    reference_result_folder: Path,
) -> None:
    shutil.copytree(tmodel_input_folder, tmp_path_dev)

    toml_file_path = tmp_path_dev / "imod_coupler.toml"
    toml_dict = {}
    with open(toml_file_path, "rb") as f:
        toml_dict = tomli.load(f)

    toml_dict["driver"]["kernels"]["modflow6"]["dll"] = str(modflow_dll_devel)
    toml_dict["driver"]["kernels"]["dflowfm"]["dll"] = str(dflowfm_dll)
    toml_dict["driver"]["kernels"]["metaswap"]["dll"] = str(metaswap_dll_devel)
    toml_dict["driver"]["kernels"]["metaswap"]["dll_dep_dir"] = str(
        metaswap_dll_dep_dir_devel
    )
    with open(toml_file_path, "wb") as toml_file:
        tomli_w.dump(toml_dict, toml_file)

    fill_para_sim_template(tmp_path_dev / "MetaSWAP", metaswap_lookup_table)

    run_coupler(toml_file_path)

    waterbalance_result = run_waterbalance_script_on_tmodel(tmp_path_dev)

    csv_reference_file = (
        reference_result_folder / "test_run_tmodel" / "waterbalance.csv"
    )

    assert numeric_csvfiles_equal(
        waterbalance_result, csv_reference_file, ";", abstol=5600.0, reltol=3.5
    )


def test_run_tmodel_no_2d(
    tmp_path_dev: Path,
    tmodel_input_folder: Path,
    modflow_dll_devel: Path,
    dflowfm_dll: Path,
    metaswap_dll_devel: Path,
    metaswap_dll_dep_dir_devel: Path,
    metaswap_lookup_table: Path,
    reference_result_folder: Path,
) -> None:
    shutil.copytree(tmodel_input_folder, tmp_path_dev)

    toml_file_path = tmp_path_dev / "imod_coupler.toml"
    toml_dict = {}
    with open(toml_file_path, "rb") as f:
        toml_dict = tomli.load(f)

    toml_dict["driver"]["kernels"]["modflow6"]["dll"] = str(modflow_dll_devel)
    toml_dict["driver"]["kernels"]["dflowfm"]["dll"] = str(dflowfm_dll)
    toml_dict["driver"]["kernels"]["metaswap"]["dll"] = str(metaswap_dll_devel)
    toml_dict["driver"]["kernels"]["metaswap"]["dll_dep_dir"] = str(
        metaswap_dll_dep_dir_devel
    )
    toml_dict["driver"]["coupling"][0].pop("msw_ponding_to_dfm_2d_dv_dmm", None)
    toml_dict["driver"]["coupling"][0].pop("dfm_2d_waterlevels_to_msw_h_dmm", None)
    toml_dict["driver"]["coupling"][0].pop("msw_sprinkling_to_dfm_1d_q_dmm", None)
    toml_dict["driver"]["coupling"][0].pop("msw_runoff_to_dfm_1d_q_dmm", None)

    toml_dict["driver"]["coupling"][0].pop("mf6_drainage_to_dfm_1d_q_dmm", None)
    toml_dict["driver"]["coupling"][0].pop("mf6_river2_to_dmf_1d_q_dmm", None)
    toml_dict["driver"]["coupling"][0].pop("mf6_river_to_dfm_1d_q_dmm", None)
    toml_dict["driver"]["coupling"][0].pop(
        "dfm_1d_waterlevel_to_mf6_river_stage_dmm", None
    )

    with open(toml_file_path, "wb") as toml_file:
        tomli_w.dump(toml_dict, toml_file)

    fill_para_sim_template(tmp_path_dev / "MetaSWAP", metaswap_lookup_table)

    run_coupler(toml_file_path)


def run_waterbalance_script_on_tmodel(testdir: Path) -> Path:
    modflow_out_file = testdir / "Modflow6" / "GWF_1" / "T-MODEL-D.LST"
    dflow_out_file = testdir / "dflow-fm" / "DFM_OUTPUT_FlowFM" / "FlowFM_his.nc"
    metaswap_out_file = testdir / "MetaSWAP" / "msw" / "csv" / "tot_svat_dtgw.csv"

    csv_file = testdir / "water_balance.csv"
    create_waterbalance_file(
        dflow_out_file, metaswap_out_file, modflow_out_file, output_file_csv=csv_file
    )
    return csv_file
