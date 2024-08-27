import cv2


# a read_video function that reads a video and returns the frames in a list
def read_video(video_path):
    # VideoCapture is a class that is used to read video files
    cap = cv2.VideoCapture(video_path)
    frames = []
    # a condition that will end its loop when the video has no more frames/has ended
    while True:
        # read is a function that gives the return value of the frame and the frame itself
        # ret is the true or false and frame is the frame itself
        ret, frame = cap.read()

        if not ret:
            break
        frames.append(frame)
    return frames

# a save_video function that saves a list of frames as a video
def save_video(output_video_frames, output_video_path):
    # Define the codec for video compression and specify the MP4 format using 'mp4v'.
    # The FourCC (Four Character Code) is a 4-byte identifier used to specify the video codec.
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    
    # Initialize the VideoWriter object to save the video.
    # - output_video_path: the path where the output video file will be saved.
    # - fourcc: the codec to be used for compressing the video frames.
    # - 24: the frame rate (frames per second) of the output video.
    # - (width, height): the dimensions of the video frames, taken from the first frame in the list.
    out = cv2.VideoWriter(output_video_path, fourcc, 24, 
                          (output_video_frames[0].shape[1], 
                           output_video_frames[0].shape[0]))
    # .shape is a function that returns the dimensions of the frame, the first element is the height and the second element is the width
    
    # Iterate over each frame in the list of output video frames.
    # This loop writes each frame sequentially to the video file.
    for frame in output_video_frames:
        # Write the current frame to the video file.
        out.write(frame)
    
    # Release the VideoWriter object and finalize the video file.
    # This is an important step to ensure that the file is properly saved
    # and that all resources associated with the VideoWriter are released.
    out.release()

