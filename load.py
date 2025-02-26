import os
import glob

image_dir = "F:/LSCDATA/keyframes/201901"

annotated_images = set()

def load_images():    
    # use os.walk to get all images in subdirectories
    all_images = glob.glob(os.path.join(image_dir, "**/*.jpg"), recursive=True)
    all_images = [i.replace("\\", "/") for i in all_images]
    total_images = len(all_images)
    image_list = [img for img in all_images if img not in annotated_images]


load_images()