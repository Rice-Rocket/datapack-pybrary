import math
from glm import vec3
import glm

def parse_obj (file, scale):
    vertexes = []
    faces = []
    for line in file:
        if line.startswith('v '):
                vertexes.append(vec3([float(i) for i in line.split()[1:]]))
        elif line.startswith('f '):
                faces_ = line.split()[1:]
                faces.append([int(face_.split('/')[0]) - 1 for face_ in faces_])
    min_v = vec3(9999999999)
    max_v = -min_v
    for v in vertexes: 
        min_v.x = min(min_v.x, v.x)
        min_v.y = min(min_v.y, v.y)
        min_v.z = min(min_v.z, v.z)

        max_v.x = max(max_v.x, v.x)
        max_v.y = max(max_v.y, v.y)
        max_v.z = max(max_v.z, v.z)

    diag = max_v - min_v
    center = (diag) / 2
    max_d = max(diag.x, diag.y, diag.z)
    #print(1 / max_d * scale)
    s = 1 / max_d * scale
    S = glm.scale(vec3(s))
    T = glm.translate(-center)
    M = S * T
    #print(M)

    for i in range(len(vertexes)):
        v = (M * vertexes[i])
        vertexes[i] = v
    #print(T)

    return vertexes, faces, min_v, max_v

def interpolate (a, b, x):
    face_points = []
    dist = math.sqrt(glm.dot(a - b, a - b))
    #dist = math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)
    n = int(dist / x)
    for i in range(n):
        u = i / n
        g = a * (1 - u) + u * b
        face_points.append(g)
    return face_points


def draw (vertexes, faces, density):
    points = []
    #for v in vertexes:
    #    points.append(v)
    for f in faces:
        for i in range(len(f)):
            i0 = f[(i - 1)%len(f)]
            i1 = f[i]
            v0 = vertexes[i0]
            v1 = vertexes[i1]
            points += interpolate(v0, v1, density)
    return points

def create_mcfunction (in_name, out_name, particle, density, scale):
    with open(in_name, 'r') as file:
        vertexes, faces, min_v, max_v = parse_obj(file, scale)
        points = draw(vertexes, faces, density)
        
        #print(min_v)
        #print(max_v)
        #print(len(points))
        #print(faces)
    with open(out_name, 'w') as out:
        out.write("## File created with RiceRocket's Obj particle converter\n\n\n")
        for i in points:
            out.write(f"particle {particle} ~{i[0]} ~{i[1]} ~{i[2]} 0 0 0 0 1 force @a\n")
    print(f"Created {len(points)} particle commands.")

## main

input_in_file = str(input("Input .obj filename (ignoring file extension): ")) + '.obj'
input_out_file = str(input("Output .mcfunction filename (ignoring file extension): ")) + '.mcfunction'
input_particle_type = str(input("Particle to use: "))

if input_particle_type == 'dust':
    input_dust = str(input("Color of dust particle (RGB): "))
    dust_array = input_dust.split(',')
    input_dust_r = float(dust_array[0])
    input_dust_g = float(dust_array[1])
    input_dust_b = float(dust_array[2])
    input_dust_size = input("Size of dust particle: ")
    input_particle_type = f"dust {input_dust_r} {input_dust_g} {input_dust_b} {input_dust_size}"

input_scale = int(input("Scale of model ingame (in blocks): "))
input_density = float(input(f"Distance between particles (in blocks), recommended number to use is {input_scale / 50}: "))

input("Press enter to continue")

create_mcfunction (input_in_file, input_out_file, input_particle_type, input_density, input_scale)

print(f"Created file '{input_out_file}'")
#create_mcfunction ('t_34_obj.obj', 'particles.mcfunction', 'flame', 0.1, 5)
#print(interpolate(vec3([1, 0, 1]), vec3([0, 0, 0]), 10))