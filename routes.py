import warnings
import matplotlib.axes
from points import Point
from polygons import Polygon

import constants
import general_maths as gm

# ----------------------------------------------- LOGGER SET UP ------------------------------------------------
import logging
import datetime
import os

date = datetime.date.today()
logging.basicConfig(level=logging.DEBUG, filename=os.path.join(os.getcwd(), 'logs/navy_log_' + str(date) + '.log'),
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt="%H:%M:%S")
logger = logging.getLogger("ROUTES")
logger.setLevel(logging.DEBUG)


# --------------------------------------------- END LOGGER SET UP ------------------------------------------------

class Route:
    def __init__(self, points: list, color=None):
        self.points = points
        self.length = 0
        self.calculate_length()
        if color is None:
            self.color = constants.STANDARD_ROUTE_COLOR
        else:
            self.color = color

    def calculate_length(self):
        self.length = 0
        for a, b in zip(self.points, self.points[1:]):
            self.length += gm.calculate_distance(a, b)

    def add_route_to_plot(self, axes: matplotlib.axes.Axes):
        for a, b in zip(self.points, self.points[1:]):
            axes.plot([a.x, b.x], [a.y, b.y], color=self.color, linestyle='dashed')
        return axes


def create_route(point_a: Point, point_b: Point, polygons_to_avoid: list) -> Route:
    """
    Create route from one point to another, avoiding a set of provided polygons
    Point can not be IN one of the provided polygons.
    :param point_a: Start Point
    :param point_b: End Point
    :param polygons_to_avoid: List of polygons to avoid
    :return:
    """
    # logger.debug(f"Creating route from {point_a} to {point_b}")
    route = [point_a, point_b]

    obstacle_on_route = True

    iterations = 0
    while obstacle_on_route:
        obstructed, obstacle, point_k, point_l = line_crosses_any_polygon(polygons_to_avoid, route)
        # logger.debug(f"Rerouting from {point_k} to {point_l}. Is obstructed: {obstructed}")

        if not obstructed:
            obstacle_on_route = False
        else:
            route = reroute_around_obstacle(point_k, point_l, obstacle, route)

        iterations += 1
        if iterations > constants.ITERATION_LIMIT:
            point_k.add_point_to_plot(axes=constants.axes_plot, color="yellow", text="k")
            point_l.add_point_to_plot(axes=constants.axes_plot, color="yellow", text="l")
            obstacle.add_polygon_to_plot(axes=constants.axes_plot, color="black", opacity=0.3)
            Route(route).add_route_to_plot(axes=constants.axes_plot)
            raise TimeoutError(f"Unable to create route from {point_a} to {point_b} "
                               f"around {obstacle}, going through edge: {point_k}, {point_l}")

    shorter_route = gm.maximize_concavity(route, polygons_to_avoid)
    # logger.debug(f"Route is set to {[str(p) for p in shorter_route]}")
    return Route(points=shorter_route)


def line_crosses_any_polygon(polygons_to_avoid: list, route) -> (bool, Polygon, Point, Point):
    for polygon in polygons_to_avoid:
        for p_1, p_2 in zip(route, route[1:]):
            violation = polygon.check_if_line_through_polygon(p_1=p_1, p_2=p_2)
            if violation:
                # logger.debug(f"Line from {p_1} to {p_2} crosses through polygon {[str(p) for p in polygon.points]}")
                return True, polygon, p_1, p_2
    return False, 0, 0, 0


def extract_route_from_convex_hull(k, l, c_h):
    """
    :param k: Starting Point k
    :param l: End Point l
    :param c_h: Convex hull containing the points k and l
    :return:
    """
    # logging.debug(f"Extracting Points {k} and {l} out of {[str(p) for p in c_h]}")
    if l not in c_h:
        Polygon(c_h).add_polygon_to_plot(constants.axes_plot, color="black", opacity=0.35)
        l.add_point_to_plot(constants.axes_plot, color="yellow", text="l")
        k.add_point_to_plot(constants.axes_plot, color="yellow", text="k")
        logger.error(f"Failed extracting route from {str(k)} to {str(l)} out of {[str(c) for c in c_h]}")
        raise IndexError(f"{l} not in {[str(p) for p in c_h]}")
    elif k not in c_h:
        Polygon(c_h).add_polygon_to_plot(constants.axes_plot, color="black", opacity=0.35)
        l.add_point_to_plot(constants.axes_plot, color="yellow", text="l")
        k.add_point_to_plot(constants.axes_plot, color="yellow", text="k")
        logger.error(f"Failed extracting route from {str(k)} to {str(l)} out of {[str(c) for c in c_h]}")
        raise IndexError(f"{k} not in {[str(p) for p in c_h]}")

    if c_h.index(l) > c_h.index(k):
        # Case 1: Simple case, just look at points between the endpoints
        sub_route_1 = [k] + c_h[c_h.index(k) + 1: c_h.index(l)] + [l]

        # Case 2: We go in other direction and then reverse list
        points_to_k = c_h[:c_h.index(k)]
        points_from_l = c_h[c_h.index(l) + 1:]
        sub_route_2 = [l] + points_from_l + points_to_k + [k]
        sub_route_2.reverse()
    elif c_h.index(l) < c_h.index(k):
        # Case 1: Route inbetween points, but reversed as end point is first
        sub_route_1 = [l] + c_h[c_h.index(l) + 1:c_h.index(k)] + [k]
        sub_route_1.reverse()

        # Case 2: Past k to start of l
        sub_route_2 = [k] + c_h[c_h.index(k) + 1:] + c_h[:c_h.index(l)] + [l]
    else:
        raise ValueError("Points on route are identical!")
    option_1 = Route(points=sub_route_1)
    option_2 = Route(points=sub_route_2)

    if option_1.length <= option_2.length:
        # logger.debug(f"Selected route 1: {[str(p) for p in sub_route_1]}")
        return sub_route_1
    else:
        # logger.debug(f"Selected route 2: {[str(p) for p in sub_route_2]}")
        return sub_route_2


def reroute_around_obstacle(point_k, point_l, obstacle: Polygon, route):
    """
    Reroutes path from k to l around the given obstacle
    :param point_k:
    :param point_l:
    :param obstacle:
    :param route:
    :return:
    """
    # logger.debug(f"Rerouting line from {point_k} to {point_l} around \n {obstacle}")

    c_h = create_convex_hull(obstacle=obstacle, points=[point_k, point_l])

    new_sub_route = extract_route_from_convex_hull(point_k, point_l, c_h)

    # Break open route to insert new sub route between points
    # logger.debug(f"Opening up route between {point_k} and {point_l}")
    route_part_1 = route[:route.index(point_k)]
    route_part_2 = route[route.index(point_l) + 1:]

    # logger.debug(f"Inserting route {[str(p) for p in new_sub_route]} "
    #              f"between {[str(p) for p in route_part_1]} "
    #              f"and {[str(p) for p in route_part_2]}")

    if route.index(point_l) - route.index(point_k) != 1:
        point_l.add_point_to_plot(constants.axes_plot, color="yellow", text="l")
        point_k.add_point_to_plot(constants.axes_plot, color="yellow", text="k")
        route.add_route_to_plot(constants.axes_plot)
        raise ValueError(f"Attempting to reroute from non subsequent points at "
                         f"{point_k} at index {route.index(point_k)} "
                         f"and {point_l} at index {route.index(point_l)}! \n"
                         f"route is {[str(p) for p in route]}")

    new_route = route_part_1 + new_sub_route + route_part_2
    # logger.debug(f"Making new route: {[str(point) for point in new_route]}")
    return new_route


def get_points_between_a_b(a: Point, b: Point, polygon: Polygon, inclusive: bool = True) -> list:
    """
    Gets all points between a and b
    :param a:
    :param b:
    :param polygon:
    :param inclusive: if inclusive -> includes the boundaries
    :return:
    """
    try:
        a_location = polygon.points.index(a)
    except ValueError as e:
        a.add_point_to_plot(constants.axes_plot, color="yellow", text="point_a")
        raise ValueError(e)

    try:
        b_location = polygon.points.index(b)
    except ValueError as e:
        b.add_point_to_plot(constants.axes_plot, color="yellow", text="point_b")
        raise ValueError(e)

    all_points = polygon.points
    if a_location > b_location:
        if inclusive:
            points = all_points[a_location:] + all_points[:b_location + 1]
        else:
            points = all_points[a_location + 1:] + all_points[:b_location]
    elif b_location > a_location:
        if inclusive:
            points = all_points[a_location: b_location + 1]
        else:
            points = all_points[a_location + 1: b_location]
    else:
        a.add_point_to_plot(axes=constants.axes_plot, color="yellow")
        raise ValueError(f"Location a and b is the same: {a}, {b}")
    return points


def merge_paths(path_precede: list, path_follow: list, target: Point) -> list:
    """
    Takes two paths to a target point, returns it as one merged path
    :param path_precede:
    :param path_follow:
    :param target:
    :return:
    """
    # First combine the paths - do this by seeing where target point is.
    if path_precede.index(target) == 0:
        start_of_precede = True
    else:
        start_of_precede = False

    if path_follow.index(target) == 0:
        start_of_follow = True
    else:
        start_of_follow = False

    # Now merge the two lists base on the order:
    if start_of_precede and start_of_follow:
        path_precede.reverse()
        path = path_precede + path_follow[1:]

    elif start_of_precede and not start_of_follow:
        path_precede.reverse()
        path_follow.reverse()
        path = path_precede + path_follow[1:]

    elif not start_of_precede and start_of_follow:
        path = path_precede + path_follow[1:]

    elif not start_of_precede and not start_of_follow:
        path_follow.reverse()
        path = path_precede + path_follow[1:]
    else:
        raise NotImplementedError

    # logger.debug(f"Merged path is {[str(p) for p in path]}")
    return path


def insert_path_in_c_h(path, c_h, target):
    preceding_point = path[0]
    following_point = path[-1]

    preceding_index = c_h.index(preceding_point)
    following_index = c_h.index(following_point)

    if preceding_index < following_index:
        points_preceding_first = c_h[preceding_index: following_index + 1]
        points_following_first = c_h[following_index:] + c_h[:preceding_index + 1]
    else:
        points_preceding_first = c_h[preceding_index:] + c_h[:following_index + 1]
        points_following_first = c_h[following_index:preceding_index + 1]

    logger.debug(f"Path is {[str(p) for p in path]}, {preceding_index=}, {following_index=} \n"
                 f"preceding points: {[str(p) for p in points_preceding_first]}, "
                 f"following points: {[str(p) for p in points_following_first]}, "
                 f"C_h is: {[str(p) for p in c_h]}")

    if len(points_following_first) < len(points_preceding_first):
        path.reverse()
        index_point = following_index
        for p in path:
            if p not in c_h:
                c_h.insert(index_point + 1, p)
                # logger.debug(f"Following - Inserted {p} at {index_point + 1} \n C_h is: {[str(p) for p in c_h]}")
                index_point = c_h.index(p)
            else:
                index_point = c_h.index(p)
                # logger.debug(f"Following - {p} already in c_h, setting index to {index_point}")
    else:
        index_point = preceding_index
        for p in path:
            if p not in c_h:
                c_h.insert(index_point + 1, p)
                # logger.debug(f"Preceding - Inserted {p} at {index_point} \n C_h is: {[str(p) for p in c_h]}")
                index_point = c_h.index(p)
            else:
                index_point = c_h.index(p)
                # logger.debug(f"Preceding - {p} already in c_h, setting index to {index_point}")


def re_add_point_to_hull(target: Point, c_h: list, obstacle: Polygon) -> list:
    """
    Takes a convex hull and a target point. Adds the point back into the convex hull (losing convexity)
    :param target:
    :param c_h:
    :param obstacle:
    :return:
    """
    logger.debug(f"READDING {target} to convex hull - {[str(p) for p in c_h]} - obstacle: {[str(p) for p in c_h]}")
    if target in c_h:
        return c_h

    gm.sort_convex_hull(c_h)

    # First find a close reachable point on the polygon
    closest_point = gm.find_closest_reachable_point(target, obstacle)

    # Add any points that are in the convex hull but not in polygon INTO the polygon at a proper place
    # (This is generally the destination/arrival point, part of the convex hull, but not within the hull of the polygon)
    ext_polygon_points = obstacle.points.copy()
    for k, l, m in zip(c_h, c_h[1:] + [c_h[0]], c_h[2:] + c_h[0:2]):
        if l not in obstacle.points:
            # logger.debug(f"Attempting to add {str(l)} between {str(k)} and {str(m)} in polypoints")
            add_point_to_poly_points(obstacle, k, l, m, ext_polygon_points)
    # logger.debug(f"Closest point is {closest_point} --- extracting updated convex hull --- "
    #              f"extended polypoints is {[str(p) for p in ext_polygon_points]}")
    # Find the two convex hull points adjacent to this point
    point_options = []
    for convex_point in c_h:
        if convex_point is closest_point:
            continue
        points_a_to_b = get_points_between_a_b(a=convex_point, b=closest_point,
                                               polygon=Polygon(ext_polygon_points), inclusive=True)
        points_b_to_a = get_points_between_a_b(a=closest_point, b=convex_point,
                                               polygon=Polygon(ext_polygon_points), inclusive=True)
        # logger.debug(f"Convex point {convex_point} - closest point {closest_point}")
        # logger.debug(f"a_to_b: {[str(p) for p in points_a_to_b]}, b_to_a: {[str(p) for p in points_b_to_a]}")
        point_options.append([convex_point, points_a_to_b, "precedes"])
        point_options.append([convex_point, points_b_to_a, "follows"])

    point_options.sort(key=lambda x: len(x[1]))

    # check if point before or after, select closest before and closest after
    before_selected = False
    after_selected = False

    point_precede = None
    point_after = None
    preceding_points = None
    following_points = None
    # logger.debug(f"Point option is {[[str(p[0]), p[2]] for p in point_options]} - target {target}. "
    #              f"c_h is {[str(p) for p in c_h]}")
    for option in point_options:
        min_point, list_of_points, order = option
        # Check more sophisticated if point is before or after (could be at end of list)
        if order == "precedes" and not before_selected:
            # Option is in front, select it
            point_precede = min_point
            preceding_points = list_of_points
            before_selected = True
            # logger.debug(f"Preceding points set at {point_precede} with {[str(p) for p in preceding_points]}")

        if order == "follows" and not after_selected:
            point_after = min_point
            following_points = list_of_points
            after_selected = True
            # logger.debug(f"After points set at {point_after} with {[str(p) for p in following_points]}")

        if before_selected and after_selected:
            break

    if point_precede is None or point_after is None or preceding_points is None or following_points is None:
        raise ValueError(f"{point_precede=}, {point_after=}")

    following_points.reverse()
    # Create the paths from the selected nodes to the target nodes
    path_precede = create_path_along_polygon_between_points(start_point=point_precede, target=target,
                                                            routing_points=preceding_points, obstacle=obstacle)

    path_follow = create_path_along_polygon_between_points(start_point=point_after, target=target,
                                                           routing_points=following_points, obstacle=obstacle)
    logger.debug(f"precede {[str(p) for p in path_precede]}, follow: {[str(p) for p in path_follow]}")
    path = merge_paths(path_precede, path_follow, target)
    insert_path_in_c_h(path, c_h, target)

    logger.debug(f"Returning hull {[str(p) for p in c_h]}")
    return c_h


def create_convex_hull(obstacle: Polygon, points=None) -> list:
    """
    Creates convex hull of set of points and polygons.
    :param obstacle: List of polygons, each entry in the list is a polygon
    :param points: List of points, no point, or single point
    :return:
    """
    if points is None or len(points) == 0:
        all_points = []
    elif isinstance(points, list):
        all_points = points
    elif isinstance(points, Point):
        all_points = [points]
        warnings.warn("create_convex_hull received a single point rather than a list of points")
    else:
        raise TypeError("Unexpected Type For List Of Points")

    for point in all_points:
        # logger.debug(f"Setting points {point} to FORCE-MAINTAIN")
        point.force_maintain = True

    for point in obstacle.points:
        if point not in all_points:
            # logger.debug(f"Adding point {point} to {[str(p) for p in all_points]}")
            all_points.append(point)

    convex_hull = gm.graham_scan(all_points)

    for point in all_points:
        if point.force_maintain and point not in convex_hull:
            convex_hull = re_add_point_to_hull(point, convex_hull, obstacle)

    # logging.debug(f"Returning convex hull {Polygon(convex_hull)}")
    for point in all_points:
        point.force_maintain = False
    return convex_hull


def add_point_to_poly_points(obstacle: Polygon, k: Point, l: Point, m: Point, list_of_points: list):
    """
    Takes points in a convex hull that belong to a polygon.
    For a single added point that is not part of the polygon (points) -
    add it to the polygon at the most suited (closest) location
    :param list_of_points: List of points to insert the missing point into
    :param obstacle:
    :param k:
    :param l:
    :param m:
    :return:
    """
    distances = []
    poly_points = obstacle.points.copy()
    if l not in poly_points:
        points_between_k_and_m = get_points_between_a_b(a=k, b=m, polygon=obstacle)

        # logger.debug(f"Points between k ({k}) and m ({m}) is: {[str(p) for p in points_between_k_and_m]}")
        # Consider all pairs of points between k and m (inclusive),
        # see if we can add point L inbetween and calculate the distance if we can
        for index, a in enumerate(points_between_k_and_m):
            if index < len(points_between_k_and_m) - 1:
                b = points_between_k_and_m[index + 1]
            else:
                b = points_between_k_and_m[0]

            a_obstructed = obstacle.check_if_line_through_polygon(p_1=a, p_2=l)
            b_obstructed = obstacle.check_if_line_through_polygon(p_1=l, p_2=b)
            # logger.debug(f"Checking if we can add {str(l)} between {str(a)} and {str(b)} -"
            #              f" {a_obstructed}, {b_obstructed}")
            if not a_obstructed and not b_obstructed:
                total_dist = l.distance_to_point(a) + l.distance_to_point(b)
                distances.append([[a, b], total_dist])

    else:
        return

    if len(distances) == 0:
        # logger.debug(f"Distances is length 0")
        return

    min_coords = min(distances, key=lambda x: x[1])[0]
    a, b = min_coords

    # Add point l between a and b
    # logging.debug(f"Inserting {str(l)} at index {poly_points.index(b)} (at [{str(b)}])")
    list_of_points.insert(poly_points.index(b), l)


def create_path_along_polygon_between_points(start_point: Point, target: Point,
                                             routing_points: list, obstacle: Polygon) -> list:
    points_to_travel_from = [start_point] + routing_points

    path = []
    # logger.debug(f"Creating path from {start_point} to {target}. Routing points: {[str(p) for p in routing_points]}")
    for point in points_to_travel_from:
        obstructed = obstacle.check_if_line_through_polygon(point, target)
        if obstructed:
            path.append(point)
            # Check if we can remove intermediate points
            if len(path) >= 2:
                path = gm.maximize_concavity(path, [obstacle])

        # if we can reach point, complete the path
        else:
            # logger.debug(f"Able to reach {target} from {point}")
            path.extend([point, target])
            # Check if we can remove intermediate points
            if len(path) >= 2:
                path = gm.maximize_concavity(path, [obstacle])
            return path

    raise NotImplementedError(f"Unable to create path along polygon - {start_point=}, {target=},"
                              f" {[str(p) for p in points_to_travel_from]}")

