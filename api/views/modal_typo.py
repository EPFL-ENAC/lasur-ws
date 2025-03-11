import logging
from typing import Dict
from fastapi import APIRouter, Security
from ..auth import get_api_key
from typo_modal.service import TypoModalService, load_data
from ..models.modal_typo import ODData, TypoData, RecoData, RecoMultiData, RecoProData, EmplData

router = APIRouter()

od_mm, orig_dess, dest_dess = load_data()


@router.post("/geo", response_model=Dict)
async def compute_geo(
    odData: ODData,
    api_key: str = Security(get_api_key),
) -> Dict:
    """Compute nearest origin and destination based on the provided data."""
    service = TypoModalService(od_mm, orig_dess, dest_dess)
    try:
        return service.compute_geo(odData.o_lon, odData.o_lat, odData.d_lon, odData.d_lat)
    except Exception as e:
        logging.error(e, exc_info=True)
        return {'error': str(e)}


@router.post("/typo", response_model=Dict)
async def compute_typo(
    data: TypoData,
    api_key: str = Security(get_api_key),
) -> Dict:
    """Compute modal typology based on the provided data."""
    service = TypoModalService(od_mm, orig_dess, dest_dess)
    try:
        typo = service.compute_typo(
            data.a_voit,
            data.a_moto,
            data.a_tpu,
            data.a_train,
            data.a_marc,
            data.a_velo,
            data.i_tmps,
            data.i_prix,
            data.i_flex,
            data.i_conf,
            data.i_fiab,
            data.i_prof,
            data.i_envi)
        return {'typo': typo}
    except Exception as e:
        logging.error(e, exc_info=True)
        return {'error': str(e)}


@router.post("/reco", response_model=Dict)
async def compute_reco(
    data: RecoData,
    api_key: str = Security(get_api_key),
) -> Dict:
    """Compute modal recommendation based on the provided data."""
    service = TypoModalService(od_mm, orig_dess, dest_dess)
    try:
        t_traj_mm = service.compute_geo(
            data.o_lon, data.o_lat, data.d_lon, data.d_lat)
        reco_dt, scores = service.compute_reco_dt(t_traj_mm,
                                                  data.tps_traj,
                                                  data.tx_trav,
                                                  data.tx_tele,
                                                  data.fm_dt_voit,
                                                  data.fm_dt_moto,
                                                  data.fm_dt_tpu,
                                                  data.fm_dt_train,
                                                  data.fm_dt_velo,
                                                  data.a_voit,
                                                  data.a_moto,
                                                  data.a_tpu,
                                                  data.a_train,
                                                  data.a_marc,
                                                  data.a_velo,
                                                  data.i_tmps,
                                                  data.i_prix,
                                                  data.i_flex,
                                                  data.i_conf,
                                                  data.i_fiab,
                                                  data.i_prof,
                                                  data.i_envi)
        return {'reco_dt': reco_dt, 'scores': scores}
    except Exception as e:
        logging.error(e, exc_info=True)
        return {'error': str(e)}


@router.post("/reco-multi", response_model=Dict)
async def compute_reco_multi(
    data: RecoMultiData,
    api_key: str = Security(get_api_key),
) -> Dict:
    """Compute modal recommendation based on the provided data."""
    service = TypoModalService(od_mm, orig_dess, dest_dess)
    try:
        t_traj_mm = service.compute_geo(
            data.o_lon, data.o_lat, data.d_lon, data.d_lat)
        reco_dt2, scores, access = service.compute_reco_multi(t_traj_mm,
                                                              data.tps_traj,
                                                              data.constraints,
                                                              data.fm_dt_voit,
                                                              data.fm_dt_moto,
                                                              data.fm_dt_tpu,
                                                              data.fm_dt_train,
                                                              data.fm_dt_velo,
                                                              data.fm_dt_march,
                                                              data.fm_dt_inter,
                                                              data.a_voit,
                                                              data.a_moto,
                                                              data.a_tpu,
                                                              data.a_train,
                                                              data.a_velo,
                                                              data.a_marc,
                                                              data.i_tmps,
                                                              data.i_prix,
                                                              data.i_flex,
                                                              data.i_conf,
                                                              data.i_fiab,
                                                              data.i_prof,
                                                              data.i_envi
                                                              )
        return {'reco_dt2': reco_dt2, 'scores': scores, 'access': access}
    except Exception as e:
        logging.error(e, exc_info=True)
        return {'error': str(e)}


@router.post("/reco-pro", response_model=Dict)
async def compute_reco_pro(
    data: RecoProData,
    api_key: str = Security(get_api_key),
) -> Dict:
    """Compute pro modal recommendation based on the provided data."""
    service = TypoModalService(od_mm, orig_dess, dest_dess)
    try:
        reco_pro_loc, reco_pro_reg, reco_pro_int = service.compute_reco_pro({
            'velo': data.score_velo,
            'tpu': data.score_tpu,
            'train': data.score_train,
            'elec': data.score_elec
        },
            data.fr_pro_loc,
            data.fr_pro_reg,
            data.fr_pro_int,
            data.fm_pro_loc_voit,
            data.fm_pro_loc_moto,
            data.fm_pro_loc_tpu,
            data.fm_pro_loc_train,
            data.fm_pro_loc_velo,
            data.fm_pro_loc_marc,
            data.fm_pro_reg_voit,
            data.fm_pro_reg_moto,
            data.fm_pro_reg_train,
            data.fm_pro_reg_avio,
            data.fm_pro_int_voit,
            data.fm_pro_int_train,
            data.fm_pro_int_avio)
        return {'reco_pro_loc': reco_pro_loc, 'reco_pro_reg': reco_pro_reg, 'reco_pro_int': reco_pro_int}
    except Exception as e:
        logging.error(e, exc_info=True)
        return {'error': str(e)}


@router.post("/empl", response_model=Dict)
async def compute_empl_actions(
    data: EmplData,
    api_key: str = Security(get_api_key),
) -> Dict:
    """Compute employer actions based on the provided data."""
    service = TypoModalService(od_mm, orig_dess, dest_dess)
    try:
        mesure_dt1, mesure_dt2, mesure_pro_loc, mesure_pro_regint = service.compute_mesu_empl(
            data.empl.model_dump(),
            data.reco_dt2,
            data.reco_pro_loc,
            data.reco_pro_reg,
            data.reco_pro_int)
        return {'mesure_dt1': mesure_dt1, 'mesure_dt2': mesure_dt2, 'mesure_pro_loc': mesure_pro_loc, 'mesure_pro_regint': mesure_pro_regint}
    except Exception as e:
        logging.error(e, exc_info=True)
        return {'error': str(e)}
