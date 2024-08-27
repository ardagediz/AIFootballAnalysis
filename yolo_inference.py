# ultralytics is the library that is used to load the model, YOLO
from ultralytics import YOLO 

# YOLO has models up to v9 with different capablities, nano, small, medium, large, xlarge, and xxlarge the difference between them lies in the numebr of layers and the number of parameters
# the larger the model the more accurate it is, but the slower it is to run, the reason being for this is that the more layers and parameters the model has the more complex the model is and the more space time and compute power it needs to run
# for this project as I used github codespaces due to not having a GPU, and the github student pro membership allows for you to leverage a much stronger machine type
# I was able to use a much stronger model through stronger compute power allowed though github codespaces

#used to load the model
model = YOLO('models/best.pt')

# the function used to run the model, the save parmater is then used to save the video output result
results = model.predict('input_videos/08fd33_4.mp4',save=True)
print(results[0])
print('=====================================') # used to separate the results
for box in results[0].boxes:
    print(box)
# the for loop above is used to print out the bounding boxes of the objects detected in the video
# what is display is the xywh of the bounding box, teh confidence, class id and a few other parameters

# intitally running this takes much longer as the model must be downloaded and loaded, but after the first run the model is cached and the results are much faster

# the results are then saved in the runs folder, the first predict is from the first time i ran the model and the second predict is from the second time i ran the model using a further trained model