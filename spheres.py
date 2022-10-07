import os
import glm
import math
import shutil


def pick_colors (light, dark, x):
    light_color = glm.vec3(light[0], light[1], light[2])
    dark_color = glm.vec3(dark[0], dark[1], dark[2])

    colors = []
    for i in range(x):
        u = i / x
        g = light_color * (1 - u) + u * dark_color
        colors.append(g)

    colors.append(dark_color)
    return colors

def create_files (projectname, path, offset, helixcount, rotatespeed, helixdensity, light, dark, radius):
    os.makedirs(projectname)
    os.chdir(projectname)
    os.makedirs('anim')

    projectpath = path + '/' + projectname

    rotation_device = f'{projectname}.rotation_device'
    score = f'{projectname}.animate_sphere'
    credits = f"## This file was created with RiceRocket's sphere generator.\n## Exported under the project name {projectname}\n\n\n\n"

    with open('install.mcfunction', 'w') as install:
        install.write(credits)
        install.write(f'forceload add 0 0\nkill @e[type=area_effect_cloud,tag={rotation_device}]\nsummon area_effect_cloud 0 0 0 \u007bDuration:2147483647,Tags:["{rotation_device}"]\u007d\nscoreboard objectives add {score} dummy\ntellraw @s ["",\u007b"text":"RiceRocket\'s sphere generator installed the objective ","color":"green"\u007d,\u007b"text":"{score}","color":"aqua"\u007d]')

    with open('animate.mcfunction', 'w') as animate:
        animate.write(credits)
        animate.write(f'execute as @e[type=area_effect_cloud,tag={rotation_device}] at @s run function {projectpath}/anim/rotate\nfunction {projectpath}/anim/ticking')

    os.chdir('anim')

    with open('ticking.mcfunction', 'w') as ticking:
        ticking.write(credits)
        ticking.write(f'tp @s ~{offset[0]} ~{offset[1] + 1} ~{offset[2]} 0 -90\n\nexecute at @e[type=area_effect_cloud,tag={rotation_device}] run summon area_effect_cloud ^ ^ ^{helixcount} \u007bTags:["{projectname}.rotation.sine"]\u007d\nexecute store result score @s {score} run data get entity @e[type=area_effect_cloud,tag={projectname}.rotation.sine,limit=1] Pos[1] 100\n\nscoreboard players set particle {score} 90\nscoreboard players set angle {score} 0\nscoreboard players operation color {score} = @s {score}\nscoreboard players add color {score} 90\n\nexecute run function {projectpath}/anim/particles\ntp @s ~ ~ ~')

    with open('rotate.mcfunction', 'w') as rotate:
        rotate.write(credits)
        rotate.write(f'execute unless entity @s[tag={projectname}.rotate.flip] at @s rotated as @s run tp @s ~ ~ ~ ~{rotatespeed * 2} ~-{rotatespeed}\nexecute if entity @s[tag={projectname}.rotate.flip] at @s rotated as @s run tp @s ~ ~ ~ ~{rotatespeed * 2} ~{rotatespeed}\n\nexecute if entity @s[x_rotation=-90] run tag @s add {projectname}.rotate.flip\nexecute if entity @s[x_rotation=90] run tag @s remove {projectname}.rotate.flip')

    colors = pick_colors(light, dark, 5)

    with open('particles.mcfunction', 'w') as particles:
        particles.write(credits)
        particles.write(f'scoreboard players remove particle {score} 1\nscoreboard players remove color {score} 3\n\nexecute if score color {score} matches ..-142 at @s run particle minecraft:dust {colors[0][0]} {colors[0][1]} {colors[0][2]} 0.8 ^ ^ ^{radius} 0 0 0 0 1 force\nexecute if score color {score} matches -143..-93 at @s run particle minecraft:dust {colors[1][0]} {colors[1][1]} {colors[1][2]} 0.8 ^ ^ ^{radius} 0 0 0 0 1 force\nexecute if score color {score} matches -94..-45 at @s run particle minecraft:dust {colors[2][0]} {colors[2][1]} {colors[2][2]} 0.8 ^ ^ ^{radius} 0 0 0 0 1 force\nexecute if score color {score} matches -46..-3 at @s run particle minecraft:dust {colors[3][0]} {colors[3][1]} {colors[3][2]} 0.8 ^ ^ ^{radius} 0 0 0 0 1 force\nexecute if score color {score} matches -4..52 at @s run particle minecraft:dust {colors[4][0]} {colors[4][1]} {colors[4][2]} 0.8 ^ ^ ^{radius} 0 0 0 0 1 force\nexecute if score color {score} matches 53.. at @s run particle minecraft:dust {colors[5][0]} {colors[5][1]} {colors[5][2]} 0.8 ^ ^ ^{radius} 0 0 0 0 1 force\n\nexecute at @s run tp @s ~ ~ ~ ~ ~2\nscoreboard players operation angle {score} += @s {score}\nexecute store result entity @s Rotation[0] float {helixdensity} run scoreboard players get angle {score}\nexecute if score particle {score} matches 1.. at @s run function {projectpath}/anim/particles')

replace_files = True

input_projectname = str(input("Name of your project: "))

if os.path.exists(input_projectname):
    replace_confirm = input("This folder already exists, would you like to replace it? (Y/N): ")
    if replace_confirm == 'N' or replace_confirm == 'n':
        replace_files = False
    else: 
        replace_files = True


if replace_files == True:
    input_path = str(input("Path of your sphere functions (Ex. example:folder_1/folder_2): "))
    input_offset = str(input("XYZ offset of the sphere relative to the executer: "))
    input_helix_count = float(input("\rParticle distribution (Bigger number makes a more solid sphere. Recommended value is 1): "))
    input_helix_density = float(input("Density of the helix. For essentially one twirl, use 0.08: "))
    input_rotate_speed = float(input("Rotation speed of the animation. A value of 5 results in approximately a one second rotation: "))
    input_radius = float(input("Radius of sphere (in blocks): "))

    input_light_color = str(input("Lightest possible color of the sphere (RGB): "))
    input_dark_color = str(input("Darkest possible color of the sphere (RGB): "))


    offset_array = input_offset.split(',')
    light_color_array = input_light_color.split(',')
    dark_color_array = input_dark_color.split(',')

    shutil.rmtree(input_projectname)

    create_files (input_projectname, input_path, (float(offset_array[0]), float(offset_array[1]), float(offset_array[2])), input_helix_count, input_rotate_speed, input_helix_density, (float(light_color_array[0]), float(light_color_array[1]), float(light_color_array[2])), (float(dark_color_array[0]), float(dark_color_array[1]), float(dark_color_array[2])), input_radius)

    print(f"\n\nCreated 5 files and 1 directory under the directory '{input_projectname}'")