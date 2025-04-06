import os
from PIL import Image

# Configuration
frames_folder = "frames"
avatar_path = "avatar.png"
num_frames = 9
delay = 0.02
output_size = (256, 310)
avatar_size = (256, 255)
triggered_size = (256, 55)
triggered_position = (0, 255)
tint_color = (255, 0, 0, 50)  # Red tint

# Predefined path (list of tuples with (x, y) coordinates)
path = [
    (-4, -3),
    (3, 2),
    (2, 4),
]


def apply_red_tint(image, tint_color):
    """Apply a red tint to the image."""
    tint_image = Image.new("RGBA", image.size, tint_color)
    tinted_image = Image.blend(image, tint_image, alpha=tint_color[3] / 255.0)
    return tinted_image


def create_avatar_gif():
    """Create a GIF with the avatar following a predetermined path and combine with triggered frames."""
    frames_list = []

    # Load and tint the avatar image
    if not os.path.exists(avatar_path):
        print(f"Error: {avatar_path} does not exist.")
        return

    avatar_img = Image.open(avatar_path).resize(avatar_size).convert("RGBA")
    avatar_img = apply_red_tint(avatar_img, tint_color)

    for i, position in enumerate(path):
        if i >= num_frames:
            break

        img_resized = Image.new("RGBA", output_size, (0, 0, 0, 0))

        # Overlay the avatar image onto the resized frame
        img_resized.paste(avatar_img, position, avatar_img)  # Use avatar_img as mask

        frames_list.append(img_resized)

    # Process each triggered frame
    triggered_frames = []
    for i in range(1, num_frames + 1):
        frame_path = os.path.join(frames_folder, f"{i}.png")

        if not os.path.exists(frame_path):
            print(f"Error: {frame_path} does not exist.")
            continue

        # Open and resize the triggered frame
        triggered_img = Image.open(frame_path).resize(triggered_size).convert("RGBA")

        img_resized = Image.new("RGBA", output_size, (0, 0, 0, 0))
        img_resized.paste(triggered_img, triggered_position)

        triggered_frames.append(img_resized)

    if not triggered_frames:
        print("No triggered frames to process.")
        return

    # Combine avatar frames with triggered frames
    combined_frames = []
    for i in range(min(num_frames, len(frames_list), len(triggered_frames))):
        frame_with_trigger = Image.alpha_composite(frames_list[i], triggered_frames[i])
        combined_frames.append(frame_with_trigger)

    if not combined_frames:
        print("No combined frames to save.")
        return

    # Save the final GIF
    output_gif_path = "triggered.gif"
    combined_frames[0].save(
        output_gif_path,
        save_all=True,
        append_images=combined_frames[1:],
        duration=int(delay * 1000),  # Duration in milliseconds
        loop=0,  # Loop indefinitely
    )


create_avatar_gif()
