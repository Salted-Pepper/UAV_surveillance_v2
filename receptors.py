"""
Receptors track the pheromones for the spread and contain local statistics (e.g. weather conditions) per region
"""
import time

import matplotlib.patches

import constants
import general_maths
from points import Point
from general_maths import calculate_distance

import numpy as np
import matplotlib.pyplot as plt
import math

import os
import logging
import datetime

date = datetime.date.today()
logging.basicConfig(level=logging.DEBUG, filename=os.path.join(os.getcwd(), 'logs/navy_log_' + str(date) + '.log'),
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt="%H:%M:%S")
logger = logging.getLogger("RECEPTORS")
logger.setLevel(logging.DEBUG)


class Receptor:
    def __init__(self, x, y, in_polygon=False) -> None:
        # TODO: Receptors currently only 100 when IN a landmass -> change to territorial waters (input diff polygon)
        #  - also finetune value

        if in_polygon:
            self.pheromones = 100
            self.decay = False
        elif not is_in_area_of_interest(Point(x, y)):
            self.pheromones = 100
            self.decay = False
        else:
            self.pheromones = np.random.uniform(0, 0.1)
            self.decay = True

        self.location = Point(x, y)
        self.in_polygon = in_polygon

        self.patch = None

    def __str__(self):
        return f"Receptor at: {self.location} - with pheromones {self.pheromones}"

    def initiate_plot(self, axes, cmap):
        if not constants.PLOTTING_MODE:
            return axes
        self.patch = matplotlib.patches.Circle((self.location.x, self.location.y),
                                               radius=0.05, color=cmap(self.pheromones / 100),
                                               alpha=0.5, linewidth=None)
        axes.add_patch(self.patch)
        return axes

    def update_plot(self, axes, cmap):
        if not constants.PLOTTING_MODE:
            return
        self.patch.set_facecolor(cmap(self.pheromones / 100))
        self.patch.set_edgecolor(cmap(self.pheromones / 100))
        return axes

    def in_range_of_point(self, point: Point, radius: float) -> bool:
        if point.distance_to_point(self.location) <= radius:
            return True
        else:
            return False


class ReceptorGrid:
    def __init__(self, polygons: list, world) -> None:
        self.receptors = []

        self.max_cols = None
        self.max_rows = None

        self.world = world

        self.polygons = polygons

        self.initiate_grid(polygons)
        self.cmap = plt.get_cmap("Greens")

    def initiate_grid(self, polygons) -> None:
        """
        Creates all receptors in the grid given the settings.
        Initiates the pheromone values (0 for empty, inf for in polygon)
        """
        # Add a frame around the AoI, to ensure UAVs don't just hover the edge
        min_lat = constants.MIN_LAT - constants.LAT_GRID_EXTRA
        max_lat = constants.MAX_LAT + constants.LAT_GRID_EXTRA

        min_lon = constants.MIN_LONG - constants.LONG_GRID_EXTRA
        max_lon = constants.MAX_LONG + constants.LONG_GRID_EXTRA

        num_cols = (max_lon - min_lon) // constants.GRID_WIDTH
        num_rows = (max_lat - min_lat) // constants.GRID_HEIGHT

        self.max_cols = int(np.ceil(num_cols))
        self.max_rows = int(np.ceil(num_rows))

        for row in range(self.max_rows):
            for col in range(self.max_cols):
                x_location = min_lat + row * constants.GRID_HEIGHT
                y_location = min_lon + col * constants.GRID_WIDTH

                in_polygon = general_maths.check_if_point_in_polygons(polygons, Point(x_location, y_location),
                                                                      exclude_edges=False)
                self.receptors.append(Receptor(x=x_location, y=y_location, in_polygon=in_polygon))

    def select_receptors_in_radius(self, point: Point, radius: float) -> list:
        """
        Select all the receptors within a radius of a point.
        Prevents having to cycle through all points by using how the list of receptors was created
        :param point: Point object
        :param radius: Radius around the point
        :return:
        """
        t_0 = time.perf_counter()
        # Adjust radius to an upperbound of the coordinate transformation
        lon_lat_radius = max(radius / 100, constants.GRID_WIDTH / 2)
        # only check receptors in the rectangle of size radius - select receptors in the list based on
        # how the list is constructed.
        x, y = point.x, point.y
        # print(f"Looking for receptors around ({x:.3f},{y:.3f}) with radius {radius}, "
        #       f"max_rows {self.max_rows}, max_cols {self.max_cols}")
        min_x = x - lon_lat_radius
        max_x = x + lon_lat_radius
        min_y = y - lon_lat_radius
        max_y = y + lon_lat_radius

        # see in which rows and columns this rectangle is:
        min_row = int(max(np.floor((min_x - (constants.MIN_LAT - constants.LAT_GRID_EXTRA))
                                   / constants.GRID_HEIGHT), 0))
        max_row = int(min(np.ceil((max_x - (constants.MIN_LAT - constants.LAT_GRID_EXTRA))
                                  / constants.GRID_HEIGHT), self.max_rows))

        min_col = int(max(np.floor((min_y - (constants.MIN_LONG - constants.LONG_GRID_EXTRA))
                                   / constants.GRID_WIDTH), 0))
        max_col = int(min(np.ceil((max_y - (constants.MIN_LONG - constants.LONG_GRID_EXTRA))
                                  / constants.GRID_WIDTH), self.max_cols))

        # num_cols = int(np.ceil(((constants.MAX_LONG + constants.LONG_GRID_EXTRA) -
        #                         (constants.MIN_LONG - constants.LONG_GRID_EXTRA))
        #                        // constants.GRID_WIDTH))

        receptors_in_radius = []
        # logger.debug(f"{min_row=}, {max_row=}, {min_col=}, {max_col=}")
        # print(f"{min_row=}, {max_row=}, {min_col=}, {max_col=}")
        for row_index in range(min_row, max_row):
            for col_index in range(min_col, max_col):
                index = self.max_cols * row_index + col_index
                r = self.receptors[index]

                if r.in_range_of_point(point, radius * constants.RECEPTOR_RADIUS_MULTIPLIER):
                    receptors_in_radius.append(r)

        t_1 = time.perf_counter()
        constants.time_spent_selecting_receptors += (t_1 - t_0)
        return receptors_in_radius

    def depreciate_pheromones(self):
        for receptor in self.receptors:
            if receptor.decay:
                receptor.pheromones = (receptor.pheromones *
                                       constants.PHEROMONE_DEPRECIATION_FACTOR_PER_TIME_DELTA
                                       ** (1/self.world.time_delta))

    def calculate_CoP(self, point: Point, radius: float) -> (float, list):
        """
        Calculates the concentration of pheromones
        :param point:
        :param radius:
        :return:
        """
        # Increase radius of receptors selected by a factor 2 to make more future-proof decisions
        receptors = self.select_receptors_in_radius(point, radius * 2)

        if not is_in_area_of_interest(point):
            return math.inf, receptors

        for polygon in self.polygons:
            if polygon.check_if_contains_point(point, exclude_edges=False):
                return math.inf, receptors

        CoP = 0
        for receptor in receptors:
            CoP += (1 / max(0.1, calculate_distance(a=point, b=receptor.location))) * receptor.pheromones
        # logger.debug(f"Calculated CoP at {point} with rad {radius}: {CoP} - from {len(receptors)} receptors.")
        return CoP, receptors


def is_in_area_of_interest(point: Point) -> bool:
    if constants.MIN_LAT <= point.x <= constants.MAX_LAT and constants.MIN_LONG <= point.y <= constants.MAX_LONG:
        return True
    else:
        return False
