import os
import subprocess
import base64
from PIL import Image
import imageio.v3 as iio

try:
    import cairosvg
except ImportError:
    cairosvg = None

def raster_to_svg(input_file, output_file):
    with open(input_file, "rb") as f:
        img_data = f.read()
    b64_data = base64.b64encode(img_data).decode("utf-8")
    svg_content = f'<svg xmlns="http://www.w3.org/2000/svg"><image href="data:image/png;base64,{b64_data}" height="100%" width="100%"/></svg>'
    with open(output_file, "w") as f:
        f.write(svg_content)

def convert_image(input_file, output_format, output_path=None):
    if not output_path:
        output_path = os.path.splitext(input_file)[0] + "." + output_format
    ext = os.path.splitext(input_file)[1].lower().replace(".", "")
    raster_formats = ["jpg", "jpeg", "png", "webp", "bmp", "gif", "tiff"]
    vector_formats = ["svg", "pdf", "eps"]

    if ext in raster_formats and output_format.lower() in raster_formats:
        Image.open(input_file).save(output_path)
    elif ext in raster_formats and output_format.lower() == "svg":
        raster_to_svg(input_file, output_path)
    elif cairosvg and ext in vector_formats and output_format.lower() in raster_formats:
        cairosvg.svg2png(url=input_file, write_to=output_path)
    else:
        img = iio.imread(input_file)
        iio.imwrite(output_path, img)

    return output_path

def convert_video(input_file, output_format, output_path=None):
    if not output_path:
        output_path = os.path.splitext(input_file)[0] + "." + output_format
    subprocess.run(["ffmpeg", "-i", input_file, output_path, "-y"])
    return output_path

def convert_audio(input_file, output_format, output_path=None):
    if not output_path:
        output_path = os.path.splitext(input_file)[0] + "." + output_format
    subprocess.run(["ffmpeg", "-i", input_file, output_path, "-y"])
    return output_path
