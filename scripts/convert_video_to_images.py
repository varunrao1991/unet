import cv2
import os
import argparse
import numpy as np
    
def save_frames(video_path, output_folder):
    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Open the video file for reading
    cap = cv2.VideoCapture(video_path)
    dir_path, full_file_name = os.path.split(video_path)
    file_name, extension = os.path.splitext(full_file_name)
    # Loop over all frames in the video
    frame_index = 0
    skip_index  = 100
    while True:
        # Read a frame from the video
        ret, frame = cap.read()
        if not ret:
            # End of video
            break
            
        if frame_index % skip_index != 0:
            frame_index += 1
            continue

        # Construct the output file path
        output_path = os.path.join(output_folder, f"{file_name}_frame_{frame_index}.jpg")
        
        # Define the ROI coordinates
        cv2.imwrite(output_path, frame)
        frame_index += 1

    # Release the video file
    cap.release()

if __name__ == '__main__':
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description='Save all frames of a video file as separate image files in a folder.')

    # Add the command line arguments
    parser.add_argument('--video_path', '-v', type=str, required=True, help='Path to the video file.')
    parser.add_argument('--output_folder', '-o', type=str, required=True, help='Path to the output folder for saving the frames.')

    # Parse the arguments
    args = parser.parse_args()

    # Call the save_frames function with the command line arguments
    save_frames(args.video_path, args.output_folder)
