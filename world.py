from points import Point
from polygons import Polygon
from drones import Drone, Airbase
from ships import Ship, generate_random_ship

import matplotlib.pyplot as plt

from receptors import ReceptorGrid
import constants
import constants_coords

import numpy as np
import datetime
import os
import logging

if not os.path.exists("logs"):
    os.makedirs("logs")

date = datetime.date.today()

logging.basicConfig(level=logging.DEBUG, filename=os.path.join(os.getcwd(), 'logs/navy_log_' + str(date) + '.log'),
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt="%H:%M:%S")
logger = logging.getLogger("WORLD")
logger.setLevel(logging.DEBUG)

logging.getLogger("matplotlib").setLevel(logging.WARNING)
logging.getLogger("PIL").setLevel(logging.WARNING)
logging.getLogger("PIL.PngImagePlugin").setLevel(logging.WARNING)
logging.getLogger("fiona.ogrext").setLevel(logging.WARNING)
logging.getLogger("GEOPOLYGON").setLevel(logging.WARNING)


class World:
    def __init__(self, time_delta: float):
        # Create Geography
        self.landmasses = []
        self.china_polygon = None
        self.initiate_land_masses()
        self.polygons = [landmass.polygon for landmass in self.landmasses]

        self.x_min = None
        self.x_max = None

        self.y_min = None
        self.y_max = None

        self.docks = None
        self.initiate_docks()

        self.airbases = None
        self.initiate_airbases()

        self.receptor_grid = None
        self.initiate_receptor_grid()

        # World Variable Characteristics
        self.weather = None
        self.time_delta = time_delta  # In Hours
        self.time = 0

        # Statistics
        self.current_vessels = []
        self.current_airborne_drones = []

        # Plotting
        self.fig = None
        self.ax = None
        self.plot_world(True)

        self.drones = None
        self.initiate_drones()

    def initiate_land_masses(self) -> None:
        self.landmasses = [Landmass(name="taiwan", polygon=Polygon(points=constants_coords.TAIWAN_POINTS),
                                    color=constants_coords.TAIWAN_COLOR),
                           Landmass(name="orchid_island", polygon=Polygon(points=constants_coords.ORCHID_ISLAND_POINTS),
                                    color=constants_coords.TAIWAN_COLOR),
                           Landmass(name="green_island", polygon=Polygon(points=constants_coords.GREEN_ISLAND_POINTS),
                                    color=constants_coords.TAIWAN_COLOR),
                           Landmass(name="penghu", polygon=Polygon(points=constants_coords.PENGHU_COUNTRY_POINTS),
                                    color=constants_coords.TAIWAN_COLOR),
                           Landmass(name="wangan", polygon=Polygon(points=constants_coords.WANGAN_POINTS),
                                    color=constants_coords.TAIWAN_COLOR),
                           Landmass(name="qimei", polygon=Polygon(points=constants_coords.QIMEI_POINTS),
                                    color=constants_coords.TAIWAN_COLOR),
                           Landmass(name="yonaguni", polygon=Polygon(points=constants_coords.YONAGUNI_POINTS),
                                    color=constants_coords.JAPAN_COLOR),
                           Landmass(name="taketomi", polygon=Polygon(points=constants_coords.TAKETOMI_POINTS),
                                    color=constants_coords.JAPAN_COLOR),
                           Landmass(name="ishigaki", polygon=Polygon(points=constants_coords.ISHIGAKE_POINTS),
                                    color=constants_coords.JAPAN_COLOR),
                           Landmass(name="miyakojima", polygon=Polygon(points=constants_coords.MIYAKOJIMA_POINTS),
                                    color=constants_coords.JAPAN_COLOR),
                           Landmass(name="okinawa", polygon=Polygon(points=constants_coords.OKINAWA_POINTS),
                                    color=constants_coords.JAPAN_COLOR),
                           Landmass(name="okinoerabujima",
                                    polygon=Polygon(points=constants_coords.OKINOERABUJIMA_POINTS),
                                    color=constants_coords.JAPAN_COLOR),
                           Landmass(name="tokunoshima", polygon=Polygon(points=constants_coords.TOKUNOSHIMA_POINTS),
                                    color=constants_coords.JAPAN_COLOR),
                           Landmass(name="amami_oshima", polygon=Polygon(points=constants_coords.AMAMI_OSHIMA_POINTS),
                                    color=constants_coords.JAPAN_COLOR),
                           Landmass(name="yakushima", polygon=Polygon(points=constants_coords.YAKUSHIMA_POINTS),
                                    color=constants_coords.JAPAN_COLOR),
                           Landmass(name="tanegashima", polygon=Polygon(points=constants_coords.TANEGASHIMA_POINTS),
                                    color=constants_coords.JAPAN_COLOR),
                           Landmass(name="japan", polygon=Polygon(points=constants_coords.JAPAN_POINTS),
                                    color=constants_coords.JAPAN_COLOR),
                           ]

        self.china_polygon = Landmass(name="china", polygon=Polygon(points=constants_coords.CHINA_POINTS),
                                      color=constants_coords.CHINA_COLOR)

    def initiate_receptor_grid(self) -> None:
        self.receptor_grid = ReceptorGrid(self.polygons + [self.china_polygon.polygon])

    def initiate_docks(self) -> None:
        self.docks = [Dock(name="Kaohsiung", location=Point(120.30, 22.44, name="Kaohsiung", force_maintain=True),
                           probability=0.4),
                      Dock(name="Tiachung", location=Point(120.42, 24.21, name="Tiachung", force_maintain=True),
                           probability=0.3),
                      Dock(name="Keelung", location=Point(121.75, 25.19, name="Keelung", force_maintain=True),
                           probability=0.25),
                      Dock(name="Hualien", location=Point(121.70, 23.96, name="Hualien", force_maintain=True),
                           probability=0.05)]

    def initiate_airbases(self) -> None:
        self.airbases = [Airbase(name="Base 1", location=Point(112, 22, force_maintain=True)),
                         Airbase(name="Base 2", location=Point(114, 32, force_maintain=True))]

    def initiate_drones(self) -> None:
        # TODO: Automatically make a large set of drones and spread out over the airbases.
        logger.debug("Initiating Drones...")
        self.drones = [Drone(model='test', world=self, airbase=self.airbases[0]),
                       Drone(model='test', world=self, airbase=self.airbases[1]),
                       Drone(model='test', world=self, airbase=self.airbases[0]),
                       Drone(model='test', world=self, airbase=self.airbases[1]),
                       Drone(model='test', world=self, airbase=self.airbases[0]),
                       Drone(model='test', world=self, airbase=self.airbases[1]),
                       Drone(model='test', world=self, airbase=self.airbases[0]),
                       Drone(model='test', world=self, airbase=self.airbases[1]),
                       Drone(model='test', world=self, airbase=self.airbases[0]),
                       Drone(model='test', world=self, airbase=self.airbases[1]), ]

    def plot_world(self, include_receptors=False) -> None:
        self.fig, self.ax = plt.subplots(1, figsize=(constants.PLOT_SIZE, constants.PLOT_SIZE))
        self.ax.set_title(f"Sea Map - time is {self.time}")
        self.ax.set_facecolor("#2596be")
        self.ax.set_xlim(left=constants.MIN_LAT, right=constants.MAX_LAT)
        self.ax.set_xlabel("Latitude")
        self.ax.set_ylim(bottom=constants.MIN_LONG, top=constants.MAX_LONG)
        self.ax.set_ylabel("Longitude")

        for landmass in self.landmasses:
            logging.debug(f"Plotting {landmass}")
            self.ax = landmass.add_landmass_to_plot(self.ax)

        self.ax = self.china_polygon.add_landmass_to_plot(self.ax)

        for dock in self.docks:
            logging.debug(f"Plotting {dock}")
            self.ax = dock.add_dock_to_plot(self.ax)

        for airbase in self.airbases:
            logging.debug(f"Plotting {airbase}")
            self.ax = airbase.add_airbase_to_plot(self.ax)

        if include_receptors:
            for receptor in self.receptor_grid.receptors:
                self.ax = receptor.initiate_plot(self.ax, self.receptor_grid.cmap)

        constants.axes_plot = self.ax

        plt.show()
        self.fig.canvas.draw()

    def plot_world_update(self) -> None:
        self.ax.set_title(f"Sea Map - time is {self.time}")
        for ship in self.current_vessels:
            ship.update_plot()

        for drone in self.current_airborne_drones:
            drone.update_plot()

        for receptor in self.receptor_grid.receptors:
            receptor.update_plot(self.ax, self.receptor_grid.cmap)

        self.fig.canvas.draw()
        plt.show()

    def ship_enters(self, ship: Ship) -> None:
        ship.enter_world(self)
        self.current_vessels.append(ship)

    def launch_drone(self) -> None:
        # TODO: Work out sending/launching of drones (currently launches one each turn)
        if self.time > 10:
            for drone in self.drones:
                if drone.grounded:
                    print(f"Drone {drone.uav_id} launched.")
                    drone.launch(self)
                    return

    def calculate_ships_entering(self) -> int:
        """
        Calculate number of ships entering in time period t.
        :return: Integer number of ships entering
        """
        # TODO: Sample from poisson with rate lambda as in overleaf
        if np.random.rand() > 0.8:
            return 1
        else:
            return 0

    def create_arriving_ships(self):
        for _ in range(self.calculate_ships_entering()):
            new_ship = generate_random_ship(self)
            logger.debug(f"New ship: {new_ship.ship_id} is entering the AoI")
            self.ship_enters(new_ship)

    def calculate_ship_movements(self):
        ships_finished = []

        for ship in self.current_vessels:
            ship.make_move(self.time_delta)
            if ship.reached_destination:
                ships_finished.append(ship)

        # Remove ships that have reached their destination
        for ship in ships_finished:
            self.current_vessels.remove(ship)

    def calculate_drone_movements(self):
        for drone in self.current_airborne_drones:
            drone.move()

    def time_step(self):
        self.time += self.time_delta

        self.create_arriving_ships()
        self.calculate_ship_movements()

        self.launch_drone()
        self.calculate_drone_movements()
        for drone in self.current_airborne_drones:
            if drone.patrolling:
                drone.observe_area(self.current_vessels)

        self.receptor_grid.depreciate_pheromones()
        self.plot_world_update()
        print(f"Completed iteration {self.time}")
        logger.debug(f"End of iteration {self.time} \n")


class Landmass:
    def __init__(self, name: str, polygon: Polygon, color="grey"):
        self.name = name
        self.polygon = polygon
        self.color = color

    def __str__(self):
        return f"Landmass {self.name}"

    def add_landmass_to_plot(self, axis):
        axis = self.polygon.add_polygon_to_plot(axis, color=self.color, opacity=0.8)
        return axis


class Dock:
    color = "green"

    def __init__(self, name: str, location: Point, probability: float):
        self.name = name
        self.location = location
        self.probability = probability
        self.load_received = 0

    def __str__(self):
        return str(self.name)

    def add_dock_to_plot(self, ax):
        self.location.add_point_to_plot(ax, color=self.color, marker="D",
                                        marker_edge_width=2, markersize=constants.WORLD_MARKER_SIZE - 4,
                                        plot_text=False)
        return ax


world = World(time_delta=1)

# for landmass in world.landmasses:
#     for point in landmass.polygon.points:
#         if landmass.name == "japan" or landmass.name == "taiwan":
#             point.add_point_to_plot(constants.axes_plot, text=f"{str(point)}", markersize=5)

for _ in range(20):
    world.time_step()
