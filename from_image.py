from PIL import Image

def rgb_pixel (img, x, y):
    #im = Image.open(img)
    r, g, b = img.getpixel((x, y))
    a = (r / 255, g / 255, b / 255)
    return a

def create_mcfunction (img, out_name, dx, dy, density, size):
    desired_width = int(dx / density)
    desired_height = int(dy / density)

    im = Image.open(img).convert('RGB')
    scaled_im = im.resize((desired_width, desired_height))

    colors = []
    for x in range(desired_width):
        for y in range(desired_height):
            color = rgb_pixel(scaled_im, x, y)
            color_coords = ((x * density, y * density), (color))
            colors.append(color_coords)

    out_name = out_name + '.mcfunction'
    with open(out_name, 'w') as file:
        file.write("## File created with RiceRocket's Obj particle converter\n\n\n")
        for i in colors:
            file.write(f'particle dust {i[1][0]} {i[1][1]} {i[1][2]} {size} ~{i[0][0]} ~ ~{i[0][1]} 0 0 0 0 1 force\n')

input_image = str(input("Input image name (include file extension): "))
input_out = str(input("Output function (exclude .mcfunction file extension): "))
input_width = float(input("Width of image (in blocks): "))

a, b, x, y = Image.open(input_image).getbbox()
aspect = x / y
rec_height = input_width / aspect

input_height = float(input(f"Height of image (in blocks). To maintain aspect ratio, use {rec_height}: "))
input_density = float(input(f"Density of particles (closeness in blocks): "))
input_size = float(input("Size of particles: "))


create_mcfunction (input_image, input_out, input_width, input_height, input_density, input_size)
