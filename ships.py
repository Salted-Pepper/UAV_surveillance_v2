"""
Contains information regarding the ship object, behaviour and basic information regarding entering
"""

import random
import copy
from typing import Literal

import constants
from points import Point
from general_maths import calculate_direction_vector
from routes import create_route

import os
import logging
import datetime
date = datetime.date.today()
logging.basicConfig(level=logging.DEBUG, filename=os.path.join(os.getcwd(), 'logs/navy_log_' + str(date) + '.log'),
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt="%H:%M:%S")
logger = logging.getLogger("SHIPS")
logger.setLevel(logging.WARNING)

ship_id = 0


class Ship:
    def __init__(self, model: Literal['Cargo', 'Bulk', 'Container'], world):

        # General Properties
        global ship_id
        logger.debug(f"Initializing ship {ship_id} with type {model}")
        self.ship_id = ship_id
        ship_id += 1
        self.world = world

        # Location and traverse properties
        self.location: Point or None = None
        self.entry_point = None
        self.next_point = None
        self.remaining_points = None
        self.past_points = []
        self.destination = None
        self.goal_dock = None

        self.route = None

        # Parameters to track ship status
        self.arrival_time = None
        self.health_points = constants.SHIP_HEALTH
        self.trailing_UAVs = []

        self.retreating = False
        self.detected = False
        self.CTL = False
        self.boarded = False
        self.sunk = False
        self.reached_destination = False
        self.left_AoI = False
        self.damage_penalty = 0

        # Model Inherited Properties

        self.load = None
        self.speed = None
        self.RCS = None
        self.model = model
        self.initiate_parameters()

        # Plot Properties
        self.ax = world.ax
        self.marker = None
        self.text = None

    def initiate_parameters(self) -> None:
        if self.model == "Cargo":
            self.speed = constants.CARGO_AVERAGE_SPEED
            self.load = constants.CARGO_AVERAGE_LOAD
            self.RCS = constants.CARGO_RCS
        elif self.model == "Bulk":
            self.speed = constants.BULK_AVERAGE_SPEED
            self.load = constants.BULK_AVERAGE_LOAD
            self.RCS = constants.BULK_RCS
        elif self.model == "Container":
            self.speed = constants.CONTAINER_AVERAGE_SPEED
            self.load = constants.CONTAINER_AVERAGE_LOAD
            self.RCS = constants.CONTAINER_RCS

    def enter_world(self, world) -> None:
        self.generate_ship_entry_point()
        self.generate_ship_end_point(world)

    def set_destination(self, world, destination: Point) -> None:
        logger.debug(f"Ship {self.ship_id} set destination to {destination}")
        self.destination = destination
        self.destination.name = "Destination"
        self.generate_route(world.polygons)

    def make_move(self):
        """
        Creates the decision the ship makes in this timestep (e.g. continue with route, return, etc.)
        :return:
        """
        # TODO: Add decisions on moving back, being hit, etc. - for now just continue following route

        self.move(self.world.time_delta)

    def move(self, time_delta) -> None:
        distance_to_travel = time_delta * self.speed

        # Use the distance we move to travel past as many points on the route as we can
        # (ensure we don't overshoot a point)
        iterations = 0
        while distance_to_travel > 0 and not self.reached_destination:
            iterations += 1
            if iterations > constants.ITERATION_LIMIT:
                raise TimeoutError(f"Vessel {self.ship_id} stuck on distance {distance_to_travel}")
            logger.debug(f"Ship {self.ship_id} travelling from {self.location.x, self.location.y} "
                         f"to {self.next_point.x, self.next_point.y} ")
            direction_vector = calculate_direction_vector(self.location, self.next_point)

            logger.debug(f"- dir vector is {direction_vector} - dist to travel {distance_to_travel}")
            distance_to_next_point = self.location.distance_to_point(self.next_point)
            distance_travelled = min(distance_to_travel, distance_to_next_point)
            distance_to_travel -= distance_travelled
            logger.debug(f"Next point {self.next_point}. Dist to next point {distance_to_next_point}, "
                         f"distance travelled {distance_travelled}")

            if distance_to_next_point <= distance_travelled:
                self.past_points.append(self.next_point)
                self.location.x = self.next_point.x
                self.location.y = self.next_point.y
                if len(self.remaining_points) > 0:
                    self.next_point = self.remaining_points.pop(0)
                else:
                    self.reached_end_point()
                logger.debug(f"Ship {self.ship_id} has {distance_to_travel} remaining - next point {self.next_point}, "
                             f"location is {self.location.x, self.location.y}")
            else:
                logger.debug(f"Ship {self.ship_id} moved from {self.location.x}, {self.location.y}")
                part_of_route = (distance_travelled/distance_to_next_point)
                self.location.x = self.location.x * (1 - part_of_route) + self.next_point.x * part_of_route
                self.location.y = self.location.y * (1 - part_of_route) + self.next_point.y * part_of_route
                logger.debug(f"to {self.location.x}, {self.location.y}")

    def generate_ship_entry_point(self) -> None:
        """
        Generates random y coordinate at which ship enters on the East Coast
        :return:
        """
        longitude = random.uniform(constants.MIN_LONG, constants.MAX_LONG)
        latitude = constants.MAX_LAT

        self.entry_point = Point(latitude, longitude)
        self.location = copy.deepcopy(self.entry_point)
        logger.debug(f"Ship {self.ship_id} enters at {self.entry_point}")

    def generate_ship_end_point(self, world) -> None:
        """
        Create destination for ship (One of the Docks in Taiwan)
        :param world:
        :return:
        """
        self.goal_dock = random.choices(world.docks, weights=[d.probability for d in world.docks], k=1)[0]
        self.set_destination(world, self.goal_dock.location)

    def generate_route(self, polygons: list, destination: Point = None) -> None:
        if destination is None:
            pass
        else:
            self.destination = destination
        self.route = create_route(point_a=self.location, point_b=self.destination,
                                  polygons_to_avoid=copy.deepcopy(polygons))
        self.past_points.append(self.route.points[0])
        self.next_point = self.route.points[1]
        self.remaining_points = self.route.points[2:]
        logger.debug(f"Ship {self.ship_id} has route {[str(p) for p in self.route.points]}")

    def reached_end_point(self) -> None:
        for uav in self.trailing_UAVs:
            uav.stop_trailing()
        self.reached_destination = True
        self.update_plot()
        self.text.remove()

    def remove_from_plot(self):
        if self.marker is not None:
            for m in self.marker:
                m.remove()
            self.text.remove()

    def update_plot(self):
        self.remove_from_plot()
        self.marker = self.ax.plot(self.location.x, self.location.y, color=constants.MERCHANT_COLOR,
                                   marker="*", markersize=constants.WORLD_MARKER_SIZE, markeredgecolor="black")
        self.text = self.ax.text(self.location.x, self.location.y, str(self.ship_id), color="white")

    def receive_damage(self, damage: int) -> None:
        """
        Receive damage from drone attack and adjust behaviour according to result
        :param damage:
        :return:
        """

        damage = damage + 10 * self.damage_penalty
        self.health_points -= damage
        print(f"Ship {self.ship_id} received {damage} damage. New health: {self.health_points}")

        # Set Damage Effects
        if self.health_points >= 81:
            return
        elif self.health_points >= 71:
            pass
        elif self.health_points >= 47:
            self.damage_penalty = 1
        elif self.health_points >= 21:
            self.damage_penalty = 2
        # TODO : Address 9-16 range (CTL but not retreating?)
        elif self.health_points >= 9:
            self.CTL = True
            self.damage_penalty = 2
        else:
            self.sinking()
            return

        # retreat unless health > 81 or sunk
        self.start_retreat()

    def sinking(self):
        """
        Ship sank, remove from world, update statistics.
        :return:
        """
        print(f"Ship {self.ship_id} sunk at ({self.location.x}, {self.location.y}).")
        for uav in self.trailing_UAVs:
            uav.perceive_ship_sunk()

        self.sunk = True
        self.route = None
        self.world.ship_destroyed(self)
        self.remove_from_plot()

    def start_retreat(self) -> None:
        """
        Start retreat process, generate a route back out of the area of interest
        :return:
        """
        print(f"Ship {self.ship_id} is retreating with {self.health_points=}")
        if self.retreating:
            return
        else:
            self.retreating = True
            self.generate_route(self.world.polygons, destination=self.entry_point)


def generate_random_ship(world) -> Ship:
    model = random.choices(["Cargo", "Container", "Bulk"],
                           [constants.CARGO_DAILY_ARRIVAL_MEAN,
                            constants.BULK_DAILY_ARRIVAL_MEAN,
                            constants.CONTAINER_DAILY_ARRIVAL_MEAN])[0]
    return Ship(model, world)
