from types import SimpleNamespace

from app.impact_logic import calculate_dynamic_radius


def test_waste_vector_risk_is_indirect_vigilance_not_direct_radius():
    ai_data = SimpleNamespace(
        macro_category="Déchets & Insalubrité",
        sub_category="Accumulation d'ordures",
        source_size_meters=8.0,
        spread_vectors=["vectors_insects_rodents"],
    )

    result = calculate_dynamic_radius(
        ai_data=ai_data,
        spatial_data={
            "temperature_celsius": 25.0,
            "precipitation": 0.0,
            "wind_speed": 0.0,
            "slope_percent": 0.0,
        },
        macro_osm_counts={"residential_buildings": 0},
        sat_data={"land_use": "Urbain / Bâti"},
    )

    assert result["final_radius"] == 25.0
    assert result["indirect_vigilance"]["potential_radius"] == 125
    assert result["indirect_vigilance"]["vector"] == "Insectes / Rongeurs"
