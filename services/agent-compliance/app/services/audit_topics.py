"""Building-type/height-aware audit topic selection.

Used two ways: (1) each selected topic becomes its own retrieval query,
so an audit fetches regulation text across exactly the topics relevant
to THIS building instead of one fixed list applied to every building
regardless of type; (2) the same list is rendered into the compliance
prompt so Gemini must produce exactly one check per selected topic, in
order — this is what makes the number and kind of checks reproducible
across runs of the same building, instead of depending on which chunks
a query happened to return.

Thresholds below (30m/60m for High-Rise/Super High-Rise, Purpose Group
6/7 for storage-industrial) were verified directly against the
regulation text's own definitions chapter, not assumed — see the
Horizon Business Tower investigation for the exact chunks confirming
each one.
"""

CORE_TOPICS: list[tuple[str, str]] = [
    ("means_of_escape_exits", "minimum number of independent exits required per storey based on occupant load and floor area"),
    ("means_of_escape_exit_width", "minimum and maximum clear width requirements for exit doors"),
    ("travel_distance", "maximum permissible one-way and two-way travel distance in metres by occupancy risk profile and fire growth rate"),
    ("dead_end_corridor", "maximum dead-end corridor or passage travel distance limits"),
    ("compartmentation_general", "maximum compartment floor area and cubic volume size limits for buildings in general, based on height above ground and number of storeys"),
    ("sprinklers", "automatic sprinkler system requirements based on building height and storage of combustible goods"),
    ("detection_alarm", "manual call points and automatic fire detection and alarm system requirements"),
    ("extinguishers", "portable fire extinguisher siting, rating, and maximum travel distance to an extinguisher"),
    ("hose_reels", "hydraulic hose reel system requirements"),
    ("hydrants", "external pillar fire hydrant requirements"),
    ("structural_fire_resistance", "minimum period of fire resistance for elements of structure"),
    ("hazard_classification", "occupancy hazard classification (Light Hazard, Ordinary Hazard Group I to IV, or High Hazard) used specifically for automatic sprinkler system design density and water supply — distinct from the building's Purpose Group occupancy type"),
    # Applies to every building regardless of type or size — Reg. 7(3)'s
    # table has an entry for every floor-area/height combination, not
    # just large buildings.
    ("fire_engine_access", "percentage of building perimeter requiring vehicle access for pump and high reach appliances by total floor area and height of top storey"),
    # Applies to every building — Reg. 2(53) exempts only Purpose Group
    # 1(c); every other occupancy needs emergency lighting/exit signage
    # regardless of height. Chapter 2, so the Chapter-6-scoped
    # occupancy-specific retrieval never reaches it on its own.
    ("emergency_lighting", "emergency lighting and exit signage requirements including minimum illumination level, battery changeover time, and backup duration"),
    # Deliberately in CORE, not HIGH_RISE_TOPICS: Reg. 4(20)(a)(i) also
    # mandates voice evacuation for large/high-occupancy buildings
    # (floor area or occupant load thresholds) independent of height, so
    # a large low-rise assembly building needs this check too, not just
    # high-rises.
    ("voice_evacuation", "one-way emergency voice evacuation and communication system requirements based on building height, floor area, or occupant load"),
]

# Gated on occupancy_purpose_group in (6, 7) — Table 7's compartment
# limits are specific to Industrial/Factories and Storage occupancies,
# on top of (not instead of) the general Table 6 limits in CORE_TOPICS.
STORAGE_INDUSTRIAL_TOPICS: list[tuple[str, str]] = [
    ("compartmentation_storage", "maximum compartment floor area limits specific to industrial and storage occupancy buildings, based on height above ground and sprinkler protection"),
]

# Gated on height_m > HIGH_RISE_THRESHOLD_M (30m, per the regulation's
# own definitions chapter).
HIGH_RISE_TOPICS: list[tuple[str, str]] = [
    ("stairway_pressurization", "pressurization system requirements for fire escape stairways in high-rise and super high-rise buildings"),
    ("smoke_control", "mechanical smoke control or smoke purging system requirements for high-rise and super high-rise buildings"),
    ("firemans_lift", "fireman's lift requirements including protected shaft, fire-fighting lobby, car dimensions, rated load, and power supply"),
    ("fire_fighting_shaft_fcc", "fire-fighting shaft and Fire Command Centre requirements for high-rise and super high-rise buildings"),
    ("two_way_telephone", "two-way telephone communication system requirements connecting the Fire Command Centre to fire-fighting lobbies, the fire pump room, and the fire service lift"),
    ("wet_risers", "wet riser system requirements including number of risers, floor area coverage, and landing valve travel distance"),
    ("fire_pump_room", "location of fire pumps protected from surrounding occupancies by fire-rated construction or physically separated from the building"),
]

# Gated on height_m > SUPER_HIGH_RISE_THRESHOLD_M (60m, per the
# regulation's own definitions chapter).
SUPER_HIGH_RISE_TOPICS: list[tuple[str, str]] = [
    ("refuge_floor", "refuge floor and holding area requirements for super high-rise buildings"),
    ("evacuation_lift", "evacuation lift requirements for super high-rise buildings"),
]

# Gated on has_basement_car_park — Reg. 6(53)(a) applies to ANY basement
# or enclosed car park unconditionally, no size/ventilation qualifier.
BASEMENT_CAR_PARK_TOPICS: list[tuple[str, str]] = [
    ("co_detection", "carbon monoxide detection system requirements for basement and enclosed car parks"),
]

# Used INSTEAD OF (never alongside) every occupied-building topic above
# when construction_status == "under_construction" — a building actively
# being built is governed by a separate, self-contained set of
# provisions (Reg. 5(31), Reg. 4(27)-4(28)), not the occupied-building
# checklist. Applying the occupied-building checklist to an active site
# produces false violations (no permanent sprinklers/detection/hose
# reels yet, because none of that is required until the building is
# actually complete); applying this list to a finished building would
# under-check it. See select_topics() for the branch.
CONSTRUCTION_TOPICS: list[tuple[str, str]] = [
    ("construction_rising_main", "type of rising main (dry or wet) required for a building under construction based on current habitable floor height, and the height threshold for switching from dry to wet"),
    ("construction_breeching_inlets", "breeching inlet requirements for a building under construction, including number and connection to the rising main per the approved plan"),
    ("construction_vehicle_access", "minimum vehicle access width and overhead clearance required to a breeching inlet on a construction site"),
    ("construction_extinguishers", "portable fire extinguisher coverage requirements per floor level for a building under construction"),
    ("construction_landing_valves", "landing valve connection requirements for a building under construction, including any exception for the topmost floors still being completed"),
    ("construction_water_tank", "temporary fire water storage tank requirements for a building under construction, including capacity and the height by which it must be in place"),
    ("construction_pump_capacity", "minimum fire pump flow rate and pressure requirements at the highest hydrant for a building under construction"),
    ("construction_responsibility", "responsibility for provision and maintenance of fire-fighting facilities during construction"),
    ("construction_water_supply", "requirement that the fire-fighting water supply on a construction site be independent of other site water services"),
    ("construction_siren", "manually operated or hand-crank fire alarm/siren requirements for construction workers on site"),
    ("construction_site_lighting", "emergency evacuation access path and lighting requirements for a construction site, including during night-shift work"),
]

HIGH_RISE_THRESHOLD_M = 30.0
SUPER_HIGH_RISE_THRESHOLD_M = 60.0
STORAGE_INDUSTRIAL_PURPOSE_GROUPS = (6, 7)


def select_topics(building) -> list[tuple[str, str]]:
    """building is a BuildingContext, typed loosely here to avoid a
    schemas<->audit_topics import cycle risk as this module grows."""
    if getattr(building, "construction_status", "completed") == "under_construction":
        return list(CONSTRUCTION_TOPICS)

    topics = list(CORE_TOPICS)

    if building.occupancy_purpose_group in STORAGE_INDUSTRIAL_PURPOSE_GROUPS:
        topics += STORAGE_INDUSTRIAL_TOPICS

    if building.height_m is not None and building.height_m > HIGH_RISE_THRESHOLD_M:
        topics += HIGH_RISE_TOPICS
    if building.height_m is not None and building.height_m > SUPER_HIGH_RISE_THRESHOLD_M:
        topics += SUPER_HIGH_RISE_TOPICS

    if building.has_basement_car_park:
        topics += BASEMENT_CAR_PARK_TOPICS

    return topics


def render_checklist(topics: list[tuple[str, str]]) -> str:
    return "\n".join(f"{i + 1}. {desc}" for i, (_, desc) in enumerate(topics))
