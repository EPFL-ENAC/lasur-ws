from fastapi import FastAPI
from pydantic import BaseModel


class ODData(BaseModel):
    o_lon: float
    o_lat: float
    d_lon: float
    d_lat: float

class TypoData(BaseModel):
    a_voit: int
    a_moto: int
    a_tpu: int
    a_train: int
    a_marc: int
    a_velo: int
    i_tmps: int
    i_prix: int
    i_flex: int
    i_conf: int
    i_fiab: int
    i_prof: int
    i_envi: int
    
class RecoData(BaseModel):
    o_lon: float
    o_lat: float
    d_lon: float
    d_lat: float
    tps_traj: int
    tx_trav: int
    tx_tele: int
    fm_dt_voit: int
    fm_dt_moto: int
    fm_dt_tpu: int
    fm_dt_train: int
    fm_dt_velo: int
    a_voit: int
    a_moto: int
    a_tpu: int
    a_train: int
    a_marc: int
    a_velo: int
    i_tmps: int
    i_prix: int
    i_flex: int
    i_conf: int
    i_fiab: int
    i_prof: int
    i_envi: int