import geopandas as gpd
import numpy as np
import pandas as pd
import ribasim
import ribasim.geometry
import xarray as xr
from fixtures.common import create_wells_max_layer
from imod import msw
from imod.mf6 import Modflow6Simulation, Recharge, StorageCoefficient
from imod.msw import MetaSwapModel
from primod import (
    MetaModDriverCoupling,
    RibaMetaDriverCoupling,
    RibaMetaMod,
    RibaModActiveDriverCoupling,
)
from ribasim.geometry import NodeTable as RibaNodeTbl
from ribasim.nodes import level_demand, user_demand
from shapely.geometry import Point
from test_ribamod_cases import (
    get_mf6_drainage_packagenames,
    get_mf6_gwf_modelnames,
    get_mf6_river_packagenames,
)


def create_basin_definition(
    node: RibaNodeTbl,
    buffersize: float,
    yoff: float = 0.0,
    xoff: float = 0.0,
    **kwargs,
) -> gpd.GeoDataFrame:
    # Call to_numpy() to get rid of the index
    nodelist: list[int]
    if "nodes" in kwargs:
        nodelist = kwargs["nodes"]
    else:
        nodelist = list(node.df["node_id"])
    sel = node.df["node_id"].isin(nodelist)
    basin_definition = gpd.GeoDataFrame(
        data={"node_id": node.df.loc[sel]["node_id"].to_numpy()},
        geometry=node.df[sel]["geometry"]
        .translate(yoff=yoff, xoff=xoff)
        .buffer(buffersize)
        .to_numpy(),
    )
    return basin_definition


def add_rch_package(
    mf6_model: Modflow6Simulation,
) -> Modflow6Simulation:
    """
    adds recharge package to MODFLOW6 model for coupling with MetaSWAP
    """
    idomain = mf6_model["GWF_1"]["dis"]["idomain"]
    recharge = xr.zeros_like(idomain.sel(layer=1), dtype=float)
    recharge = recharge.where(idomain.sel(layer=1))
    mf6_model["GWF_1"]["rch_msw"] = Recharge(rate=recharge)
    return mf6_model


def add_well_package(
    mf6_model: Modflow6Simulation,
) -> Modflow6Simulation:
    idomain = mf6_model["GWF_1"]["dis"]["idomain"]
    _, nrow, ncol = idomain.shape
    mf6_model["GWF_1"]["well_msw"] = create_wells_max_layer(nrow, ncol, idomain)
    return mf6_model


def case_bucket_model(
    mf6_bucket_model: Modflow6Simulation,
    msw_bucket_model: MetaSwapModel,
    ribasim_bucket_model: ribasim.Model,
) -> RibaMetaMod:
    mf6_modelname, mf6_model = get_mf6_gwf_modelnames(mf6_bucket_model)[0]
    mf6_active_river_packages = get_mf6_river_packagenames(mf6_model)
    basin_definition = create_basin_definition(
        ribasim_bucket_model.basin.node, buffersize=100.0
    )
    mf6_bucket_model = add_rch_package(mf6_bucket_model)
    mf6_bucket_model = add_well_package(mf6_bucket_model)

    metamod_coupling = MetaModDriverCoupling(
        mf6_model=mf6_modelname,
        mf6_recharge_package="rch_msw",
        mf6_wel_package="well_msw",
    )
    ribamod_coupling = RibaModActiveDriverCoupling(
        mf6_model=mf6_modelname,
        mf6_packages=mf6_active_river_packages,
        ribasim_basin_definition=basin_definition,
    )
    ribameta_coupling = RibaMetaDriverCoupling(
        ribasim_basin_definition=basin_definition,
    )
    # increase resistance to 1 day
    conductance = mf6_bucket_model["GWF_1"][mf6_active_river_packages[0]].dataset[
        "conductance"
    ]
    conductance = conductance / 400
    mf6_bucket_model["GWF_1"][mf6_active_river_packages[0]].dataset["conductance"] = (
        conductance
    )
    mf6_bucket_model["GWF_1"].pop("sto")
    idomain = mf6_bucket_model["GWF_1"]["dis"]["idomain"]
    ss = xr.ones_like(idomain) * 1e-6
    ss[0, :, :] = 0.15  # phreatic layer, importent for non coupled nodes
    mf6_bucket_model["GWF_1"]["sto"] = StorageCoefficient(ss, 0.1, True, 0)

    return RibaMetaMod(
        ribasim_model=ribasim_bucket_model,
        msw_model=msw_bucket_model,
        mf6_simulation=mf6_bucket_model,
        coupling_list=[metamod_coupling, ribamod_coupling, ribameta_coupling],
    )


def case_backwater_model(
    mf6_backwater_model: Modflow6Simulation,
    msw_backwater_model: MetaSwapModel,
    ribasim_backwater_model: ribasim.Model,
) -> RibaMetaMod:
    mf6_modelname, mf6_model = get_mf6_gwf_modelnames(mf6_backwater_model)[0]
    mf6_active_river_packages = get_mf6_river_packagenames(mf6_model)
    mf6_active_drainage_packages = get_mf6_drainage_packagenames(mf6_backwater_model)
    basin_definition = create_basin_definition(
        ribasim_backwater_model.basin.node,
        buffersize=5.0,
    )
    # offset basin definition by one node, since no svats are defined at river nodes.
    dy = np.diff(mf6_backwater_model["GWF_1"]["dis"]["idomain"].y)[0]
    basin_definition_ponding = create_basin_definition(
        ribasim_backwater_model.basin.node, buffersize=5.0, yoff=dy
    )
    mf6_backwater_model = add_rch_package(mf6_backwater_model)
    # mf6_backwater_model = add_well_package(mf6_backwater_model)

    msw_backwater_model.pop("sprinkling")
    msw_backwater_model.pop("mod2svat")
    msw_backwater_model["mod2svat"] = msw.CouplerMapping(
        modflow_dis=mf6_backwater_model["GWF_1"]["dis"]
    )

    mf6_backwater_model["GWF_1"].pop("sto")
    idomain = mf6_backwater_model["GWF_1"]["dis"]["idomain"]
    ss = xr.ones_like(idomain, dtype=float) * 1e-6
    ss[0, :, :] = 0.15  # phreatic layer, importent for non coupled nodes
    mf6_backwater_model["GWF_1"]["sto"] = StorageCoefficient(ss, 0.1, True, 0)

    metamod_coupling = MetaModDriverCoupling(
        mf6_model=mf6_modelname,
        mf6_recharge_package="rch_msw",
    )
    ribamod_coupling = RibaModActiveDriverCoupling(
        mf6_model=mf6_modelname,
        mf6_packages=mf6_active_river_packages + mf6_active_drainage_packages,
        ribasim_basin_definition=basin_definition,
    )
    ribameta_coupling = RibaMetaDriverCoupling(
        ribasim_basin_definition=basin_definition_ponding,
    )
    return RibaMetaMod(
        ribasim_model=ribasim_backwater_model,
        msw_model=msw_backwater_model,
        mf6_simulation=mf6_backwater_model,
        coupling_list=[metamod_coupling, ribamod_coupling, ribameta_coupling],
    )


def case_two_basin_model(
    mf6_two_basin_model: Modflow6Simulation,
    msw_two_basin_model: MetaSwapModel,
    ribasim_two_basin_model: ribasim.Model,
) -> RibaMetaMod:
    mf6_modelname, mf6_model = get_mf6_gwf_modelnames(mf6_two_basin_model)[0]
    mf6_active_river_packages = get_mf6_river_packagenames(mf6_model)
    basin_definition = create_basin_definition(
        ribasim_two_basin_model.basin.node,
        buffersize=250.0,
    )
    mf6_two_basin_model = add_rch_package(mf6_two_basin_model)
    # mf6_two_basin_model = add_well_package(mf6_two_basin_model)

    msw_two_basin_model.pop("sprinkling")
    msw_two_basin_model.pop("mod2svat")
    msw_two_basin_model["mod2svat"] = msw.CouplerMapping(
        modflow_dis=mf6_two_basin_model["GWF_1"]["dis"]
    )

    mf6_two_basin_model["GWF_1"].pop("sto")
    idomain = mf6_two_basin_model["GWF_1"]["dis"]["idomain"]
    ss = xr.ones_like(idomain, dtype=float) * 1e-6
    ss[0, :, :] = 0.15  # phreatic layer, importent for non coupled nodes
    mf6_two_basin_model["GWF_1"]["sto"] = StorageCoefficient(ss, 0.1, True, 0)

    metamod_coupling = MetaModDriverCoupling(
        mf6_model=mf6_modelname,
        mf6_recharge_package="rch_msw",
    )  #         mf6_wel_package="well_msw",
    ribamod_coupling = RibaModActiveDriverCoupling(
        mf6_model=mf6_modelname,
        mf6_packages=mf6_active_river_packages,
        ribasim_basin_definition=basin_definition,
    )
    ribameta_coupling = RibaMetaDriverCoupling(
        ribasim_basin_definition=basin_definition,
    )

    return RibaMetaMod(
        ribasim_model=ribasim_two_basin_model,
        msw_model=msw_two_basin_model,
        mf6_simulation=mf6_two_basin_model,
        coupling_list=[metamod_coupling, ribamod_coupling, ribameta_coupling],
    )


def case_two_basin_model_single_users(
    mf6_two_basin_model_3layer: Modflow6Simulation,
    msw_two_basin_model_3layer: MetaSwapModel,
    ribasim_two_basin_model: ribasim.Model,
) -> RibaMetaMod:
    mf6_modelname, mf6_model = get_mf6_gwf_modelnames(mf6_two_basin_model_3layer)[0]
    mf6_active_river_packages = get_mf6_river_packagenames(mf6_model)
    basin_definition = create_basin_definition(
        ribasim_two_basin_model.basin.node,
        buffersize=250.0,
    )
    mf6_two_basin_model_3layer = add_rch_package(mf6_two_basin_model_3layer)
    mf6_two_basin_model_3layer = add_well_package(mf6_two_basin_model_3layer)

    mf6_two_basin_model_3layer["GWF_1"].pop("sto")
    idomain = mf6_two_basin_model_3layer["GWF_1"]["dis"]["idomain"]
    ss = xr.ones_like(idomain, dtype=float) * 1e-6
    ss[0, :, :] = 0.15  # phreatic layer, importent for non coupled nodes
    mf6_two_basin_model_3layer["GWF_1"]["sto"] = StorageCoefficient(ss, 0.1, True, 0)

    # Add waterusers to model
    ribasim_two_basin_model.user_demand.add(
        ribasim.Node(7, Point(250.0, 10.0), subnetwork_id=2),
        [
            user_demand.Static(  # type: ignore
                demand=[1.0],
                active=True,
                return_factor=[0.0],
                min_level=[-999.0],
                priority=[1],
            ),
        ],
    )
    ribasim_two_basin_model.user_demand.add(
        ribasim.Node(8, Point(750.0, 10.0), subnetwork_id=3),
        [
            user_demand.Static(  # type: ignore
                demand=[0.0, 0.0, 0.0],
                active=True,
                return_factor=[0.0, 0.0, 0.0],
                min_level=[-999.0, -999.0, -999.0],
                priority=[1, 6, 8],
            ),
        ],
    )
    # add subnetwork id to basins
    ribasim_two_basin_model.basin.node.df["subnetwork_id"].loc[
        ribasim_two_basin_model.basin.node.df["node_id"] == 2
    ] = 2
    ribasim_two_basin_model.basin.node.df["subnetwork_id"].loc[
        ribasim_two_basin_model.basin.node.df["node_id"] == 3
    ] = 3
    # add two-way connections to water-user nodes
    ribasim_two_basin_model.edge.add(
        ribasim_two_basin_model.basin[2], ribasim_two_basin_model.user_demand[7]
    )
    ribasim_two_basin_model.edge.add(
        ribasim_two_basin_model.user_demand[7], ribasim_two_basin_model.basin[2]
    )

    ribasim_two_basin_model.edge.add(
        ribasim_two_basin_model.basin[3], ribasim_two_basin_model.user_demand[8]
    )
    ribasim_two_basin_model.edge.add(
        ribasim_two_basin_model.user_demand[8], ribasim_two_basin_model.basin[3]
    )

    # add default level-control to basins
    ribasim_two_basin_model.level_demand.add(
        ribasim.Node(9, Point(240.0, 10.0), subnetwork_id=2),
        [level_demand.Static(priority=[1], min_level=[-1.0e6], max_level=[-1.0e6])],
    )
    ribasim_two_basin_model.edge.add(
        ribasim_two_basin_model.level_demand[9],
        ribasim_two_basin_model.basin[2],
    )
    ribasim_two_basin_model.level_demand.add(
        ribasim.Node(10, Point(740.0, 10.0), subnetwork_id=3),
        [level_demand.Static(priority=[1], min_level=[-1.0e6], max_level=[-1.0e6])],
    )
    ribasim_two_basin_model.edge.add(
        ribasim_two_basin_model.level_demand[10],
        ribasim_two_basin_model.basin[3],
    )

    # activate Allocation in Ribasim-model
    ribasim_two_basin_model.allocation = ribasim.Allocation(
        timestep=86400.0, use_allocation=True
    )

    user_definition = create_basin_definition(
        ribasim_two_basin_model.user_demand.node, buffersize=250.0, nodes=[7]
    )
    metamod_coupling = MetaModDriverCoupling(
        mf6_model=mf6_modelname,
        mf6_recharge_package="rch_msw",
        mf6_wel_package="well_msw",
    )
    ribamod_coupling = RibaModActiveDriverCoupling(
        mf6_model=mf6_modelname,
        mf6_packages=mf6_active_river_packages,
        ribasim_basin_definition=basin_definition,
    )
    ribameta_coupling = RibaMetaDriverCoupling(
        ribasim_basin_definition=basin_definition,
        ribasim_user_demand_definition=user_definition,
    )
    # increase inflow rate to be able to extract irrigation water
    ribasim_two_basin_model.flow_boundary.static.df["flow_rate"][0] = 0.05

    # increase PET in MetaSWAP-model
    pet = msw_two_basin_model_3layer["meteo_grid"].dataset["evapotranspiration"]
    pp = msw_two_basin_model_3layer["meteo_grid"].dataset["precipitation"]
    msw_two_basin_model_3layer["meteo_grid"].dataset["evapotranspiration"] = pet * 100
    msw_two_basin_model_3layer["meteo_grid"].dataset["precipitation"] = pp * 0.0

    # lower initial conditions MF6 model
    mf6_two_basin_model_3layer[mf6_modelname]["ic"].dataset["start"] = -100.0

    # increase river resistance so basins don't run dry
    cond = mf6_two_basin_model_3layer[mf6_modelname][
        mf6_active_river_packages[0]
    ].dataset["conductance"]
    cond_new = (20 * 20) / 50
    active = cond.notnull()
    mf6_two_basin_model_3layer[mf6_modelname][mf6_active_river_packages[0]].dataset[
        "conductance"
    ] = xr.full_like(cond, fill_value=cond_new).where(active)
    return RibaMetaMod(
        ribasim_model=ribasim_two_basin_model,
        msw_model=msw_two_basin_model_3layer,
        mf6_simulation=mf6_two_basin_model_3layer,
        coupling_list=[metamod_coupling, ribamod_coupling, ribameta_coupling],
    )


def case_two_basin_model_double_users(
    mf6_two_basin_model_3layer: Modflow6Simulation,
    msw_two_basin_model_3layer: MetaSwapModel,
    ribasim_two_basin_model: ribasim.Model,
) -> RibaMetaMod:
    mf6_modelname, mf6_model = get_mf6_gwf_modelnames(mf6_two_basin_model_3layer)[0]
    mf6_active_river_packages = get_mf6_river_packagenames(mf6_model)
    basin_definition = create_basin_definition(
        ribasim_two_basin_model.basin.node,
        buffersize=250.0,
    )
    mf6_two_basin_model_3layer = add_rch_package(mf6_two_basin_model_3layer)
    mf6_two_basin_model_3layer = add_well_package(mf6_two_basin_model_3layer)

    mf6_two_basin_model_3layer["GWF_1"].pop("sto")
    idomain = mf6_two_basin_model_3layer["GWF_1"]["dis"]["idomain"]
    ss = xr.ones_like(idomain, dtype=float) * 1e-6
    ss[0, :, :] = 0.15  # phreatic layer, important for non coupled nodes
    mf6_two_basin_model_3layer["GWF_1"]["sto"] = StorageCoefficient(ss, 0.1, True, 0)

    # Add waterusers to model; basin 2
    ribasim_two_basin_model.user_demand.add(
        ribasim.Node(7, Point(250.0, 10.0), subnetwork_id=2),
        [
            user_demand.Static(  # type: ignore
                demand=[1.0],
                active=True,
                return_factor=[0.0],
                min_level=[-999.0],
                priority=[1],
            ),
        ],
    )
    ribasim_two_basin_model.user_demand.add(
        ribasim.Node(8, Point(240.0, 20.0), subnetwork_id=2),
        [
            user_demand.Static(  # type: ignore
                demand=[0.00001, 0.00002],
                active=True,
                return_factor=[0.0, 0.0],
                min_level=[-999.0, -999.0],
                priority=[4, 8],
            ),
        ],
    )
    # Add waterusers to model; basin 3
    ribasim_two_basin_model.user_demand.add(
        ribasim.Node(9, Point(750.0, 10.0), subnetwork_id=3),
        [
            user_demand.Static(  # type: ignore
                demand=[1.0],
                active=True,
                return_factor=[0.0],
                min_level=[-999.0],
                priority=[3],
            ),
        ],
    )
    # add subnetwork id to basins
    ribasim_two_basin_model.basin.node.df["subnetwork_id"].loc[
        ribasim_two_basin_model.basin.node.df["node_id"] == 2
    ] = 2
    ribasim_two_basin_model.basin.node.df["subnetwork_id"].loc[
        ribasim_two_basin_model.basin.node.df["node_id"] == 3
    ] = 3
    # add two-way connections to water-user nodes; basin 2
    ribasim_two_basin_model.edge.add(
        ribasim_two_basin_model.basin[2], ribasim_two_basin_model.user_demand[7]
    )
    ribasim_two_basin_model.edge.add(
        ribasim_two_basin_model.user_demand[7], ribasim_two_basin_model.basin[2]
    )
    ribasim_two_basin_model.edge.add(
        ribasim_two_basin_model.basin[2], ribasim_two_basin_model.user_demand[8]
    )
    ribasim_two_basin_model.edge.add(
        ribasim_two_basin_model.user_demand[8], ribasim_two_basin_model.basin[2]
    )
    # add two-way connections to water-user nodes; basin 3
    ribasim_two_basin_model.edge.add(
        ribasim_two_basin_model.basin[3], ribasim_two_basin_model.user_demand[9]
    )
    ribasim_two_basin_model.edge.add(
        ribasim_two_basin_model.user_demand[9], ribasim_two_basin_model.basin[3]
    )
    # add default level-control to basins
    ribasim_two_basin_model.level_demand.add(
        ribasim.Node(10, Point(240.0, 10.0), subnetwork_id=2),
        [level_demand.Static(priority=[1], min_level=[-1.0e6], max_level=[-1.0e6])],
    )
    ribasim_two_basin_model.edge.add(
        ribasim_two_basin_model.level_demand[10],
        ribasim_two_basin_model.basin[2],
    )
    ribasim_two_basin_model.level_demand.add(
        ribasim.Node(11, Point(740.0, 10.0), subnetwork_id=3),
        [level_demand.Static(priority=[1], min_level=[-1.0e6], max_level=[-1.0e6])],
    )
    ribasim_two_basin_model.edge.add(
        ribasim_two_basin_model.level_demand[11],
        ribasim_two_basin_model.basin[3],
    )

    # increatse initial stage second basin, so irrigation can take place.
    ribasim_two_basin_model.basin.state.df["level"].loc[
        ribasim_two_basin_model.basin.node.df["node_id"] == 3
    ] = 8.0
    new_df = pd.DataFrame(
        {
            "node_id": np.array([4] * 3),
            "active": np.array([pd.NA] * 3),
            "level": np.array([0, 3.0, 6.0]),
            "flow_rate": np.array([0.0, 0.0, 0.000000001]),
            "control_state": [None, None, None],
        }
    )
    ribasim_two_basin_model.tabulated_rating_curve.static.df = new_df

    # activate Allocation in Ribasim-model
    ribasim_two_basin_model.allocation = ribasim.Allocation(
        timestep=86400.0, use_allocation=True
    )

    user_definitions = create_basin_definition(
        ribasim_two_basin_model.user_demand.node,
        buffersize=250.0,
        nodes=[7, 9],
    )

    metamod_coupling = MetaModDriverCoupling(
        mf6_model=mf6_modelname,
        mf6_recharge_package="rch_msw",
        mf6_wel_package="well_msw",
    )
    ribamod_coupling = RibaModActiveDriverCoupling(
        mf6_model=mf6_modelname,
        mf6_packages=mf6_active_river_packages,
        ribasim_basin_definition=basin_definition,
    )
    ribameta_coupling = RibaMetaDriverCoupling(
        ribasim_basin_definition=basin_definition,
        ribasim_user_demand_definition=user_definitions,
    )
    # increase inflow rate to be able to extract irrigation water
    ribasim_two_basin_model.flow_boundary.static.df["flow_rate"][0] = 0.05

    # increase PET in MetaSWAP-model
    pet = msw_two_basin_model_3layer["meteo_grid"].dataset["evapotranspiration"]
    pp = msw_two_basin_model_3layer["meteo_grid"].dataset["precipitation"]
    msw_two_basin_model_3layer["meteo_grid"].dataset["evapotranspiration"] = pet * 100
    msw_two_basin_model_3layer["meteo_grid"].dataset["precipitation"] = pp * 0.0

    # increase sprinkling season
    msw_two_basin_model_3layer["landuse_options"]["start_sprinkling_season"][:] = 0.0
    msw_two_basin_model_3layer.simulation_settings["tdbgsm"] = 0.0
    soil_cover = msw_two_basin_model_3layer["crop_factors"]["soil_cover"]
    soil_cover[:] = 1.0
    new = msw.AnnualCropFactors(
        soil_cover=soil_cover,
        leaf_area_index=xr.full_like(soil_cover, 3.0),
        interception_capacity=xr.zeros_like(soil_cover),
        vegetation_factor=xr.ones_like(soil_cover),
        interception_factor=xr.ones_like(soil_cover),
        bare_soil_factor=xr.ones_like(soil_cover),
        ponding_factor=xr.ones_like(soil_cover),
    )
    msw_two_basin_model_3layer.pop("crop_factors")
    msw_two_basin_model_3layer["crop_factors"] = new

    # lower initial conditions MF6 model
    mf6_two_basin_model_3layer[mf6_modelname]["ic"].dataset["start"] = -100.0

    # increase river resistance so basins don't run dry
    cond = mf6_two_basin_model_3layer[mf6_modelname][
        mf6_active_river_packages[0]
    ].dataset["conductance"]
    cond_new = (20 * 20) / 50
    active = cond.notnull()
    mf6_two_basin_model_3layer[mf6_modelname][mf6_active_river_packages[0]].dataset[
        "conductance"
    ] = xr.full_like(cond, fill_value=cond_new).where(active)
    return RibaMetaMod(
        ribasim_model=ribasim_two_basin_model,
        msw_model=msw_two_basin_model_3layer,
        mf6_simulation=mf6_two_basin_model_3layer,
        coupling_list=[metamod_coupling, ribamod_coupling, ribameta_coupling],
    )
