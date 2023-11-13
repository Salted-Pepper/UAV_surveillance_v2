
axes_plot = None

ITERATION_LIMIT = 100

# ---- World Constants ----
CARGO_DAILY_ARRIVAL_MEAN = 30
BULK_DAILY_ARRIVAL_MEAN = 30
CONTAINER_DAILY_ARRIVAL_MEAN = 30

MIN_LAT = 110
MAX_LAT = 150

MIN_LONG = 0
MAX_LONG = 50

GRID_WIDTH = 1
GRID_HEIGHT = GRID_WIDTH

PLOT_SIZE = 7

LAT_GRID_EXTRA = 8
LONG_GRID_EXTRA = 8

# ---- Pheromone ----
PHEROMONE_DEPRECIATION_FACTOR = 0.9

# ---- GEO Constants ----
EXPANSION_PARAMETER = 0.001      # Parameter to slightly extend polygons to prevent overlaps when selecting a point

STANDARD_ROUTE_COLOR = "red"

# ---- UAV Parameters ----
UAV_HEALTH = 100
MAX_TRAILING_DISTANCE = 0.01

SAFETY_ENDURANCE = 0.1

PATROL_MIN_LAT = 117
PATROL_MAX_LAT = 150

PATROL_MIN_LONG = 10
PATROL_MAX_LONG = 40


# ---- Detection Parameters ----
UAV_MOVEMENT_SPLITS = 5  # Splits the last move into n parts, such that the distance is checked on multiple parts
PATROL_LOCATIONS = 10

K_CONSTANT = 39_633

# ---- Vessel Constants ----

SHIP_HEALTH = 100

# Cargo Ships
CARGO_AVERAGE_SPEED = 0.5
CARGO_AVERAGE_LOAD = 1
CARGO_RCS = 1


# Bulk Ships
BULK_AVERAGE_SPEED = 0.7
BULK_AVERAGE_LOAD = 1
BULK_RCS = 1.25


# Container Ships
CONTAINER_AVERAGE_SPEED = 0.4
CONTAINER_AVERAGE_LOAD = 1
CONTAINER_RCS = 1.5

# ---- Plotting Constants -----
WORLD_MARKER_SIZE = 8

MERCHANT_COLOR = "forestgreen"
UAV_COLOR = "indianred"
RECEPTOR_COLOR = "green"
