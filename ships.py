"""
Contains information regarding the ship object, behaviour and basic information regarding entering
"""

import random
import copy
from typing import Literal

import constants
from points import Point
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
    def __init__(self, world):

        # General Properties
        global ship_id
        self.ship_id = ship_id
        ship_id += 1
        self.world = world

        self.ship_type = None
        self.speed = None

        # Location and traverse properties
        self.location: Point or None = None
        self.entry_point = None
        self.next_point = None
        self.remaining_points = None
        self.past_points = []
        self.destination = None

        self.route = None

        # Parameters to track ship status
        self.arrival_time = None
        self.health_points = None
        self.trailing_UAVs = []

        self.traveling_to_end_point = False
        self.retreating = False
        self.detected = False
        self.CTL = False
        self.boarded = False
        self.sunk = False
        self.harbour_reached = False
        self.left_world = False
        self.left_AoI = False
        self.damage_penalty = 0

        # Plot Properties
        self.ax = world.ax
        self.marker = None
        self.text = None
        self.color = None

    def enter_world(self, world) -> None:
        self.generate_ship_entry_point()

    def set_destination(self, world, destination: Point, harbour=False, leaving=False) -> None:
        """
        :param world:
        :param destination:
        :param harbour: Boolean whether ship is heading to harbour
        :param leaving: Boolean whether ship is leaving the world
        :return:
        """
        logger.debug(f"Ship {self.ship_id} - {self.ship_type} set destination to {destination}")
        self.destination = destination

        if harbour:
            self.destination.name = "Harbour"
        elif leaving:
            self.destination.name = "Exit Point"
        else:
            self.destination.name = "Destination"
        self.generate_route(world.polygons)

    def make_move(self):
        """
        Creates the decision the ship makes in this timestep (e.g. continue with route, return, etc.)
        :return:
        """

        self.move()

        self.debug_unit()

    def move(self) -> None:
        """

        :param self.world.time_delta:
        :return:
        """
        distance_to_travel = self.world.time_delta * self.speed

        # Use the distance we move to travel past as many points on the route as we can
        # (ensure we don't overshoot a point)
        iterations = 0
        while distance_to_travel > 0 and not self.left_world:
            iterations += 1
            if iterations > constants.ITERATION_LIMIT:
                raise TimeoutError(f"{self.ship_type} {self.ship_id} stuck on distance {distance_to_travel}")
            logger.debug(f"{self.ship_type} {self.ship_id} travelling from {self.location.x, self.location.y} "
                         f"to {self.next_point.x, self.next_point.y} ")

            # logger.debug(f"- dir vector is {direction_vector} - dist to travel {distance_to_travel}")
            distance_to_next_point = self.location.distance_to_point(self.next_point)
            distance_travelled = min(distance_to_travel, distance_to_next_point)
            distance_to_travel -= distance_travelled
            # logger.debug(f"Next point {self.next_point}. Dist to next point {distance_to_next_point}, "
            #              f"distance travelled {distance_travelled}")

            if distance_to_next_point <= distance_travelled:
                self.past_points.append(self.next_point)
                self.location.x = self.next_point.x
                self.location.y = self.next_point.y
                if len(self.remaining_points) > 0:
                    self.next_point = self.remaining_points.pop(0)
                else:
                    if self.destination.name == "Exit Point":
                        self.reached_exit_point()
                    elif self.destination.name == "Harbour":
                        self.reached_harbour()
                    else:
                        # reached desired location - awaiting next step
                        return
                # logger.debug(f"Ship {self.ship_id} has {distance_to_travel} remaining - next point {self.next_point},"
                #              f" location is {self.location.x, self.location.y}")
            else:
                # logger.debug(f"Ship {self.ship_id} moved from {self.location.x}, {self.location.y}")
                part_of_route = (distance_travelled/distance_to_next_point)
                new_x = self.location.x + part_of_route * (self.next_point.x - self.location.x)
                new_y = self.location.y + part_of_route * (self.next_point.y - self.location.y)
                self.location = Point(new_x, new_y, name=str(self.ship_type) + " " + str(self.ship_id))
                # logger.debug(f"to {self.location.x}, {self.location.y}")

    def generate_ship_entry_point(self) -> None:
        """
        Generates random y coordinate at which ship enters on the East Coast
        :return:
        """
        longitude = random.uniform(constants.MIN_LONG, constants.MAX_LONG)
        latitude = constants.MAX_LAT

        self.entry_point = Point(latitude, longitude)
        self.location = copy.deepcopy(self.entry_point)
        logger.debug(f"{self.ship_type} {self.ship_id} enters at {self.entry_point}")

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
        logger.debug(f"{self.ship_type} {self.ship_id} has route {[str(p) for p in self.route.points]}")

    def reached_exit_point(self) -> None:
        for uav in self.trailing_UAVs:
            uav.stop_trailing("Ship Reached Endpoint", call_from_ship=True)
        self.left_world = True
        self.update_plot()
        self.remove_from_plot()

    def reached_harbour(self) -> None:
        for uav in self.trailing_UAVs:
            uav.stop_trailing("Ship Reached Endpoint", call_from_ship=True)
        self.harbour_reached = True
        self.left_world = True
        self.update_plot()
        self.remove_from_plot()

    def remove_from_plot(self):
        if not constants.PLOTTING_MODE:
            return
        if self.marker is not None:
            for m in self.marker:
                m.remove()
            self.text.remove()

    def update_plot(self):
        if not constants.PLOTTING_MODE:
            return
        self.remove_from_plot()
        self.marker = self.ax.plot(self.location.x, self.location.y, color=self.color,
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
        logger.debug(f"{self.ship_type} {self.ship_id} received {damage} damage. New health: {self.health_points}")

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
        print(f"{self.ship_type} {self.ship_id} sunk at ({self.location.x}, {self.location.y}).")
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
        print(f"{self.ship_type} {self.ship_id} is retreating with {self.health_points=}")
        if self.retreating:
            return
        else:
            self.retreating = True
            self.generate_route(self.world.polygons, destination=self.entry_point)

    def debug_unit(self) -> None:
        if constants.DEBUG_MODE:
            for polygon in self.world.polygons:
                if polygon.check_if_contains_point(self.location):
                    self.location.add_point_to_plot(axes=constants.axes_plot, color="yellow")
                    self.next_point.add_point_to_plot(axes=constants.axes_plot, color="black", text="NEXT")
                    self.route.add_route_to_plot(axes=constants.axes_plot)
                    for p in self.route.points:
                        p.add_point_to_plot(axes=constants.axes_plot, color="purple", text=p.point_id, markersize=8)
                        polygon.check_if_line_through_polygon(self.past_points[-1], self.next_point)
                    raise PermissionError(f"{self.ship_type} {self.ship_id} at illegal location: "
                                          f"({self.location.x: .3f}, {self.location.y: .3f}). \n"
                                          f"Route is {[str(p) for p in self.route.points]} "
                                          f"retreating: {self.retreating}, "
                                          f"sunk: {self.sunk} "
                                          f"Next Point: {self.next_point}, "
                                          f"trailing uavs? : {[u for u in self.trailing_UAVs]}. \n"
                                          f"this falls in polygon {[str(p) for p in polygon.points]}")


class Merchant(Ship):
    def __init__(self, model: Literal['Cargo', 'Bulk', 'Container'], world):
        super().__init__(world)

        # Merchant Inherited Properties
        logger.debug(f"Initializing merchant {ship_id} with type {model}")
        self.ship_type = "Merchant"
        self.cargo_load = None
        self.RCS = None
        self.model = model
        self.initiate_parameters()

        self.being_guarded = False

        self.health_points = constants.MERCHANT_HEALTH

        self.goal_dock = None

        self.color = constants.MERCHANT_COLOR

    def initiate_parameters(self) -> None:
        if self.model == "Cargo":
            self.speed = constants.CARGO_AVERAGE_SPEED
            self.cargo_load = constants.CARGO_AVERAGE_LOAD
            self.RCS = constants.CARGO_RCS
        elif self.model == "Bulk":
            self.speed = constants.BULK_AVERAGE_SPEED
            self.cargo_load = constants.BULK_AVERAGE_LOAD
            self.RCS = constants.BULK_RCS
        elif self.model == "Container":
            self.speed = constants.CONTAINER_AVERAGE_SPEED
            self.cargo_load = constants.CONTAINER_AVERAGE_LOAD
            self.RCS = constants.CONTAINER_RCS

    def set_harbour_destination(self) -> None:
        """
        Create destination for a merchant - a target dock in Taiwan
        :return:
        """
        self.goal_dock = random.choices(self.world.docks, weights=[d.probability for d in self.world.docks], k=1)[0]
        self.set_destination(self.world, self.goal_dock.location, leaving=True)

    def enter_world(self, world) -> None:
        self.generate_ship_entry_point()
        self.set_harbour_destination()


class Escort(Ship):
    def __init__(self, world, model: str, country: str):
        super().__init__(world)

        self.ship_type = "Escort"
        self.health_points = constants.ESCORT_HEALTH

        if country == "US":
            self.color = constants.US_ESCORT
        elif country == "Taiwan":
            self.color = constants.US_ESCORT
        elif self.color == "Japan":
            self.color = constants.JAPAN_ESCORT
        else:
            raise ValueError(f"Unexpected country {country} for creation of escort.")

        self.length = None
        self.displacement = None
        self.armed = None
        self.max_speed = None
        self.contains_helicopter = None
        self.endurance = None

        self.guarding_target = None

        self.obstacles = world.polygons
        self.behaviour = constants.escort_behaviour

        self.initiate_model(model)

    def initiate_model(self, model):
        for blueprint in constants.ESCORT_MODELS:
            if blueprint['name'] == model:
                self.length = blueprint['length']
                self.displacement = blueprint['displacement']
                self.armed = blueprint['armed']
                self.max_speed = blueprint['max_speed']
                self.contains_helicopter = blueprint['helicopter']
                self.endurance = blueprint['endurance']

    def make_move(self):

        if self.behaviour == "chase":
            # TODO: How do the ships hunt and detect UAVs? Similar function?
            self.move()
        elif self.behaviour == "patrol":
            # TODO: On what do we base patrol location?
            pass
        elif self.behaviour == "alongside":

            # Case 1 - currently not guarding (never assigned, merchant sunk?)
            if self.guarding_target is None:
                successful_selection = self.select_guarding_target()
                if successful_selection:
                    self.move()
                else:
                    # TODO: To implement - what if escort has no ship to guard? Leave area?
                    pass
            else:
                self.move()
        else:
            raise NotImplementedError(f"Behaviour {self.behaviour} not implemented for escorts.")

    def start_guarding(self, unit):
        unit.being_guarded = True
        self.guarding_target = unit

    def select_guarding_target(self) -> bool:
        merchants = [vessel for vessel in self.world.current_vessels
                     if vessel.ship_type == "Merchant" and not vessel.being_guarded]

        # TODO: refine how the merchant is selected - for now just closest unguarded merchant
        if len(merchants) == 0:
            return False

        escort_location = self.location
        merchant = min(merchants, key=lambda m: escort_location.distance_to_point(m.location))
        self.start_guarding(merchant)
        return True


def generate_random_merchant(world) -> Merchant:
    model = random.choices(["Cargo", "Container", "Bulk"],
                           [constants.CARGO_DAILY_ARRIVAL_MEAN,
                            constants.BULK_DAILY_ARRIVAL_MEAN,
                            constants.CONTAINER_DAILY_ARRIVAL_MEAN])[0]
    return Merchant(model, world)

