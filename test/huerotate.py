from io import BytesIO
import numpy as np
from PIL import Image


def adjust_hue(image, hue_shift):
    image = image.convert("HSV")
    hue, saturation, value = image.split()
    hue = np.array(hue, dtype=np.float32)
    hue = (hue + hue_shift) % 255
    hue = Image.fromarray(hue.astype(np.uint8))
    return Image.merge("HSV", (hue, saturation, value)).convert("RGB")


def process_image(image_path, degree):
    # Open the image
    image = Image.open(image_path)

    # Calculate hue shift
    hue_shift = degree * 255 / 360

    adjusted_image = adjust_hue(image, hue_shift)

    output = BytesIO()
    adjusted_image.save(output, format="PNG")
    output.seek(0)

    return output


# Example usage:
image_path = "image.png"
degree = 120
adjusted_image_output = process_image(image_path, degree)

# To save the output to a file
with open("adjusted_image.png", "wb") as f:
    f.write(adjusted_image_output.getbuffer())
