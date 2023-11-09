from world import World
import PIL
import matplotlib
matplotlib.use("Agg")
from matplotlib.animation import FuncAnimation, PillowWriter

test_world = World(time_delta=1)


def animation_function(frame):
    test_world.time_step()


anim_created = FuncAnimation(test_world.fig, animation_function, frames=200, interval=60, repeat=False)

anim_created.save("animated_arrivals.mp4", writer="ffmpeg")

print("Simulation Completed.")


