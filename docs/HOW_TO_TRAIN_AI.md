# How to Train the AI to Detect Multicabs

The current AI model (`yolov8s.pt` or `yolov5s.pt`) is pre-trained on the COCO dataset, which can detect general "cars", "trucks", or "buses", but it does not know what a "multicab" is. 

To teach the AI to specifically identify a **multicab**, you need to train a *custom YOLOv8 model*. Here is the step-by-step process.

---

## Step 1: Collect Images of Multicabs
You need a dataset containing pictures of multicabs. 
1. **Take Photos/Videos:** Record footage from the actual camera you are using for the system. This ensures the AI learns what multicabs look like from that specific angle, lighting, and height. 
2. **Extract Frames:** If you took a video, extract frames (images) from the video.
3. **Quantity:** Aim for at least **200 to 500 images** of multicabs in various positions, lighting conditions, and angles. The more, the better.

## Step 2: Annotate (Draw Boxes) on the Images
The AI learns by looking at thousands of examples where a human has drawn a box around the object and labeled it.
1. Create a free account on **[Roboflow](https://roboflow.com/)** (highly recommended for beginners).
2. Create a new project and set the Object Type to "Object Detection".
3. Upload your images.
4. **Annotate:** Go through every single image and draw a tight bounding box around every multicab you see. Label it exactly as `multicab`.
5. *Tip:* If there are normal cars or people in the image, you don't necessarily have to label them unless you want the AI to detect them too. If you only care about multicabs, just label the multicabs.

## Step 3: Export the Dataset
Once you have annotated all images:
1. In Roboflow, generate a new dataset version.
2. Click **Export Dataset**.
3. Choose **YOLOv8** format.
4. Download the dataset to your computer as a `.zip` file and extract it into your project folder. Let's assume you extract it to a folder named `datasets/multicab_data`.

## Step 4: Train the Custom YOLOv8 Model
Since your system already has the `ultralytics` package installed, you can train the model right on your machine!

1. Open your terminal/command prompt and activate your virtual environment (refer to `HOW_TO_RUN.md`).
2. Inside your `datasets/multicab_data` folder, there should be a `data.yaml` file.
3. Run the following command in your terminal to start training:

```bash
yolo task=detect mode=train model=yolov8s.pt data=datasets/multicab_data/data.yaml epochs=50 imgsz=640
```

- `model=yolov8s.pt`: We start with the base YOLOv8 small model to speed up learning.
- `epochs=50`: The number of times the AI looks at the entire dataset. 50-100 is usually good for a first try.
- `imgsz=640`: The image size. 640 is standard.

*Note: Training can take several hours depending on your computer's graphics card (GPU) or CPU.*

## Step 5: Locate and Move Your New Weights
When training finishes successfully, Ultralytics will save the new "brain" (weights file) in a folder. Look at the terminal output; it will usually say something like:
`Results saved to runs/detect/train/weights/best.pt`

1. Locate the `best.pt` file.
2. Copy it into your project's main folder (or `ai_model` folder) and rename it to something clear, like `multicab_model.pt`.

## Step 6: Update the System to Use the New Model
Finally, you need to tell your python code to use the new model instead of the default one.

1. Open `config/config.py`.
2. Find the line that sets the model path:
   ```python
   MODEL_PATH = "yolov8s.pt" # Or whatever it currently is
   ```
3. Change it to point to your new file:
   ```python
   MODEL_PATH = "multicab_model.pt"
   ```

Restart your application (`python app.py`) and your system will now be able to specifically detect and label "multicabs"!
