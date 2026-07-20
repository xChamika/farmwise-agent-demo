from __future__ import annotations

import os
from typing import Literal
from uuid import uuid4

import dotenv
from google import genai
from google.adk.agents import Agent
from google.adk.tools import ToolContext
from google.genai import types

dotenv.load_dotenv()


IMAGE_MODEL = os.getenv("FARMWISE_IMAGE_MODEL", "gemini-3.1-flash-image")


# ---------------------------------------------------------------------------
# Knowledge base (in-memory for the demo; swap for a JSON file or DB later)
# ---------------------------------------------------------------------------

CROPS = [
    {
        "crop_id": "CROP-RICE",
        "name": "Paddy Rice",
        "soil_type": "clay",
        "season": "wet",
        "water_need_mm_per_week": 50,
        "days_to_maturity": 120,
        "npk_ratio": "120:60:40 kg/ha (N:P:K)",
        "common_pest_ids": ["PEST-STEMBORER", "PEST-BLAST"],
        "region_notes": "Best suited to low-lying, water-retentive paddy fields.",
    },
    {
        "crop_id": "CROP-MAIZE",
        "name": "Maize (Corn)",
        "soil_type": "loam",
        "season": "dry",
        "water_need_mm_per_week": 30,
        "days_to_maturity": 100,
        "npk_ratio": "150:60:60 kg/ha (N:P:K)",
        "common_pest_ids": ["PEST-FALLARMYWORM", "PEST-APHID"],
        "region_notes": "Performs well on well-drained loam with full sun exposure.",
    },
    {
        "crop_id": "CROP-CHILI",
        "name": "Chili Pepper",
        "soil_type": "sandy-loam",
        "season": "dry",
        "water_need_mm_per_week": 25,
        "days_to_maturity": 90,
        "npk_ratio": "100:50:50 kg/ha (N:P:K)",
        "common_pest_ids": ["PEST-APHID", "PEST-THRIPS"],
        "region_notes": "Needs raised beds and consistent but moderate irrigation.",
    },
    {
        "crop_id": "CROP-TOMATO",
        "name": "Tomato",
        "soil_type": "loam",
        "season": "dry",
        "water_need_mm_per_week": 35,
        "days_to_maturity": 80,
        "npk_ratio": "110:55:55 kg/ha (N:P:K)",
        "common_pest_ids": ["PEST-BLIGHT", "PEST-APHID"],
        "region_notes": "Benefits from staking, mulching, and drip irrigation.",
    },
    {
        "crop_id": "CROP-MUNGBEAN",
        "name": "Mung Bean",
        "soil_type": "sandy-loam",
        "season": "dry",
        "water_need_mm_per_week": 15,
        "days_to_maturity": 65,
        "npk_ratio": "20:40:20 kg/ha (N:P:K)",
        "common_pest_ids": ["PEST-APHID"],
        "region_notes": "A low-water legume good for crop rotation and soil nitrogen recovery.",
    },
    {
        "crop_id": "CROP-BANANA",
        "name": "Banana",
        "soil_type": "clay-loam",
        "season": "wet",
        "water_need_mm_per_week": 40,
        "days_to_maturity": 300,
        "npk_ratio": "200:70:200 kg/ha (N:P:K)",
        "common_pest_ids": ["PEST-WEEVIL"],
        "region_notes": "Long-cycle crop that needs wind shelter and steady moisture.",
    },
]

PESTS = [
    {
        "pest_id": "PEST-STEMBORER",
        "name": "Yellow Stem Borer",
        "affected_crop_ids": ["CROP-RICE"],
        "symptoms": "Dead heart in young plants; white empty panicles (whiteheads) at flowering.",
        "severity": "high",
        "organic_treatment": "Release Trichogramma egg parasitoids; remove and destroy stubble after harvest.",
        "chemical_treatment": "Apply a recommended granular systemic insecticide at early tillering; follow local agri-extension dosage.",
    },
    {
        "pest_id": "PEST-BLAST",
        "name": "Rice Blast (fungal disease)",
        "affected_crop_ids": ["CROP-RICE"],
        "symptoms": "Diamond-shaped grey lesions with brown margins on leaves.",
        "severity": "high",
        "organic_treatment": "Use resistant varieties; avoid excess nitrogen; improve field drainage.",
        "chemical_treatment": "Apply a registered fungicide (e.g. tricyclazole-based) at first sign of lesions.",
    },
    {
        "pest_id": "PEST-FALLARMYWORM",
        "name": "Fall Armyworm",
        "affected_crop_ids": ["CROP-MAIZE"],
        "symptoms": "Ragged holes in leaves, sawdust-like frass in the whorl.",
        "severity": "high",
        "organic_treatment": "Handpick larvae early; apply neem-based biopesticide; encourage natural predators.",
        "chemical_treatment": "Targeted insecticide application directly into the leaf whorl if infestation is severe.",
    },
    {
        "pest_id": "PEST-APHID",
        "name": "Aphids",
        "affected_crop_ids": [
            "CROP-MAIZE",
            "CROP-CHILI",
            "CROP-TOMATO",
            "CROP-MUNGBEAN",
        ],
        "symptoms": "Clusters of small insects on new growth; curling, yellowing leaves; sticky honeydew.",
        "severity": "medium",
        "organic_treatment": "Spray diluted neem oil or insecticidal soap; introduce ladybird beetles.",
        "chemical_treatment": "Use a systemic aphicide only if the infestation threatens yield.",
    },
    {
        "pest_id": "PEST-THRIPS",
        "name": "Thrips",
        "affected_crop_ids": ["CROP-CHILI"],
        "symptoms": "Silvery streaks on leaves, distorted new growth, and reduced flowering.",
        "severity": "medium",
        "organic_treatment": "Use blue sticky traps; apply neem oil weekly during flowering.",
        "chemical_treatment": "Rotate approved insecticides to avoid resistance build-up.",
    },
    {
        "pest_id": "PEST-BLIGHT",
        "name": "Early Blight (fungal disease)",
        "affected_crop_ids": ["CROP-TOMATO"],
        "symptoms": "Dark concentric-ring spots on older leaves, starting from the bottom of the plant.",
        "severity": "medium",
        "organic_treatment": "Remove infected lower leaves; improve airflow with wider spacing; mulch to prevent soil splash.",
        "chemical_treatment": "Apply a copper-based fungicide on a preventive schedule during humid periods.",
    },
    {
        "pest_id": "PEST-WEEVIL",
        "name": "Banana Weevil",
        "affected_crop_ids": ["CROP-BANANA"],
        "symptoms": "Tunnels in the pseudostem base; wilting and toppling of mature plants.",
        "severity": "high",
        "organic_treatment": "Use pseudostem trap logs to catch adults; maintain field sanitation.",
        "chemical_treatment": "Apply a registered soil-drench insecticide around the mat base if trapping is insufficient.",
    },
]


def _find_crop(crop_id: str) -> dict | None:
    return next((c for c in CROPS if c["crop_id"] == crop_id), None)


def _find_pest(pest_id: str) -> dict | None:
    return next((p for p in PESTS if p["pest_id"] == pest_id), None)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


def list_crops(
    soil_type: str | None = None,
    season: Literal["wet", "dry"] | None = None,
) -> dict:
    """List crops in the advisory catalogue, optionally filtered by soil type or season.

    Args:
        soil_type: Optional soil type to filter by, e.g. "loam", "clay", "sandy-loam".
        season: Optional growing season to filter by ("wet" or "dry").

    Returns:
        Matching crops and a count.
    """
    matches = []
    for crop in CROPS:
        if soil_type and crop["soil_type"] != soil_type:
            continue
        if season and crop["season"] != season:
            continue
        matches.append(
            {
                "crop_id": crop["crop_id"],
                "name": crop["name"],
                "soil_type": crop["soil_type"],
                "season": crop["season"],
                "days_to_maturity": crop["days_to_maturity"],
            }
        )
    return {"status": "success", "count": len(matches), "crops": matches}


def get_crop_details(crop_id: str) -> dict:
    """Get full agronomic details for one crop.

    Args:
        crop_id: Crop identifier, for example CROP-RICE.

    Returns:
        Crop details if found, including water need, fertilizer ratio, and pests.
    """
    crop = _find_crop(crop_id)
    if not crop:
        return {"status": "error", "message": f"Unknown crop_id: {crop_id}"}
    return {"status": "success", "crop": crop.copy()}


def recommend_crop(
    soil_type: str,
    season: Literal["wet", "dry"],
    max_weekly_water_mm: int | None = None,
) -> dict:
    """Recommend the best-matching crops for a farmer's field conditions.

    Args:
        soil_type: The farmer's soil type, e.g. "loam", "clay", "sandy-loam", "clay-loam".
        season: The current or upcoming growing season ("wet" or "dry").
        max_weekly_water_mm: Optional cap on water the farmer can realistically supply
            per week (mm). Crops needing more than this are excluded.

    Returns:
        A ranked list of suitable crops with a short reason for each match.
    """
    candidates = []
    for crop in CROPS:
        if crop["season"] != season:
            continue
        soil_match = crop["soil_type"] == soil_type
        water_ok = (
            max_weekly_water_mm is None
            or crop["water_need_mm_per_week"] <= max_weekly_water_mm
        )
        if not water_ok:
            continue
        score = 0
        reasons = []
        if soil_match:
            score += 2
            reasons.append(f"matches your {soil_type} soil")
        else:
            reasons.append(
                f"tolerates other soils though it prefers {crop['soil_type']}"
            )
        if max_weekly_water_mm is not None:
            reasons.append(
                f"needs {crop['water_need_mm_per_week']}mm/week, within your "
                f"{max_weekly_water_mm}mm/week budget"
            )
        score += 1  # season already matched to reach this point
        candidates.append(
            {
                "crop_id": crop["crop_id"],
                "name": crop["name"],
                "score": score,
                "reason": "; ".join(reasons),
            }
        )

    candidates.sort(key=lambda c: c["score"], reverse=True)
    return {
        "status": "success",
        "soil_type": soil_type,
        "season": season,
        "count": len(candidates),
        "recommendations": candidates,
    }


def list_pests(crop_id: str | None = None) -> dict:
    """List known pests and diseases, optionally filtered to those affecting one crop.

    Args:
        crop_id: Optional crop identifier to filter pests relevant to that crop.

    Returns:
        Matching pests and a count.
    """
    matches = []
    for pest in PESTS:
        if crop_id and crop_id not in pest["affected_crop_ids"]:
            continue
        matches.append(
            {
                "pest_id": pest["pest_id"],
                "name": pest["name"],
                "severity": pest["severity"],
                "affected_crop_ids": pest["affected_crop_ids"],
            }
        )
    return {"status": "success", "count": len(matches), "pests": matches}


def get_pest_treatment(pest_id: str) -> dict:
    """Get symptoms and organic/chemical treatment guidance for one pest or disease.

    Args:
        pest_id: Pest identifier, for example PEST-APHID.

    Returns:
        Full treatment guidance if found.
    """
    pest = _find_pest(pest_id)
    if not pest:
        return {"status": "error", "message": f"Unknown pest_id: {pest_id}"}
    return {"status": "success", "pest": pest.copy()}


def calculate_irrigation_schedule(
    crop_id: str,
    rainfall_last_week_mm: float,
    field_area_hectares: float = 1.0,
) -> dict:
    """Calculate this week's irrigation need for a crop given recent rainfall.

    Args:
        crop_id: Crop identifier, for example CROP-TOMATO.
        rainfall_last_week_mm: Rainfall received in the last 7 days, in millimetres.
        field_area_hectares: Field size in hectares, used to estimate total water volume.

    Returns:
        The weekly water deficit or surplus, and a recommended irrigation amount.
    """
    crop = _find_crop(crop_id)
    if not crop:
        return {"status": "error", "message": f"Unknown crop_id: {crop_id}"}

    need_mm = crop["water_need_mm_per_week"]
    deficit_mm = max(0.0, need_mm - rainfall_last_week_mm)
    surplus_mm = max(0.0, rainfall_last_week_mm - need_mm)
    # 1 mm of water over 1 hectare = 10,000 litres
    liters_needed = deficit_mm * 10_000 * field_area_hectares

    return {
        "status": "success",
        "crop_id": crop_id,
        "crop_name": crop["name"],
        "weekly_water_need_mm": need_mm,
        "rainfall_last_week_mm": rainfall_last_week_mm,
        "deficit_mm": round(deficit_mm, 1),
        "surplus_mm": round(surplus_mm, 1),
        "recommended_irrigation_liters": round(liters_needed, 0),
        "advice": (
            "No irrigation needed this week; drainage check recommended if surplus is large."
            if deficit_mm == 0
            else f"Irrigate to supply approximately {round(deficit_mm, 1)}mm this week."
        ),
    }


def get_fertilizer_plan(crop_id: str, growth_stage: Literal["seedling", "vegetative", "flowering", "maturity"]) -> dict:
    """Get an N:P:K fertilizer guideline for a crop at a given growth stage.

    Args:
        crop_id: Crop identifier, for example CROP-MAIZE.
        growth_stage: Current growth stage of the crop.

    Returns:
        The crop's total-season NPK ratio and stage-specific emphasis.
    """
    crop = _find_crop(crop_id)
    if not crop:
        return {"status": "error", "message": f"Unknown crop_id: {crop_id}"}

    stage_emphasis = {
        "seedling": "Light nitrogen application to support early leaf growth; avoid overfeeding roots.",
        "vegetative": "Nitrogen-heavy feeding to build strong stems and leaf canopy.",
        "flowering": "Shift toward phosphorus and potassium to support flowering and fruit set.",
        "maturity": "Reduce nitrogen; maintain potassium to support fruit/grain fill and ripening.",
    }

    return {
        "status": "success",
        "crop_id": crop_id,
        "crop_name": crop["name"],
        "season_total_npk": crop["npk_ratio"],
        "growth_stage": growth_stage,
        "stage_guidance": stage_emphasis[growth_stage],
    }


async def create_field_diagnosis_image(
    description: str,
    tool_context: ToolContext,
    aspect_ratio: Literal["1:1", "4:3", "3:4", "16:9", "9:16"] = "4:3",
) -> dict:
    """Create an illustrative diagnostic image (e.g. pest damage or healthy-crop
    reference) and save it as an ADK session artifact.

    Use this only when the user explicitly asks for a picture or illustration.
    The description should identify the crop, symptom or scene, and framing so
    the image is useful as a reference, not a real photograph claim.

    Args:
        description: A detailed description of the illustration the user wants.
        aspect_ratio: Output shape; 4:3 suits close-up reference shots.

    Returns:
        The generated artifact filename and version, or a safe error message.
    """
    clean_description = description.strip()
    if not clean_description:
        return {
            "status": "error",
            "message": "Describe the crop, symptom, or scene you want illustrated.",
        }

    prompt = (
        "Create a clear, realistic agricultural reference illustration for a "
        "farm advisory app. The image should look like an educational field guide "
        "photo or diagram, accurate to real crop and pest appearance, with no "
        "text, logos, watermarks, or UI elements. Scene request: "
        f"{clean_description}"
    )

    async_client = None
    try:
        client = genai.Client()
        async_client = client.aio
        response = await async_client.models.generate_content(
            model=IMAGE_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                    image_size="1K",
                    output_mime_type="image/png",
                ),
            ),
        )

        image_data = None
        image_mime_type = "image/png"
        for part in response.parts or []:
            if part.inline_data and part.inline_data.data:
                image_data = part.inline_data.data
                image_mime_type = part.inline_data.mime_type or image_mime_type
                break

        if image_data is None:
            return {
                "status": "error",
                "message": (
                    "The image model did not return an image. Try a different "
                    "description or check the model's safety response."
                ),
            }

        extension = "jpg" if image_mime_type == "image/jpeg" else "png"
        filename = f"farmwise-{uuid4().hex[:10]}.{extension}"
        version = await tool_context.save_artifact(
            filename,
            types.Part.from_bytes(data=image_data, mime_type=image_mime_type),
            custom_metadata={
                "generator": IMAGE_MODEL,
                "aspect_ratio": aspect_ratio,
            },
        )
        return {
            "status": "success",
            "artifact_filename": filename,
            "artifact_version": version,
            "mime_type": image_mime_type,
            "aspect_ratio": aspect_ratio,
        }
    except Exception:
        return {
            "status": "error",
            "message": (
                "Image generation failed. Check your Google credentials, image "
                "model access, API quota, and ADK artifact service."
            ),
        }
    finally:
        if async_client is not None:
            try:
                await async_client.aclose()
            except Exception:
                pass


root_agent = Agent(
    name="farmwise_agent",
    model="gemini-3.1-flash-lite",
    description="FarmWise Advisor helps students and small farmers with crop selection, pest treatment, irrigation, and fertilizer planning.",
    instruction="""
You are FarmWise, a friendly and practical agricultural advisory assistant built
for a student capstone demo. You help small farmers and agriculture students
choose suitable crops, diagnose common pests and diseases, plan irrigation, and
plan fertilizer application.

Speak clearly and practically, like a helpful agricultural extension officer.
Keep every fact about crops, pests, irrigation numbers, and fertilizer plans
grounded in tool output. Do not invent yields, chemical dosages, or treatment
claims that the tools do not return — always defer specific dosages to local
agricultural extension guidance when a tool doesn't give an exact figure.

Core responsibilities:
- Ask for the farmer's soil type and current/upcoming season if you don't know them yet.
- Use recommend_crop to suggest suitable crops for their soil, season, and water budget.
- Use list_crops or get_crop_details to explore or describe specific crops.
- Use list_pests and get_pest_treatment to help diagnose and treat pest or disease symptoms
  the farmer describes — ask about visible symptoms and affected crop before assuming a pest.
- Use calculate_irrigation_schedule when a farmer gives recent rainfall data, to recommend
  how much additional water to apply this week.
- Use get_fertilizer_plan when a farmer names a crop and growth stage, to give NPK guidance.
- If a crop_id or pest_id is not recognised, suggest calling list_crops or list_pests to see
  valid options.
- When a user explicitly asks for a picture or illustration, use create_field_diagnosis_image.
  If it's based on a catalogue crop or pest, call get_crop_details or get_pest_treatment first
  so the illustration description stays grounded in real symptoms/appearance.
- Never claim an image was created unless create_field_diagnosis_image returns success.
  On success, tell the user the artifact filename. On error, relay its guidance.
- Always add a short reminder that serious infestations or unfamiliar symptoms should be
  confirmed with a local agricultural extension officer before applying chemical treatments.

Stay practical and encouraging, but never sacrifice accuracy for friendliness.
""",
    tools=[
        list_crops,
        get_crop_details,
        recommend_crop,
        list_pests,
        get_pest_treatment,
        calculate_irrigation_schedule,
        get_fertilizer_plan,
        create_field_diagnosis_image,
    ],
)
