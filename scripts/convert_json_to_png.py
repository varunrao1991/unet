import shutil
import argparse
from PIL import Image, ImageDraw
import os
import json
import glob
import math

import random

def split_list_strings(strings, file1, file2, percentSplit = 0.7):
    random.shuffle(strings)
    split_index = int(percentSplit * len(strings))
    strings_file1 = strings[:split_index]
    strings_file2 = strings[split_index:]

    with open(file1, 'w') as f1:
        for string in strings_file1:
            f1.write(string + '\n')

    with open(file2, 'w') as f2:
        for string in strings_file2:
            f2.write(string + '\n')
def write_list_strings(strings, fileout):
    random.shuffle(strings)
    with open(fileout, 'w') as f1:
        for string in strings:
            f1.write(string + '\n')

def get_polygon_bounding_box(points):
    min_x = float('inf')
    max_x = float('-inf')
    min_y = float('inf')
    max_y = float('-inf')

    for x, y in points:
        min_x = min(min_x, x)
        max_x = max(max_x, x)
        min_y = min(min_y, y)
        max_y = max(max_y, y)

    bounding_box = (str(int(min_x)), str(int(min_y)), str(int(max_x)), str(int(max_y)))
    return bounding_box

def get_image_size(file_path):
    with Image.open(file_path) as image:
        return image.size

def scehema_parse(json_file_path):
    colors = {}
    with open(json_file_path, 'r') as json_file:
        data = json.load(json_file)
        label_class_groups = data['label_class_groups']
        for label_class_group in label_class_groups:
            group_classes = label_class_group['group_classes']
            for group_class in group_classes:
                colors[group_class["name"]] = group_class["colours"]["default"]
    print(colors)
    return colors

def split_filename_and_extension(file_path):
    file_name, file_ext = os.path.splitext(file_path)
    return file_name, file_ext
def split_folder_and_filename(file_path):
    folder, filename = os.path.split(file_path)
    return folder, filename

def get_rotated_ellipse_coordinates(x_center, y_center, radius_x, radius_y, angle):
    a = radius_x
    b = radius_y
    
    x1 = x_center + a*math.cos(angle)
    y1 = y_center + a*math.sin(angle)
    
    x2 = x_center - a*math.cos(angle)
    y2 = y_center - a*math.sin(angle)
    
    x3 = x_center + b*math.cos(angle + math.pi/2)
    y3 = y_center + b*math.sin(angle + math.pi/2)
    
    x4 = x_center - b*math.cos(angle + math.pi/2)
    y4 = y_center - b*math.sin(angle + math.pi/2)
    
    return x1, y1, x2, y2, x3, y3, x4, y4

def get_rotated_ellipse_limits(x_center, y_center, radius_x, radius_y, angle):
    x1, y1, x2, y2, x3, y3, x4, y4 = get_rotated_ellipse_coordinates(x_center, y_center, radius_x, radius_y, angle)
    x_min = min(x1, x2, x3, x4)
    x_max = max(x1, x2, x3, x4)
    y_min = min(y1, y2, y3, y4)
    y_max = max(y1, y2, y3, y4)
    return x_min, x_max, y_min, y_max

    
def convert_json_to_png(image_files, colors, output_folder, output_folder_categorical, non_json_folder):
    ssd_data = [];
    scale_mask_int = 1;
    for index, image_file in enumerate(jpg_files):
        #print(image_file)
        labels = None
        
        width, height = get_image_size(image_file)
        
        folder, filename = split_folder_and_filename(image_file)
        file_name, ext = split_filename_and_extension(filename)
        json_file_path = os.path.join(folder, file_name + "__labels.json")
        print(index, ":", filename)
        # Create a new blank image of the correct size
        image = Image.new('RGB', (width, height), color=(0, 0, 0))
        image_gray = Image.new('L', (width, height), color=0)
		
        box_data = ""

        if os.path.exists(json_file_path):
            # Open the JSON file and extract the necessary data
            with open(json_file_path, 'r') as json_file:
                data = json.load(json_file)
                labels = data['labels']

            # Draw each label as a filled polygon on the image
            for label_index, label in enumerate(labels):
                label_class = label['label_class']
                color = ()
                if label_class is not None:
                    color_list = colors[label_class]
                    color = (color_list[0], color_list[1], color_list[2])
                else:
                    color = (255, 255, 255)
                if label_class is None:
                    continue
                label_type = label['label_type']
                if label_type == "polygon":
                    regions = label['regions']
                    for region in regions:
                        points = []
                        for point in region:
                            points.append((point['x'],point['y']))
                        draw = ImageDraw.Draw(image)
                        draw.polygon(points, fill=color)
                        draw = ImageDraw.Draw(image_gray)
                        draw.polygon(points, fill=scale_mask_int *(label_index + 1))
                        box = get_polygon_bounding_box(points)
                        box_data += " " + ",".join(box) + "," + str(label_index)
                elif label_type == "oriented_ellipse":
                    x = label['centre']['x']
                    y = label['centre']['y']
                    r1 = label['radius1']
                    r2 = label['radius2']
                    angle = label['orientation_radians']
                    #xmin, xmax, ymin, ymax = get_rotated_ellipse_limits(x, y, r1, r2, angle)
                    #print(xmin, xmax, ymin, ymax)
                    #draw.ellipse((xmin, ymin, xmax, ymax), fill=color)

                    x0 = x - r1
                    x1 = x + r1
                    y0 = y - r2
                    y1 = y + r2
                    new_im = Image.new('RGB', (width, height), color=(0, 0, 0))
                    draw1 = ImageDraw.Draw(new_im)
                    draw1.ellipse((x0, y0, x1, y1), fill=color)
                    new_im = new_im.rotate(-math.degrees(angle), center = (x, y))
                    # Convert the input image to grayscale
                    grayscale_image = new_im.convert("L")

                    # Threshold the grayscale image to create a binary mask
                    threshold = 0
                    binary_mask = grayscale_image.point(lambda pixel: 255 if pixel > threshold else 0)
                    image.paste(new_im, (0, 0, width, height), binary_mask)

                    new_im_gray = Image.new('L', (width, height), color=0)                

                    draw1 = ImageDraw.Draw(new_im_gray)
                    draw1.ellipse((x0, y0, x1, y1), fill=scale_mask_int *(label_index + 1))
                    new_im_gray = new_im_gray.rotate(-math.degrees(angle), center = (x, y))
                    # Convert the input image to grayscale
                    grayscale_image = new_im_gray.convert("L")

                    # Threshold the grayscale image to create a binary mask
                    threshold = 0
                    binary_mask = grayscale_image.point(lambda pixel: 255 if pixel > threshold else 0)
                    image_gray.paste(new_im_gray, (0, 0, width, height), binary_mask)
                        
            ssd_data.append(image_file + box_data)

            image_out_path = os.path.join(output_folder, file_name + ".png")
            # Save the resulting image as a PNG file
            image.save(image_out_path, 'PNG')
            image_out_path = os.path.join(output_folder_categorical, file_name + ".png")
            # Save the resulting image as a PNG file
            image_gray.save(image_out_path, 'PNG')
        else:
            shutil.move(image_file, os.path.join(non_json_folder, filename))
    return ssd_data

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process an json file and convert to png.')
    parser.add_argument('--schema_file', '-s', type=str, default="schema.json", required=False, help='Provide a schema file.')
    parser.add_argument('--image_folder', '-i', type=str, required=True, help='Provide a folder for images.')
    parser.add_argument('--output_folder', '-o', type=str, required=True, help='Provide output folder.')
    parser.add_argument('--output_folder_categorical', '-c', type=str, required=True, help='Provide output folder for categorical.')
    parser.add_argument('--non_json_folder', '-n', type=str, required=True, help='Provide output folder.')
    args = parser.parse_args()

    # Create the output folder if it doesn't exist
    if not os.path.exists(args.output_folder):
        os.makedirs(args.output_folder)
    # Create the output folder if it doesn't exist
    if not os.path.exists(args.non_json_folder):
        os.makedirs(args.non_json_folder)
    # Create the output folder if it doesn't exist
    if not os.path.exists(args.output_folder_categorical):
        os.makedirs(args.output_folder_categorical)

    schema_path = os.path.join(args.image_folder, args.schema_file)
    jpg_files = glob.glob(os.path.join(args.image_folder, "*.bmp")) + glob.glob(os.path.join(args.image_folder, "*.jpg"))
    colors = scehema_parse(schema_path)

    # Call the main function with the input and output file paths
    out_data = convert_json_to_png(jpg_files, colors, args.output_folder, args.output_folder_categorical, args.non_json_folder)

    #write_list_strings(out_data, os.path.join(args.output_folder, "data.csv"))
    split_list_strings(out_data, os.path.join(args.output_folder, "objects_train.txt"), os.path.join(args.output_folder, "objects_test.txt"))
