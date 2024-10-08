from ultralytics import YOLO
import supervision as sv
import pickle
import os
# sys is used to append the path to the utils folder so that the functions in the utils folder can be used
import sys
sys.path.append('../')
from utils import get_center_of_bbox, get_bbox_width, get_foot_position
import cv2
import numpy as np
import pandas as pd

class Tracker:
    def __init__(self, model_path):
        # this is simply the constructor for the class, it is used to initialize the class and set the model path to the model path that is passed in
        self.model = YOLO(model_path) 
        # the tracker is then initialized to the ByteTrack class from the supervision library
        # ByteTracker is a algorithm used to track the obects within the video
        # tracking is essential as to ensure objects are not lost and redetected as a new object
        self.tracker = sv.ByteTrack()

    # what this function does is that it allows us to work with each frames in the video
    def detect_frames(self, frames):
        # batch size is set to 20, this is the number of frames that are processed at a time to prevent any errors from occuring with a larger batch size
        batch_size=20 
        # detections is a list that is used to store the detections of the objects in the frames
        detections = [] 
        # for loop is used to iterate through the frames in the video
        for i in range(0,len(frames),batch_size):
            # minimum confidence is set to 0.1, this is the minimum confidence that the model must have to detect an object
            detections_batch = self.model.predict(frames[i:i+batch_size],conf=0.1)
            # the detections are then appended to the detections list
            detections += detections_batch
        return detections


    def get_object_tracks(self, frames, read_from_stub=False, stub_path=None):


        # this is used to save the results of the detections so that the model doesnt have to unnecessarily run again
        # this is used to read the stub file which is the pkl file that contains the tracks of the objects
        # tracks of the objects are the detections of the objects in the video
        if read_from_stub and stub_path is not None and os.path.exists(stub_path):
            # rb is used to read the file in binary mode
            # we read in binary mode because the file is a pkl file and pkl files are read in binary mode
            with open(stub_path,'rb') as f:
                tracks = pickle.load(f)
            return tracks

        # used to detect the frames
        detections = self.detect_frames(frames)

        # this is used to store the tracks of the objects in the video
        tracks={
            "players":[],
            "referees":[],
            "ball":[]
        }  

        # here we're 
        for frame_num, detection in enumerate(detections):
            cls_names = detection.names
            # this is used to instead of having a key value of {0:player}, have a mappingf of {player:0}
            # this is done for convenience of finding the class id of the object
            cls_names_inv = {v:k for k,v in cls_names.items()}
            print(cls_names)

            # Covert to supervision Detection format

            # what this specific line does is that it converts the detection from the ultralytics format to the supervision format
            # supervisison format is a format that is used to store the detections of the objects in the video
            detection_supervision = sv.Detections.from_ultralytics(detection)

            # now that we have the detections in the supervision format we can now convert the goalkeeper to a player object
            # without changing it to supervision format we would not be able to convert the goalkeeper to a player object
            # the goalkeeper is changed to a player object because the model keeps switching the player and goalkeeper classes likley due to the model not being trained on more data

            # Convert GoalKeeper to player object
            for object_ind , class_id in enumerate(detection_supervision.class_id):
                if cls_names[class_id] == "goalkeeper":
                    detection_supervision.class_id[object_ind] = cls_names_inv["player"]
                    # replaces class id of goalkeeper with class id of player
            
            # Track objects
            # the function update_with_detections is used to update the tracker with the detections, it is a function from the supervision library
            # this is used to update the tracker with the changes in the detections e.g the goalkeeper being changed to a player object
            detection_with_tracks = self.tracker.update_with_detections(detection_supervision)

            # this is a dictionary of lists that is used to store the tracks of the objects in the video
            # this is done for convenience of finding the tracks of the objects in the video
            tracks["players"].append({})
            tracks["referees"].append({})
            tracks["ball"].append({})

            # here we are iterating through the detections with tracks and adding the detections to the tracks
            for frame_detection in detection_with_tracks:
                # tolist is a function that converts the detection to a list
                # the framedetection[?] was based off of the output of the detection_with_tracks
                # here we're extracting the bbox, class id and track id from the detection to store in the tracks
                bbox = frame_detection[0].tolist()
                cls_id = frame_detection[3]
                track_id = frame_detection[4]

                if cls_id == cls_names_inv['player']:
                    tracks["players"][frame_num][track_id] = {"bbox":bbox}
                
                if cls_id == cls_names_inv['referee']:
                    tracks["referees"][frame_num][track_id] = {"bbox":bbox}

            for frame_detection in detection_supervision:
                bbox = frame_detection[0].tolist()
                cls_id = frame_detection[3]

                if cls_id == cls_names_inv['ball']:
                    tracks["ball"][frame_num][1] = {"bbox":bbox}

        # if the function parameter is True then the tracks are saved to the stub file
        if stub_path is not None:
            # wb is used to write the file in binary mode
            with open(stub_path,'wb') as f:
                # dump is used to write the tracks to the file
                pickle.dump(tracks,f)

        return tracks

    def add_position_to_tracks(sekf,tracks):
        for object, object_tracks in tracks.items():
            for frame_num, track in enumerate(object_tracks):
                for track_id, track_info in track.items():
                    bbox = track_info['bbox']
                    if object == 'ball':
                        position= get_center_of_bbox(bbox)
                    else:
                        position = get_foot_position(bbox)
                    tracks[object][frame_num][track_id]['position'] = position

    def interpolate_ball_positions(self,ball_positions):
        ball_positions = [x.get(1,{}).get('bbox',[]) for x in ball_positions]
        df_ball_positions = pd.DataFrame(ball_positions,columns=['x1','y1','x2','y2'])

        # Interpolate missing values
        df_ball_positions = df_ball_positions.interpolate()
        df_ball_positions = df_ball_positions.bfill()

        ball_positions = [{1: {"bbox":x}} for x in df_ball_positions.to_numpy().tolist()]

        return ball_positions



    def draw_ellipse(self,frame,bbox,color,track_id=None):
        # we want to draw an ellipse on the lower half of the bbox
        # bbox[3] is the y2 coordinate of the bbox
        y2 = int(bbox[3])
        # this is the x coordinate of the center of the bbox
        # get_center_of_bbox is a function in the utils folder that is used to get the center of the bbox
        x_center, _ = get_center_of_bbox(bbox)
        # this is used to work with the radius of the ellipse
        width = get_bbox_width(bbox)

        # .ellipse() is the cv2 function that is used to draw the ellipse
        cv2.ellipse(
            frame,
            center=(x_center,y2),
            # axes is the major and minor axes of the ellipse
            # an ellipse as its oval shape has two axes, the major and minor (radius)
            axes=(int(width), int(0.35*width)),
            angle=0.0,
            # the start angle and end angle are used to create that unfinished look of the ellipse
            startAngle=-45,
            endAngle=235,
            color = color,
            thickness=2,
            lineType=cv2.LINE_4
        )

        # these are used to draw the player id on the ellipse
        rectangle_width = 40
        rectangle_height=20
        x1_rect = x_center - rectangle_width//2
        x2_rect = x_center + rectangle_width//2
        y1_rect = (y2- rectangle_height//2) +15
        y2_rect = (y2+ rectangle_height//2) +15

        if track_id is not None:
            cv2.rectangle(frame,
                          (int(x1_rect),int(y1_rect) ),
                          (int(x2_rect),int(y2_rect)),
                          color,
                          cv2.FILLED)
            
            x1_text = x1_rect+12
            if track_id > 99:
                x1_text -=10
            
            cv2.putText(
                frame,
                f"{track_id}",
                (int(x1_text),int(y1_rect+15)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0,0,0),
                2
            )

        return frame
    
    def draw_traingle(self,frame,bbox,color):
        y= int(bbox[1])
        x,_ = get_center_of_bbox(bbox)

        triangle_points = np.array([
            [x,y],
            [x-10,y-20],
            [x+10,y-20],
        ])
        cv2.drawContours(frame, [triangle_points],0,color, cv2.FILLED)
        cv2.drawContours(frame, [triangle_points],0,(0,0,0), 2)

        return frame

    def draw_team_ball_control(self,frame,frame_num,team_ball_control):
        # Draw a semi-transparent rectaggle 
        overlay = frame.copy()
        cv2.rectangle(overlay, (1350, 850), (1900,970), (255,255,255), -1 )
        alpha = 0.4
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

        team_ball_control_till_frame = team_ball_control[:frame_num+1]
        # Get the number of time each team had ball control
        team_1_num_frames = team_ball_control_till_frame[team_ball_control_till_frame==1].shape[0]
        team_2_num_frames = team_ball_control_till_frame[team_ball_control_till_frame==2].shape[0]
        team_1 = team_1_num_frames/(team_1_num_frames+team_2_num_frames)
        team_2 = team_2_num_frames/(team_1_num_frames+team_2_num_frames)

        cv2.putText(frame, f"Team 1 Ball Control: {team_1*100:.2f}%",(1400,900), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 3)
        cv2.putText(frame, f"Team 2 Ball Control: {team_2*100:.2f}%",(1400,950), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 3)

        return frame

    def draw_annotations(self,video_frames, tracks, team_ball_control):
        # this is going to be the output video frames once the annotations have been drawn on
        output_video_frames= []
        for frame_num, frame in enumerate(video_frames):
            # create a copy of the frames as to not modify the original frames
            frame = frame.copy()

            # Get the tracks for the current frame
            player_dict = tracks["players"][frame_num]
            ball_dict = tracks["ball"][frame_num]
            referee_dict = tracks["referees"][frame_num]

            # Draw around the Players
            for track_id, player in player_dict.items():
                # this is from later on in the project and is used to assign team colors to the players
                color = player.get("team_color",(0,0,255))
                # calling the draw_ellipse function to draw the ellipse around the player
                frame = self.draw_ellipse(frame, player["bbox"],color, track_id)
                
                # this is used to draw the possession marker around the player if the player has the ball
                if player.get('has_ball',False):
                    frame = self.draw_traingle(frame, player["bbox"],(0,0,255))

            # Draw around the Referee
            for _, referee in referee_dict.items():
                frame = self.draw_ellipse(frame, referee["bbox"],(0,255,255))

            # Draw around the ball 
            for track_id, ball in ball_dict.items():
                frame = self.draw_traingle(frame, ball["bbox"],(0,255,0))

            # Draw Team Ball Control
            frame = self.draw_team_ball_control(frame, frame_num, team_ball_control)


            output_video_frames.append(frame)

        return output_video_frames
    