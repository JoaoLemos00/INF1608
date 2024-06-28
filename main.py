"""
Ao executar o programa, selecione o ângulo e posição da câmera 
desejados e aperte 'q' para iniciar a simulação.
"""

import math
import time
import numpy as np
import pyvista as pv

#-------------------------------------------------------------------
# Global variables
#-------------------------------------------------------------------
# Size of mesh (cloth) in points. They are all 1 unit apart.
size_x = 40
size_y = 25
straight_bar_size = 1
diagonal_bar_size = math.sqrt(2)

# Accelerations
wind = [10, 0, 2]
gravity = [0, -9.8, 0]

points = [] # [x, y, z]
last_points = [] # stores (i-1) data for points
faces = [] # [num_vertices, vertices_indexes...]
bars = [] # [vertice_index, vertice_index, size]
secondary_bars = [] # [vertice_index, vertice_index, size]

camera_pos = [
	(20, 0, 120), # camera location
	(20, 0, 0),   # focus point
	(0, 0, 0),    # viewup vector
]

#-------------------------------------------------------------------
# Auxiliar methods
#-------------------------------------------------------------------
def is_mobile(index):
	"""Returns wether the point with given index is mobile or not"""
	return index%size_y != 0

def norm(v):
	"""Returns norm of vector v"""
	sum_ = 0
	for val in v:
		sum_ += val*val
	return math.sqrt(sum_)

def add(u, v):
	"""Returns (u+v)"""
	w = u.copy()
	for i,val in enumerate(v):
		w[i] += val
	return w

def subtract(u, v):
	"""Returns (u-v)"""
	w = u.copy()
	for i,val in enumerate(v):
		w[i] -= val
	return w

def multiply(v, k):
	"""Returns multiplication of vector v with scalar k"""
	u = v.copy()
	for i,val in enumerate(u):
		u[i] *= k
	return u

#-------------------------------------------------------------------
# Methods
#-------------------------------------------------------------------
def impose_constraint():
	"""Imposes constraint on bars"""
	for k in range(0, 20):
		# For each bar, we try to restore its original size
		for i,bar in enumerate(bars+secondary_bars):
			# First, we access the points that the bar connects
			a = points[bar[0]]
			b = points[bar[1]]
			# Then, we find its current size and direction
			d = subtract(b, a)
			dist = norm(d)
			u = multiply(d, 1/dist)
			# Finally, we calculate how much the bar should shrink or enlarge, and
			# move the connected particles to restore its original size. If both points 
			# are mobile, each should be responsible for restoring half of the difference.
			# If only one is mobile, than it is solely responsible for making up for the
			# difference caused by moving the points independently.
			dif = 0.9*(dist - bar[2])
			if is_mobile(bar[0]):
				if is_mobile(bar[1]):
					points[bar[0]] = add(a, multiply(u, dif/2))
				else:
					points[bar[0]] = add(a, multiply(u, dif))
			if is_mobile(bar[1]):
				if is_mobile(bar[0]):
					points[bar[1]] = add(b, multiply(u, -dif/2))
				else:
					points[bar[1]] = add(b, multiply(u, -dif))

def animate(h):
	"""Animates mesh"""
	global points, last_points
	points_i = points.copy() # storing points in current state to later save them in last_points
	damp_ratio = 0.02

	# First, we move each point independently through Verlet's Method
	for i,point in enumerate(points):
		if is_mobile(i):
			point[0] = point[0] + ((1 - damp_ratio)*(point[0] - last_points[i][0]))\
				+ (h*h)*(wind[0]+gravity[0])
			point[1] = point[1] + ((1 - damp_ratio)*(point[1] - last_points[i][1]))\
				+ (h*h)*(wind[1]+gravity[1])
			point[2] = point[2] + ((1 - damp_ratio)*(point[2] - last_points[i][2]))\
				+ (h*h)*(wind[2]+gravity[2])
	# Then, we impose constraint bars restrictions
	impose_constraint()
	last_points = points_i

def init():
	"""Sets up points and faces in mesh and constraint bars"""
	global last_points
	point_index = 0
	for j in range(0, size_x):
		for i in range(0, size_y):
			# Create the vertice
			points.append([j, i, 0])
			
			# Create the faces, made up of 4 adjacent points, and the adjacent bars
			if j<size_x-1 and i<size_y-1:
				faces.append([4, point_index, point_index+1, point_index+size_y+1, point_index+size_y])
				bars.append([point_index, point_index+1, straight_bar_size])
				bars.append([point_index, point_index+size_y+1, diagonal_bar_size])
				bars.append([point_index, point_index+size_y, straight_bar_size])
			elif j==size_x-1 and i<size_y-1:
				bars.append([point_index, point_index+1, straight_bar_size])
			elif i==size_y-1 and j<size_x-1:
				bars.append([point_index, point_index+size_y, straight_bar_size])

			# Create non-adjacent bars
			if j%2 == 0: # skipping odd columns for secondary bars
				if j<size_x-2 and i<size_y-2:
					secondary_bars.append([point_index, point_index+2, 2*straight_bar_size])
					secondary_bars.append([point_index, point_index+(2*(size_y+1)), 2*diagonal_bar_size])
					secondary_bars.append([point_index, point_index+(2*size_y), 2*straight_bar_size])
				elif j==size_x-1 and i<size_y-2:
					secondary_bars.append([point_index, point_index+2, 2*straight_bar_size])
				elif i==size_y-1 and j<size_x-2:
					secondary_bars.append([point_index, point_index+(2*size_y), 2*straight_bar_size])

			point_index += 1

	last_points = points.copy()

#-------------------------------------------------------------------
# Execution
#-------------------------------------------------------------------
init()
print("Choose camera angle and position")
print("To star the animation, click 'q'")

# Plotting mesh
plotter = pv.Plotter()
mesh = pv.PolyData(np.array(points), np.array(faces))
plotter.add_mesh(mesh, color='y', show_edges=False, interpolate_before_map=True)
plotter.add_axes()
plotter.enable_eye_dome_lighting()
plotter.camera_position = camera_pos
plotter.show(interactive=True, auto_close=False, window_size=[800, 600])

plotter.open_gif("animation.gif")
plotter.write_frame()

n_steps = 75
for i in range(n_steps):
	start = time.time()
	animate(0.4)
	end = time.time()
	print(f"   Plotting step {i+1} of {n_steps}... elapsed time for 0.4s step: {(end - start)}s", end="\r")
	plotter.update_coordinates(np.array(points), mesh=mesh)
	plotter.write_frame()

print("\n")
plotter.close()