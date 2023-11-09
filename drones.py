import matplotlib.patches
import numpy as np
import math
import copy

import constants
from points import Point
from routes import create_route
from general_maths import calculate_distance, calculate_direction_vector
from ships import Ship

import os
import logging
import datetime

date = datetime.date.today()
logging.basicConfig(level=logging.DEBUG, filename=os.path.join(os.getcwd(), 'logs/navy_log_' + str(date) + '.log'),
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt="%H:%M:%S")
logger = logging.getLogger("UAV")
logger.setLevel(logging.DEBUG)

uav_id = 0


class Drone:
    def __init__(self, model, world, airbase):
        # General properties

        global uav_id
        self.uav_id = uav_id
        uav_id += 1
        self.location = copy.deepcopy(airbase.location)
        self.base = airbase
        self.world = world
        self.polygons_to_avoid = world.polygons

        self.direction = "east"
        self.time_spent_airborne = 0

        self.routing_to_start = False
        self.routing_to_base = False
        self.route = None

        self.last_location = None

        self.past_points = []
        self.next_point = None
        self.remaining_points = None

        self.patrolling = False
        self.trailing = False
        self.located_ship = None
        self.grounded = True

        self.under_maintenance = False
        self.estimated_finish_maintenance = None

        self.health_points = 100

        self.name = model

        # Model inherited properties
        # TODO: Tweak pheromone spread and make it model dependent
        # CONSIDER IF WE MAKE IT DIFFERENT TYPES OF PHEROMONES OR QUANTITIES
        self.pheromone_spread = 100

        self.speed = None
        self.radius = None
        self.endurance = None
        self.range = None
        self.vulnerability = None
        self.ability_to_target = None
        self.ammunition = None
        self.max_ammunition = None
        self.height = None

        self.make(model=model)

        # Plotting properties
        self.marker = None
        self.radius_patch = None
        self.ax = world.ax
        self.text = None

    def __str__(self):
        return f"Drone {self.uav_id} at {self.location}. Status: Grounded? {self.grounded}, Trailing? {self.trailing}"

    def make(self, model: str) -> None:
        logger.debug(f"Initiating drone of type {model}.")
        if model == "WLI_GJ1":
            self.speed = 210
            self.vulnerability = 3
            self.ability_to_target = True
            self.max_ammunition = 6
            self.radius = 11
            self.endurance = 20
            self.range = 1250
        elif model == "WLI_WD1":
            self.speed = 210
            self.vulnerability = 3
            self.ability_to_target = True
            self.max_ammunition = 0
            self.radius = 11
            self.endurance = 20
            self.range = 1250
        elif model == "BZK-007":
            self.speed = 210
            self.vulnerability = 3
            self.ability_to_target = True
            self.max_ammunition = 0
            self.radius = 11
            self.endurance = 16
            self.range = 250
        elif model == "CH-4":
            self.speed = 210
            self.vulnerability = 3
            self.ability_to_target = True
            self.max_ammunition = 6
            self.radius = 11
            self.endurance = 40
            self.range = 1700
        elif model == "BZK-005":
            self.speed = 210
            self.vulnerability = 2
            self.ability_to_target = False
            self.max_ammunition = 0
            self.radius = 83
            self.endurance = 40
            self.range = 2000
        elif model == "TB-001":
            self.speed = 210
            self.vulnerability = 2
            self.ability_to_target = True
            self.max_ammunition = 6
            self.radius = 11
            self.endurance = 35
            self.range = 2000
        elif model == "WLII":
            self.speed = 210
            self.vulnerability = 2
            self.ability_to_target = True
            self.max_ammunition = 6
            self.radius = 11
            self.endurance = 32
            self.range = 2000
        elif model == "WZ-7":
            self.speed = 750
            self.vulnerability = 1
            self.ability_to_target = False
            self.max_ammunition = 0
            self.radius = 83
            self.endurance = 10
            self.range = 2000
        elif model == "WLIII":
            self.speed = 210
            self.vulnerability = 2
            self.endurance = 27
            self.radius = 83
            self.max_ammunition = 6
            self.range = 2000
        elif model == "WZ-10":
            self.speed = 750
            self.vulnerability = 2
            self.endurance = 10
            self.radius = 83
            self.max_ammunition = 6
            self.range = 2000
        elif model == "Y-8":
            self.speed = 210
            self.vulnerability = 2
            self.endurance = 10
            self.radius = 83
            self.max_ammunition = 6
            self.range = 2000
        elif model == "Y-9":
            self.speed = 210
            self.vulnerability = 2
            self.endurance = 20
            self.radius = 83
            self.max_ammunition = 6
            self.range = 2000
        elif model == "test":
            self.speed = 1
            self.vulnerability = 2
            self.endurance = np.random.uniform(150, 300)
            self.radius = 1
            self.max_ammunition = 0
            self.range = 2000

    def can_continue(self):
        """
        See if UAV can continue current action or has to return
        :return:
        """
        logger.debug(f"Testing if UAV {self.uav_id} has to return.")
        if self.location.x == self.base.location.x and self.location.y == self.base.location.y:
            return True

        remaining_endurance = self.endurance - self.time_spent_airborne

        logger.debug(f"Creating route to base for UAV {self.uav_id} at ({self.location.x}, {self.location.y}) "
                     f"from {self.location} to {self.base.location}")
        base_route = create_route(self.location, self.base.location, self.polygons_to_avoid)
        time_required_to_return = np.ceil(base_route.length / self.speed)

        logger.debug(f"UAV {self.uav_id} - remaining endurance: {remaining_endurance}, "
                     f"time to return: {time_required_to_return}")

        if remaining_endurance - self.endurance * constants.SAFETY_ENDURANCE <= time_required_to_return:
            return False
        else:
            return True

    def move(self):
        """
        Make the move for the current time step.
        Depends on if they are travelling to a destination (base/start point), patrolling, or trailing.
        :return:
        """
        logger.debug(f"Moving UAV {self.uav_id} --- to start: {self.routing_to_start}, "
                     f"to base: {self.routing_to_base}, "
                     f"trailing? : {self.trailing}")
        distance_to_travel = self.speed * self.world.time_delta
        self.last_location = copy.deepcopy(self.location)
        if not self.can_continue() and not self.routing_to_base:
            self.return_to_base()
            self.time_spent_airborne += self.world.time_delta
            return

        self.time_spent_airborne += self.world.time_delta
        if self.routing_to_start or self.routing_to_base or self.trailing:
            if self.trailing:
                self.update_trail_route()
            self.move_through_route(distance_to_travel)

            if self.trailing:
                self.call_action_on_ship(self.located_ship)
        else:
            self.make_next_patrol_move(distance_to_travel)

        # Check if drone is in legal location
        for polygon in self.world.polygons:
            if polygon.check_if_contains_point(P=self.location, exclude_edges=True):
                self.location.add_point_to_plot(axes=constants.axes_plot, color="yellow")
                self.last_location.add_point_to_plot(axes=constants.axes_plot, color="purple", text="LAST")
                self.next_point.add_point_to_plot(axes=constants.axes_plot, color="black", text="NEXT")
                for p in self.past_points:
                    p.add_point_to_plot(axes=constants.axes_plot, color="black", text=p.point_id)
                if self.route is not None:
                    self.route.add_route_to_plot(axes=constants.axes_plot)
                raise PermissionError(f"UAV {self.uav_id} at illegal location: "
                                      f"({self.location.x: .3f}, {self.location.y: .3f}). \n"
                                      f"Route is {[str(p) for p in self.route.points]} "
                                      f"to start: {self.routing_to_start}, "
                                      f"last point: {self.last_location} "
                                      f"to base: {self.routing_to_base}, "
                                      f"trailing? : {self.trailing}. "
                                      f"Last location = ({self.last_location.x}, {self.last_location.y}). \n"
                                      f"this falls in polygon {[str(p) for p in polygon.points]}")

    def make_next_patrol_move(self, distance_to_travel):
        left_direction = self.report_new_direction("left")
        right_direction = self.report_new_direction("right")
        turn_direction = self.report_new_direction("turn")

        logger.debug(f"Making patrol move for {self.uav_id} - current direction: {self.direction}.   "
                     f"left: {left_direction}, right: {right_direction}")

        left_point = self.move_in_direction(distance_to_travel, direction=left_direction)
        CoP_left, left_receptors = self.world.receptor_grid.calculate_CoP(left_point, self.radius)

        straight_point = self.move_in_direction(distance_to_travel, direction=self.direction)
        CoP_straight, straight_receptors = self.world.receptor_grid.calculate_CoP(straight_point, self.radius)

        right_point = self.move_in_direction(distance_to_travel, direction=right_direction)
        CoP_right, right_receptors = self.world.receptor_grid.calculate_CoP(right_point, self.radius)

        logger.debug(f"{CoP_left=}, {CoP_straight=}, {CoP_right=}")
        CoPs = [CoP_left, CoP_straight, CoP_right]
        probabilities = [1 / CoP for CoP in CoPs]
        if sum(probabilities) != 0:
            probabilities = [p / sum(probabilities) for p in probabilities]
        else:
            logger.warning(f"No Valid probabilities")
            probabilities = [1 / len(probabilities)] * len(probabilities)

        if all([math.isinf(CoP_left), math.isinf(CoP_straight), math.isinf(CoP_right)]):
            direction = "turn"
        else:
            direction = np.random.choice(["left", "straight", "right"], 1, p=probabilities)

        logger.debug(f"Direction probabilities is left:{probabilities[0]:.2f}, "
                     f"straight:{probabilities[1]:.2f}, right:{probabilities[2]:.2f}, ")

        if direction == "left":
            new_location = self.move_in_direction(distance_to_travel, direction=left_direction)
            logger.debug(f"UAV {self.uav_id} Moving left towards {left_direction} - "
                         f"from {self.location} to  {new_location}")
            self.direction = left_direction
        elif direction == "straight":
            new_location = self.move_in_direction(distance_to_travel, direction=self.direction)
            logger.debug(f"UAV {self.uav_id} Moving straight towards {self.direction} - "
                         f"from {self.location} to  {new_location}")
        elif direction == "right":
            new_location = self.move_in_direction(distance_to_travel, direction=right_direction)
            logger.debug(f"UAV {self.uav_id} Moving right towards {right_direction} - "
                         f"from {self.location} to  {new_location}")
            self.direction = right_direction
        else:
            new_location = self.move_in_direction(distance_to_travel, direction=turn_direction)
            logger.debug(f"UAV {self.uav_id} Turning around - from {self.location} to {new_location}")
            self.direction = turn_direction

        self.location = copy.deepcopy(new_location)
        self.location.name = f"UAV {self.uav_id}"
        for polygon in self.world.polygons:
            if polygon.check_if_contains_point(self.location):
                raise PermissionError(f"UAV {self.uav_id} went from ({self.last_location.x}, {self.last_location.y}) "
                                      f"to ({self.location.x}, {self.last_location.y}) "
                                      f"which is in a polygon - {self.trailing=}, {self.routing_to_base=}"
                                      f"{self.routing_to_start=}, {self.patrolling=}")
        self.spread_pheromones()

    def report_new_direction(self, change) -> str:
        if change == "left":
            if self.direction == "north":
                return "west"
            elif self.direction == "east":
                return "north"
            elif self.direction == "south":
                return "east"
            else:
                return "south"
        elif change == "straight":
            return self.direction
        elif change == "right":
            if self.direction == "north":
                return "east"
            elif self.direction == "east":
                return "south"
            elif self.direction == "south":
                return "west"
            else:
                return "north"
        elif change == "turn":
            if self.direction == "north":
                return "south"
            elif self.direction == "east":
                return "west"
            elif self.direction == "south":
                return "north"
            else:
                return "east"
        else:
            raise ValueError(f"Unexpected change {change}")

    def move_in_direction(self, distance_to_travel, direction=None) -> Point:
        """
        Used to explore move in POTENTIAL direction
        :param distance_to_travel: Distance to travel in KM
        :param direction: N/E/S/W direction
        :return: New point of arrival
        """
        x, y = self.location.location()

        if direction is None:
            direction = self.direction

        if direction == "north":
            return Point(x, y + distance_to_travel)
        elif direction == "east":
            return Point(x + distance_to_travel, y)
        elif direction == "south":
            return Point(x, y - distance_to_travel)
        elif direction == "west":
            return Point(x - distance_to_travel, y)
        elif direction == "reverse":
            return Point(x - distance_to_travel, y)
        else:
            raise ValueError(f"Invalid direction {direction}")

    def move_through_route(self, distance_to_travel) -> None:
        chasing = self.trailing
        iterations = 0
        while distance_to_travel > 0 and (self.routing_to_start or self.routing_to_base or chasing):
            iterations += 1
            if iterations > constants.ITERATION_LIMIT:
                if self.route is not None:
                    print(f"Route: {[str(p) for p in self.route.points]}")
                    self.next_point.add_point_to_plot(constants.axes_plot, color="yellow", text="next")
                self.location.add_point_to_plot(constants.axes_plot, color="yellow", text="L")
                raise TimeoutError(f"Distance travel not converging for UAV {self.uav_id} at {self.location} "
                                   f"({self.location.x}, {self.location.y}). \n "
                                   f"- remaining dis: {distance_to_travel}, {self.routing_to_base=}, "
                                   f"{self.routing_to_start=}, {chasing=} "
                                   f"- Vessel being chased: {self.located_ship.ship_id}")

            if self.trailing and calculate_distance(a=self.location, b=self.located_ship.location) < 0.01:
                # Chasing sees if we still have to catch up with the vessel, otherwise the UAV trails it.
                return

            logger.debug(f"UAV {self.uav_id} travelling from "
                         f"{self.location} ({self.location.x: .3f}, {self.location.y: .3f}) "
                         f"to {self.next_point} ({self.next_point.x, self.next_point.y}) ")
            direction_vector = calculate_direction_vector(self.location, self.next_point)

            logger.debug(f"- dir vector is {np.around(direction_vector, 2)} - dist to travel {distance_to_travel}")
            distance_to_next_point = self.location.distance_to_point(self.next_point)
            distance_travelled = min(distance_to_travel, distance_to_next_point)
            distance_to_travel -= distance_travelled
            logger.debug(f"Next point {self.next_point}. Dist to next point {distance_to_next_point: .3f}, "
                         f"distance travelled {distance_travelled}")

            if distance_to_next_point <= distance_travelled:
                self.past_points.append(self.next_point)
                self.location = copy.deepcopy(self.next_point)
                if len(self.remaining_points) > 0:
                    self.next_point = self.remaining_points.pop(0)
                else:
                    self.reached_end_of_route()
                logger.debug(
                    f"UAV {self.uav_id} has {distance_to_travel} remaining - next point {self.next_point}, "
                    f"location is {self.location.x, self.location.y}")
            else:
                logger.debug(f"UAV {self.uav_id} moved from {self.location.x: .3f}, {self.location.y: .3f}")
                self.location.x += distance_travelled * direction_vector[0]
                self.location.y += distance_travelled * direction_vector[1]
                logger.debug(f"to {self.location.x: .3f}, {self.location.y: .3f}")

        self.spread_pheromones()

    def spread_pheromones(self):
        locations = []
        for lamb in np.arange(0, 1, 1 / constants.UAV_MOVEMENT_SPLITS):
            x_loc = self.location.x * lamb + self.last_location.x * (1 - lamb)
            y_loc = self.location.y * lamb + self.last_location.y * (1 - lamb)
            locations.append(Point(x_loc, y_loc))

        for location in locations:
            receptors = self.world.receptor_grid.select_receptors_in_radius(location, radius=self.radius)

            for receptor in receptors:
                if receptor.decay:  # To Check if receptor is not a boundary point
                    receptor.pheromones += ((1 / max(location.distance_to_point(receptor.location), 0.1)) *
                                            (self.pheromone_spread / constants.UAV_MOVEMENT_SPLITS))
                    receptor.update_plot(self.world.ax, self.world.receptor_grid.cmap)

    def reached_end_of_route(self) -> None:
        if self.routing_to_start:
            self.routing_to_start = False
            self.patrolling = True
            logger.debug(f"UAV {self.uav_id} arrived at start of patrol ({self.location})")
        elif self.routing_to_base:
            self.routing_to_base = False
            self.land()
            logger.debug(f"UAV {self.uav_id} arrived back at base ({self.location})")
        elif self.trailing:
            pass

    def observe_area(self, ships):
        for ship in ships:
            detection_probabilities = []

            radius_travelled = self.radius + self.speed * self.world.time_delta

            if calculate_distance(a=self.location, b=ship.location) > radius_travelled:
                continue

            if len(ship.trailing_UAVs) > 0:
                continue

            for lamb in np.append(np.arange(0, 1, step=1 / constants.UAV_MOVEMENT_SPLITS), 1):
                uav_location = Point(self.location.x * lamb + self.last_location.x * (1 - lamb),
                                     self.location.y * lamb + self.last_location.y * (1 - lamb))
                if calculate_distance(a=uav_location, b=ship.location) <= self.radius:
                    detection_probabilities.append(self.roll_detection_check(uav_location, ship))
            probability = 1 - np.prod([(1 - p) ** (1 / constants.UAV_MOVEMENT_SPLITS) for p in detection_probabilities])
            if np.random.rand() <= probability:
                logger.debug(f"UAV {self.uav_id} detected {ship.ship_id} - w/ prob {probability}.")
                if not self.routing_to_base:
                    self.detected(ship)
                return
            else:
                logger.debug(f"UAV {self.uav_id} missed {ship.ship_id} - detect prob {probability}.")

    @staticmethod
    def roll_detection_check(uav_location, ship: Ship) -> float:
        distance = calculate_distance(a=uav_location, b=ship.location)

        # TODO: Add weather parameter
        weather = 0.5  # To implement - see sea state in drive file.
        height = 10  # Assumed to be 10km
        top_frac_exp = constants.K_CONSTANT * height * ship.RCS * weather
        if distance < 1:
            distance = 1
        delta = 1 - math.exp(-top_frac_exp / ((distance * 110) ** 3))
        return delta

    def detected(self, ship: Ship):
        self.patrolling = False
        self.trailing = True
        ship.trailing_UAVs.append(self)
        self.located_ship = ship
        self.update_trail_route()

    def update_trail_route(self):
        # TODO: Make this territorial waters to avoid rather than world polygons
        # TODO: Fix issue where UAV trails through landmass

        if self.located_ship is not None:
            if self.located_ship.reached_destination:
                logger.debug(f"UAV {self.uav_id} is forced to stop chasing {self.located_ship.ship_id}.")
                self.stop_trailing()
                return

            for polygon in self.world.polygons:
                if polygon.check_if_contains_point(self.located_ship.location):
                    logger.debug(f"UAV {self.uav_id} is forced to stop chasing {self.located_ship.ship_id}.")
                    self.stop_trailing()
                    return

        self.generate_route(destination=self.located_ship.location)

    def stop_trailing(self):
        if self.trailing:
            self.trailing = False
            self.located_ship.trailing_UAVs.remove(self)
            self.located_ship = None
            # If it is illegal to chase, give up, start patrolling the area instead
            self.make_next_patrol_move(self.speed * self.world.time_delta)
        else:
            logger.warning(f"UAV {self.uav_id} was not trailing - ordered to stop")

    def call_action_on_ship(self, ship):
        pass

    def launch(self, world):
        world.current_airborne_drones.append(self)
        self.grounded = False
        start_location = self.generate_patrol_location()
        start_location.name = "Start Location"
        logger.debug(f"Launching UAV {self.uav_id} to {start_location}")
        self.generate_route(start_location)
        self.routing_to_start = True
        logger.debug(f"Created route to start: {[str(p) for p in self.route.points]}")
        self.move()

    def return_to_base(self):
        logger.debug(f"UAV {self.uav_id} is forced to return to base.")
        self.routing_to_start = False

        if self.trailing:
            self.stop_trailing()

        self.generate_route(self.base.location)
        self.routing_to_base = True

    def land(self):
        logger.debug(f"UAV {self.uav_id} landed at {self.location} - starting maintenance")
        if self.marker is not None:
            for m in self.marker:
                m.remove()
            self.text.remove()
        self.marker = None

        if self.radius_patch is not None:
            self.radius_patch.remove()
            self.radius_patch = None

        self.grounded = True
        logger.debug(f"Removing {self} from current airborne UAVs")
        self.world.current_airborne_drones.remove(self)

        self.past_points = []
        self.time_spent_airborne = 0
        self.start_maintenance()

    def generate_route(self, destination):
        logger.debug(f"Creating route from {self.location} to {destination} for UAV {self.uav_id}")
        self.route = create_route(point_a=self.location, point_b=destination,
                                  polygons_to_avoid=self.polygons_to_avoid)
        self.past_points.append(self.route.points[0])
        self.next_point = self.route.points[1]
        self.remaining_points = self.route.points[2:]
        logger.debug(f"UAV {self.uav_id} has routing {[str(p) for p in self.route.points]}")

    def sample_random_patrol_start(self) -> Point:
        # TODO: make dependent on endurance and range of the UAV (In a more sophisticated way)
        x = np.random.uniform(constants.PATROL_MIN_LAT,
                              constants.PATROL_MAX_LAT)
        y = np.random.uniform(constants.PATROL_MIN_LONG,
                              min(constants.PATROL_MAX_LONG, constants.PATROL_MIN_LONG + (self.range / 2)))
        return Point(x, y)

    def generate_patrol_location(self) -> Point:
        points = [self.sample_random_patrol_start() for _ in range(constants.PATROL_LOCATIONS)]
        CoPs = []
        for point in points:
            cop, _ = self.world.receptor_grid.calculate_CoP(point, self.radius)
            CoPs.append(cop)
        # currently selecting minimal location - could do weight based sampling instead
        min_index = CoPs.index(min(CoPs))
        return points[min_index]

    def start_maintenance(self):
        self.under_maintenance = True
        required_time = (3.4 * (60 / self.world.time_delta) + 0.68 * self.endurance)
        self.estimated_finish_maintenance = self.world.time + required_time

    def update_plot(self):
        if self.marker is not None:
            for m in self.marker:
                m.remove()
            self.text.remove()
            self.marker = None

        if self.radius_patch is not None:
            self.radius_patch.remove()

        self.radius_patch = matplotlib.patches.Circle((self.location.x, self.location.y), radius=self.radius,
                                                      color="indianred", alpha=0.1, linewidth=None)
        self.ax.add_patch(self.radius_patch)
        self.marker = self.ax.plot(self.location.x, self.location.y, color=constants.UAV_COLOR,
                                   marker="X", markersize=constants.WORLD_MARKER_SIZE, markeredgecolor="black")

        self.text = self.ax.text(self.location.x, self.location.y - 0.001, str(self.uav_id), color="white")


class Airbase:
    color = "rebeccapurple"

    def __init__(self, name: str, location: Point):
        self.name = name
        self.location = location
        self.drones_stationed = []

    def __str__(self):
        return f"Airbase {self.name} at {self.location}"

    def station_drone(self, drone: Drone):
        self.drones_stationed.append(drone)

    def add_airbase_to_plot(self, ax):
        self.location.add_point_to_plot(ax, color=self.color, marker="8",
                                        marker_edge_width=2, markersize=constants.WORLD_MARKER_SIZE - 4)
        return ax