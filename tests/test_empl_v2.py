from typo_modal.service import TypoModalService
from api.models.modal_typo import EmplActions


def test_empl_v2_tp_measures():
    # compute_mesu_empl_v2 does not use the service data
    empl = EmplActions(mesures_tp=["tpg_pass"], mesures_velo=["shower"],
                       mesures_pro_tp=["train_pro"]).model_dump()
    mesure_dt, mesure_pro = TypoModalService.compute_mesu_empl_v2(
        None, empl, ["train", "inter_ma_tp"], ["pub", "train", "bike"])
    assert mesure_dt == {"train": ["tpg_pass"], "inter_ma_tp": ["shower", "tpg_pass"]}
    assert mesure_pro == {"pub": ["train_pro"], "train": ["train_pro"], "bike": []}
