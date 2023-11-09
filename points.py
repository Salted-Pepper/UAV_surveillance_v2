import general_maths as gm

# ----------------------------------------------- LOGGER SET UP ------------------------------------------------
import logging
import datetime
import os

date = datetime.date.today()
logging.basicConfig(level=logging.DEBUG, filename=os.path.join(os.getcwd(), 'logs/navy_log_' + str(date) + '.log'),
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt="%H:%M:%S")
logger = logging.getLogger("POINTS")
logger.setLevel(logging.DEBUG)


# --------------------------------------------- END LOGGER SET UP ------------------------------------------------

unique_point_id = 0


class Point:
    def __init__(self, x: float, y: float, name=None, force_maintain=False, lon_lat=False):
        """
        2-dimensional point.
        :param x:
        :param y:
        :param name:
        :param force_maintain: Ensures that a point is kept in a convex hull
        :param lon_lat: In case the order is put in as lon/lat, we switch it to get the regular x/y-axis setup.
        """
        global unique_point_id
        self.point_id = unique_point_id
        unique_point_id += 1

        if lon_lat:
            self.x = y
            self.y = x
        else:
            self.x = x
            self.y = y
        if name is None:
            self.name = self.point_id
        else:
            self.name = name
        self.force_maintain = force_maintain

    def __str__(self):
        if self.name is None:
            return f"({self.x:0.3f}, {self.y:0.3f})"
        else:
            return f"{self.name}"

    def __add__(self, other: tuple) -> None:
        self.x += other[0]
        self.y += other[1]

    def location(self) -> tuple:
        return self.x, self.y

    def distance_to_point(self, point) -> float:
        return gm.calculate_distance(self, point)

    def add_point_to_plot(self, axes, color=None, text="", marker="o",
                          marker_edge_width=1, markersize=10, plot_text=True):
        if color is None:
            axes.plot(self.x, self.y, "o", markersize=markersize, alpha=0.5, marker=marker,
                      markeredgewidth=marker_edge_width)
        else:
            axes.plot(self.x, self.y, "o", color=color, markersize=markersize, alpha=0.5,
                      marker=marker, markeredgewidth=marker_edge_width)
        if self.name is None and plot_text:
            axes.text(self.x, self.y, text)
        elif self.name is not None and not plot_text:
            axes.text(self.x, self.y, self.name)
        elif plot_text:
            axes.text(self.x, self.y, text)
        else:
            pass
        return axes

