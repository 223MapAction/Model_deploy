from app.services.spatial_calculator import (
    calculate_human_impact,
    calculate_social_vulnerability,
    estimate_urban_buildings_from_radius,
)


def test_urban_building_estimation_scales_with_radius():
    small_radius_buildings = estimate_urban_buildings_from_radius(200)
    large_radius_buildings = estimate_urban_buildings_from_radius(500)

    assert small_radius_buildings == 151
    assert large_radius_buildings > small_radius_buildings


def test_probabilistic_human_impact_changes_with_radius():
    small_osm = {"residential_buildings": 0}
    large_osm = {"residential_buildings": 0}

    small_social = calculate_social_vulnerability(
        small_osm,
        land_use="Urbain / Bâti",
        radius_meters=200,
    )
    large_social = calculate_social_vulnerability(
        large_osm,
        land_use="Urbain / Bâti",
        radius_meters=500,
    )

    small_human = calculate_human_impact(
        small_osm,
        estimated_buildings=small_social["estimated_buildings"],
    )
    large_human = calculate_human_impact(
        large_osm,
        estimated_buildings=large_social["estimated_buildings"],
    )

    assert small_human["total_population_exposed"] != 975
    assert large_human["total_population_exposed"] > small_human["total_population_exposed"]
