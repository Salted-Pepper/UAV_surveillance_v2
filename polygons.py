
import matplotlib.axes
import matplotlib.patches
import shapely.geometry
import numpy as np

from points import Point
import general_maths as gm

# ----------------------------------------------- LOGGER SET UP ------------------------------------------------
import logging
import datetime
import os

date = datetime.date.today()
logging.basicConfig(level=logging.DEBUG, filename=os.path.join(os.getcwd(), 'logs/navy_log_' + str(date) + '.log'),
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt="%H:%M:%S")
logger = logging.getLogger("POLYGON")
logger.setLevel(logging.DEBUG)


# --------------------------------------------- END LOGGER SET UP ------------------------------------------------

class Polygon:
    def __init__(self, points: list):
        self.points = points

    def __str__(self):
        point_text = ""
        for point in self.points:
            point_text = point_text + f"{point}, "
        return f"Polygon with points:" + point_text

    def add_polygon_to_plot(self, axes: matplotlib.axes.Axes, color=None, opacity: float = 1) -> matplotlib.axes.Axes:
        if color is None:
            axes.add_patch(matplotlib.patches.Polygon([(p.x, p.y) for p in self.points],
                                                      closed=True, alpha=opacity))
        else:
            axes.add_patch(matplotlib.patches.Polygon([(p.x, p.y) for p in self.points],
                                                      closed=True, color=color, alpha=opacity))
        return axes

    def check_if_contains_point(self, P: Point, exclude_edges=True) -> bool:
        """
        Check if point P is in polygon - excludes the edges
        :param exclude_edges:
        :param P: Point P containing (x, y) coordinates
        :return:
        """
        x = P.x
        y = P.y

        if exclude_edges:
            for a, b in zip(self.points, self.points[1:] + [self.points[0]]):
                if gm.is_between_points(a, b, P):
                    return False

        poly_coordinates = [(p.x, p.y) for p in self.points]
        poly = shapely.geometry.Polygon(poly_coordinates)
        point = shapely.geometry.Point(x, y)
        return point.within(poly)
        # return poly.contains(point)

    def point_is_on_edge(self, target) -> bool:
        for a, b in zip(self.points, self.points[1:] + [self.points[0]]):
            if gm.is_between_points(a, b, target):
                return True
        return False

    def check_if_line_through_polygon(self, p_1: Point = None, p_2: Point = None, line: list = None) -> bool:
        """
        Check if a line L, or a line from P_1 to P_2 is in the given polygon at some point
        :param p_1:
        :param p_2:
        :param line:
        :return:
        """
        # logger.debug(f"Checking if line {p_1} -> {p_2} through polygon {[str(p) for p in self.points]}")
        # Define the points using the input type
        if (p_1 is None or p_2 is None) and line is None:
            raise AttributeError("Not enough valid attributes passed through")
        elif p_1 is None or p_2 is None:
            p_1 = line[0]
            p_2 = line[1]

        # ------------------ CASE 1.1: A POINT IS IN THE POLYGON
        if self.check_if_contains_point(p_1) or self.check_if_contains_point(p_2):
            logger.debug(f"LINE CHECK: CASE 1.1")
            # logger.debug(f"Polygon contains the point "
            #              f"p1 {p_1}: {self.check_if_contains_point(p_1)}, "
            #              f"p2 {p_2}: {self.check_if_contains_point(p_2)}")
            return True
        # ------------------ CASE 1.2 BOTH POINTS ARE THE SAME
        elif p_1 is p_2:
            logger.debug(f"LINE CHECK: CASE 1.2")
            return False
        # ------------------ CASE 1.3 ONE POINT IS A POLYGON POINT, OTHER IS ON AN EDGE OF THE POLYGON
        elif (p_1 in self.points and self.point_is_on_edge(p_2)) or (self.point_is_on_edge(p_1) and p_2 in self.points):
            logger.debug(f"LINE CHECK: CASE 1.3")
            # Check if it's on one edge - if they are on the same edge, it does not violate -
            # if they are on different edges, we check it as usual
            for a, b in zip(self.points, self.points[1:] + [self.points[0]]):
                if p_1 in [a, b] and gm.is_between_points(a, b, tested_point=p_2):
                    return False
                elif p_2 in [a, b] and gm.is_between_points(a, b, tested_point=p_1):
                    return False
                elif gm.is_between_points(a, b, tested_point=p_1) and gm.is_between_points(a, b, tested_point=p_2):
                    return False
            # logger.debug(f"Points not on subsequent edge")
            if not self.check_if_can_connect_edge_points(p_1, p_2):
                return True

        # ------------------ CASE 1.4 BOTH POINTS ARE ON EDGES OF THE POLYGON
        elif self.point_is_on_edge(p_1) and self.point_is_on_edge(p_2):
            logger.debug(f"LINE CHECK: CASE 1.4a")
            # ----------------- CASE 1.4a THE POINTS ARE ON THE SAME EDGE
            for a, b in zip(self.points, self.points[1:] + [self.points[0]]):
                if gm.is_between_points(a, b, tested_point=p_1) and gm.is_between_points(a, b, tested_point=p_2):
                    return False

            # ----------------- CASE 1.4b THE POINTS ARE ON DIFFERENT EDGES
            logger.debug(f"LINE CHECK: CASE 1.4b")
            if not self.check_if_can_connect_edge_points(p_1, p_2):
                return True

        # ----------------- CASE 2: BOTH POINTS ARE ON THE POLYGON
        if p_1 in self.points and p_2 in self.points:
            # --------------- CASE 2.1: WE TRAVERSE AN EDGE
            logger.debug(f"LINE CHECK: CASE 2.1")
            for a, b in zip(self.points, self.points[1:] + [self.points[0]]):
                if p_1 is a and p_2 is b:
                    return False
                elif p_1 is b and p_2 is a:
                    return False

            # --------------------- CASE 2.2: WE JUMP PAST A POINT - TEST IF FEASIBLE
            logger.debug(f"LINE CHECK: CASE 2.2")
            if not self.check_if_can_connect_edge_points(p_1, p_2):
                return True
            return False
        else:
            # --------------------- CASE 3: WE CROSS THE POLYGON
            logger.debug(f"LINE CHECK: CASE 3")
            for a, b in zip(self.points, self.points[1:] + [self.points[0]]):
                logger.debug(f"Checking line from {a} to {b}: {gm.check_if_lines_intersect([a, b], [p_1, p_2])}")
                # Check if there is any line that the line intersects
                if gm.check_if_lines_intersect([a, b], [p_1, p_2]):
                    # logger.debug(f"Intersection between line ({a}, {b}) and line ({p_1}, {p_2})")
                    return True

        # ----------------- CASE 4: WE DO NOT INTERACT WITH THE POLYGON
        logger.debug(f"LINE CHECK: CASE 4")
        return False

    def check_if_can_connect_edge_points(self, p_1, p_2):
        """
        Checks if we can connect two points on the edges
        :param p_1:
        :param p_2:
        :return:
        """
        # TODO: Make this less resource intensive

        for lamb in np.arange(0.01, 1, 0.01):
            if self.check_if_contains_point(
                    Point(p_1.x * lamb + p_2.x * (1 - lamb), p_1.y * lamb + p_2.y * (1 - lamb))):
                # logger.debug(f"{Point(p_1.x * lamb + p_2.x * (1 - lamb), p_1.y * lamb + p_2.y * (1 - lamb))} "
                #              f"is in the polygon")
                return False
        # logger.debug(f"{p_1} and {p_2} both in polygon. Does not cross polygon.")
        return True

    def order_points(self):
        """
        This function is purely for testing purposes to create random polygons.
        :return:
        """
        starting_point = gm.find_lowest_point_in_polygon(self.points)
        self.points.remove(starting_point)
        self.points.sort(key=lambda p: gm.calculate_polar_angle(starting_point, p))
        self.points.insert(0, starting_point)
