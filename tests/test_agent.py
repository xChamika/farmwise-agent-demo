"""Unit tests for FarmWise Advisor's function tools.

Run with: python -m pytest tests/ -v
Requires the project dependencies (see requirements.txt) to be installed,
since farmwise_agent.agent imports google.adk at module load time.
"""

from farmwise_agent.agent import (
    calculate_irrigation_schedule,
    get_crop_details,
    get_fertilizer_plan,
    get_pest_treatment,
    list_crops,
    list_pests,
    recommend_crop,
)


def test_list_crops_no_filter_returns_all():
    result = list_crops()
    assert result["status"] == "success"
    assert result["count"] == 6


def test_list_crops_filters_by_soil_type():
    result = list_crops(soil_type="loam")
    assert result["status"] == "success"
    assert all(c["soil_type"] == "loam" for c in result["crops"])


def test_get_crop_details_known_crop():
    result = get_crop_details("CROP-RICE")
    assert result["status"] == "success"
    assert result["crop"]["name"] == "Paddy Rice"


def test_get_crop_details_unknown_crop():
    result = get_crop_details("CROP-DOES-NOT-EXIST")
    assert result["status"] == "error"


def test_recommend_crop_matches_season_and_soil():
    result = recommend_crop(soil_type="loam", season="dry")
    assert result["status"] == "success"
    ids = [c["crop_id"] for c in result["recommendations"]]
    assert "CROP-MAIZE" in ids or "CROP-TOMATO" in ids


def test_recommend_crop_respects_water_budget():
    result = recommend_crop(soil_type="sandy-loam", season="dry", max_weekly_water_mm=20)
    assert result["status"] == "success"
    for crop in result["recommendations"]:
        details = get_crop_details(crop["crop_id"])["crop"]
        assert details["water_need_mm_per_week"] <= 20


def test_list_pests_filters_by_crop():
    result = list_pests(crop_id="CROP-TOMATO")
    assert result["status"] == "success"
    assert all("CROP-TOMATO" in p["affected_crop_ids"] for p in result["pests"])


def test_get_pest_treatment_known_pest():
    result = get_pest_treatment("PEST-APHID")
    assert result["status"] == "success"
    assert "organic_treatment" in result["pest"]


def test_calculate_irrigation_schedule_deficit():
    result = calculate_irrigation_schedule("CROP-TOMATO", rainfall_last_week_mm=10, field_area_hectares=1)
    assert result["status"] == "success"
    assert result["deficit_mm"] == 25.0
    assert result["recommended_irrigation_liters"] == 250_000


def test_calculate_irrigation_schedule_surplus():
    result = calculate_irrigation_schedule("CROP-MUNGBEAN", rainfall_last_week_mm=40, field_area_hectares=1)
    assert result["status"] == "success"
    assert result["deficit_mm"] == 0
    assert result["surplus_mm"] == 25.0


def test_get_fertilizer_plan_known_crop():
    result = get_fertilizer_plan("CROP-MAIZE", growth_stage="flowering")
    assert result["status"] == "success"
    assert "phosphorus" in result["stage_guidance"].lower()
