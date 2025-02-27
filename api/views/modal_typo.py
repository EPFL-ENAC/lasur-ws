from typing import Dict
from fastapi import APIRouter, Security
from ..auth import get_api_key
from typo_modal.service import TypoModalService, load_data
from ..models.modal_typo import ODData, TypoData, RecoData

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
        return {'error': str(e)}
    
@router.post("/typo", response_model=Dict)
async def compute_typo(
    typoData: TypoData,
    api_key: str = Security(get_api_key),
) -> Dict:
    """Compute modal typology based on the provided data."""
    service = TypoModalService(od_mm, orig_dess, dest_dess)
    try:
        return service.compute_typo(
            typoData.a_voit,
            typoData.a_moto,
            typoData.a_tpu,
            typoData.a_train,
            typoData.a_marc,
            typoData.a_velo,
            typoData.i_tmps,
            typoData.i_prix,
            typoData.i_flex,
            typoData.i_conf,
            typoData.i_fiab,
            typoData.i_prof,
            typoData.i_envi)
    except Exception as e:
        return {'error': str(e)}

@router.post("/reco", response_model=Dict)
async def compute_reco(
    recoData: RecoData,
    api_key: str = Security(get_api_key),
) -> Dict:
    """Compute modal recommendation based on the provided data."""
    service = TypoModalService(od_mm, orig_dess, dest_dess)
    try:
        t_traj_mm = service.compute_geo(recoData.o_lon, recoData.o_lat, recoData.d_lon, recoData.d_lat)
        reco = service.compute_reco_dt(t_traj_mm, 
                                       recoData.tps_traj,
                                       recoData.tx_trav,
                                       recoData.tx_tele,
                                       recoData.fm_dt_voit,
                                       recoData.fm_dt_moto,
                                       recoData.fm_dt_tpu,
                                       recoData.fm_dt_train,
                                       recoData.fm_dt_velo, 
                                       recoData.a_voit,
                                       recoData.a_moto,
                                       recoData.a_tpu,
                                       recoData.a_train,
                                       recoData.a_marc,
                                       recoData.a_velo,
                                       recoData.i_tmps,
                                       recoData.i_prix,
                                       recoData.i_flex,
                                       recoData.i_conf,
                                       recoData.i_fiab,
                                       recoData.i_prof,
                                       recoData.i_envi)
        return { 'reco': reco }
    except Exception as e:
        return {'error': str(e)}
