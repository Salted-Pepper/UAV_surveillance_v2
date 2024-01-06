# ---- DEBUG PARAMETERS ----
axes_plot = None

ITERATION_LIMIT = 50
DEBUG_MODE = True
PLOTTING_MODE = True

# ---- PERFORMANCE MEASURING ----

time_spent_creating_routes = 0
time_spent_calculating_distance = 0
time_spent_making_patrol_moves = 0
time_spent_observing_area = 0
time_spreading_pheromones = 0
time_spent_updating_trail_route = 0
time_spent_uav_route_move = 0
time_spent_checking_uav_return = 0
time_spent_depreciating_pheromones = 0
time_spent_following_route = 0
time_spent_launching_drones = 0

time_spent_selecting_receptors = 0

# ---- World Constants ----
CARGO_DAILY_ARRIVAL_MEAN = 30
BULK_DAILY_ARRIVAL_MEAN = 30
CONTAINER_DAILY_ARRIVAL_MEAN = 30

MIN_LAT = 110
MAX_LAT = 150

MIN_LONG = 5
MAX_LONG = 50

GRID_WIDTH = 1
GRID_HEIGHT = GRID_WIDTH

PLOT_SIZE = 7

LAT_GRID_EXTRA = 8
LONG_GRID_EXTRA = 8

# ---- Pheromone ----
PHEROMONE_DEPRECIATION_FACTOR_PER_TIME_DELTA = 0.99
RECEPTOR_RADIUS_MULTIPLIER = 10

# ---- GEO Constants ----
EXPANSION_PARAMETER = 0.001      # Parameter to slightly extend polygons to prevent overlaps when selecting a point

LATITUDE_CONVERSION_FACTOR = 110.574
LONGITUDE_CONVERSION_FACTOR = 111.320

STANDARD_ROUTE_COLOR = "red"

# ---- UAV Parameters ----
UAV_HEALTH = 100
MAX_TRAILING_DISTANCE = 0.01

SAFETY_ENDURANCE = 0.1

PATROL_MIN_LAT = 117
PATROL_MAX_LAT = 150

PATROL_MIN_LONG = 10
PATROL_MAX_LONG = 40

UAV_AVAILABILITY = 0.5

MODEL_DICTIONARIES = [{"name": "WLI_GJI",
                       "speed": 210,
                       "vulnerability": 3,
                       "ability_to_target": True,
                       "max_ammunition": 6,
                       "radius": 11,
                       "endurance": 20,
                       "range": 1250,
                       "number_of_airframes": 30},

                      {"name": "WLI_WD1",
                       "speed": 210,
                       "vulnerability": 3,
                       "ability_to_target": True,
                       "max_ammunition": 0,
                       "radius": 11,
                       "endurance": 20,
                       "range": 1250,
                       "number_of_airframes": 45},

                      {"name": "BZK-007",
                       "speed": 210,
                       "vulnerability": 3,
                       "ability_to_target": True,
                       "max_ammunition": 0,
                       "radius": 11,
                       "endurance": 16,
                       "range": 250,
                       "number_of_airframes": 15},

                      {"name": "CH-5",
                       "speed": 210,
                       "vulnerability": 3,
                       "ability_to_target": True,
                       "max_ammunition": 6,
                       "radius": 11,
                       "endurance": 40,
                       "range": 1700,
                       "number_of_airframes": 15},

                      {"name": "BZK-005",
                       "speed": 210,
                       "vulnerability": 2,
                       "ability_to_target": False,
                       "max_ammunition": 0,
                       "radius": 83,
                       "endurance": 40,
                       "range": 2000,
                       "number_of_airframes": 70},

                      {"name": "TB-001",
                       "speed": 210,
                       "vulnerability": 2,
                       "ability_to_target": True,
                       "max_ammunition": 6,
                       "radius": 11,
                       "endurance": 35,
                       "range": 2000,
                       "number_of_airframes": 15},

                      {"name": "WLII",
                       "speed": 210,
                       "vulnerability": 2,
                       "ability_to_target": True,
                       "max_ammunition": 6,
                       "radius": 11,
                       "endurance": 32,
                       "range": 2000,
                       "number_of_airframes": 15},

                      {"name": "WZ-7",
                       "speed": 750,
                       "vulnerability": 1,
                       "ability_to_target": False,
                       "max_ammunition": 0,
                       "radius": 83,
                       "endurance": 10,
                       "range": 2000,
                       "number_of_airframes": 20},

                      {"name": "WLIII",
                       "speed": 210,
                       "vulnerability": 2,
                       "ability_to_target": True,
                       "max_ammunition": 6,
                       "radius": 83,
                       "endurance": 27,
                       "range": 2000,
                       "number_of_airframes": 15},

                      {"name": "WZ-10",
                       "speed": 750,
                       "vulnerability": 2,
                       "ability_to_target": True,
                       "max_ammunition": 6,
                       "radius": 83,
                       "endurance": 10,
                       "range": 2000,
                       "number_of_airframes": 15},

                      {"name": "Y-8",
                       "speed": 210,
                       "vulnerability": 2,
                       "ability_to_target": True,
                       "max_ammunition": 6,
                       "radius": 83,
                       "endurance": 10,
                       "range": 2000,
                       "number_of_airframes": 6},

                      {"name": "Y-9",
                       "speed": 210,
                       "vulnerability": 2,
                       "ability_to_target": True,
                       "max_ammunition": 6,
                       "radius": 83,
                       "endurance": 20,
                       "range": 2000,
                       "number_of_airframes": 7},

                      {"name": "test",
                       "speed": 210,
                       "vulnerability": 2,
                       "ability_to_target": True,
                       "max_ammunition": 0,
                       "radius": 83,
                       "endurance": 30,
                       "range": 2000,
                       "number_of_airframes": 10},

                      {"name": "test-2",
                       "speed": 200,
                       "vulnerability": 2,
                       "ability_to_target": True,
                       "max_ammunition": 4,
                       "radius": 11,
                       "endurance": 40,
                       "range": 2000,
                       "number_of_airframes": 15},
                      ]

# ---- Detection Parameters ----
UAV_MOVEMENT_SPLITS_P_H = 24  # (24 is at least 2 every 5 mins) Splits per hour - gets recalculated per timedelta
PATROL_LOCATIONS = 10

K_CONSTANT = 39_633

# ---- Vessel Constants ----

SHIP_HEALTH = 100

# Cargo Ships
CARGO_AVERAGE_SPEED = 80
CARGO_AVERAGE_LOAD = 1
CARGO_RCS = 1


# Bulk Ships
BULK_AVERAGE_SPEED = 60
BULK_AVERAGE_LOAD = 1
BULK_RCS = 1.25


# Container Ships
CONTAINER_AVERAGE_SPEED = 45
CONTAINER_AVERAGE_LOAD = 1
CONTAINER_RCS = 1.5

# ---- Plotting Constants -----
WORLD_MARKER_SIZE = 7

MERCHANT_COLOR = "forestgreen"
UAV_COLOR = "indianred"
RECEPTOR_COLOR = "green"
