import math
import glm
from glm import vec3

## make each point a tuple of a glm vec3 coordinate, and a color
## points is a list of the points that have both of these values

def plot_vertexes (width, height, base_color, point_color):
    vertexes = [
        (vec3(width * -0.866, 0, width * -0.5), vec3(base_color[0], base_color[1], base_color[2])),
        (vec3(width * 0.866, 0, width * -0.5), vec3(base_color[0], base_color[1], base_color[2])),
        (vec3(0, 0, width), vec3(base_color[0], base_color[1], base_color[2])),
        (vec3(0, height, 0), vec3(point_color[0], point_color[1], point_color[2]))
    ]
    return vertexes

def interpolate_w_color (a, b, color_1, color_2, x):
    face_points = []
    dist = math.sqrt(glm.dot(a - b, a - b))
    n = int(dist / x)

    #color_dist = math.sqrt(glm.dot(color_1 - color_2, color_1 - color_2))
    #color_n = int((color_dist / x))
    for i in range(n):
        u = i / n
        g = a * (1 - u) + u * b

        k = color_1 * (1 - u) + u * color_2
        face_points.append((g, k))
    return face_points


def interpolate (a, b, color, x):
    face_points = []
    dist = math.sqrt(glm.dot(a - b, a - b))
    n = int(dist / x)

    for i in range(n):
        u = i / n
        g = a * (1 - u) + u * b

        face_points.append((g, color))
    return face_points


def create_mcfunction (out_name, width, height, density, base_color, point_color, size):
    vertexes = plot_vertexes(width, height, base_color, point_color)
    points = []
    edges = []
    for i in range(0, 3):
        a = vertexes[i][0]
        b = vertexes[3][0]

        ca = vertexes[i][1]
        cb = vertexes[3][1]
        edges.append(interpolate_w_color(a, b, ca, cb, density))
    for i in range(0, len(edges[0])):
        v0 = edges[0][i][0]
        v1 = edges[1][i][0]
        v2 = edges[2][i][0]

        color = edges[0][i][1]
        points += interpolate(v0, v1, color, density)
        points += interpolate(v1, v2, color, density)
        points += interpolate(v2, v0, color, density)
    #print(len(points))
    #with open(out_name, 'w') as out:
    #    for i in points:
    #        out.write(f"particle flame ~{i[0]} ~{i[1]} ~{i[2]} 0 0 0 0 1 force\n")
    with open(out_name, 'w') as out:
        out.write("## File created with RiceRocket's spike particle creator\n\n\n")
        for i in points:
            out.write(f"particle minecraft:dust {i[1][0]} {i[1][1]} {i[1][2]} {size} ^{i[0][0]} ^{i[0][2]} ^{i[0][1]} 0 0 0 0 1 force @a\n")

input_out = str(input("Name of output file: "))
input_width = float(input("Width of spike (in blocks): "))
input_height = float(input("Length of spike (in blocks): "))
input_density = float(input("Density of particles (in blocks). Recommended values are from 0.1 - 0.3: "))
input_base_color = str(input("Color of the base of the spike (RGB): "))
input_point_color = str(input("Color of the point of the spike (RGB): "))
input_size = float(input("Size of the particles used. Recommended values are from 0.8 - 1: "))

out_file = input_out + '.mcfunction'

base_color_array = input_base_color.split(',')
point_color_array = input_point_color.split(',')


create_mcfunction (out_file, input_width, input_height, input_density, (float(base_color_array[0]), float(base_color_array[1]), float(base_color_array[2])), (float(point_color_array[0]), float(point_color_array[1]), float(point_color_array[2])), input_size)