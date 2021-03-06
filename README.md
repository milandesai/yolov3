# Recurrent YOLO with Agot dataset

This README contains instructions for running both non-recurrent and recurrent YOLO on the Agot dataset, as described in [Spatiotemporal Action Recognition on Restaurant Videos](report.pdf).

The code is a modification of the [YOLOv3 implementation by Ultralytics LLC](https://github.com/ultralytics/yolov3). The [original README](README-ultralytics.md) has more detailed setup instructions and information, should any problems arise with the below instructions.

## Branches

- `base`: for comparing changes; we forked off of this commit from the Ultralytics repository
- `non-recurrent`: for training/testing regular YOLO on the Agot dataset
- `master`: for training Recurrent YOLO on the Agot dataset

## Prerequisites

1. Run: `pip install -U -r requirements.txt`
2. Obtain weight files from authors (too large to put in Git)
- `weights/yolov3-spp-ultralytics.pt`: pretrained COCO weights from Ultralytics
- `weights/yolov3-spp-nonrecurrent.pt`: best nonrecurrent weights for Agot dataset
- `weights/yolov3-spp-lstm1.pt`: Agot weights copied to single LSTM architecture
- `weights/yolov3-spp-lstm2.pt`: Agot weights copied to double LSTM architecture
- `weights/yolov3-spp-lstm3.pt`: Agot weights copied to triple LSTM architecture

## Part 1: Baseline YOLO (non-recurrent)
Switch to the `non-recurrent` branch.

#### Dataset Formatting

1. Load each annotated video into CVAT. See [CVAT/CVAT setup instructions.txt](CVAT/CVAT%20setup%20instructions.txt) for more information.
2. Export each annotated video in YOLO format
3. Place the unzipped, exported datasets into a single folder accessible by the yolov3 code.
    1. If you want to use the existing paths in [custom/train.txt](custom/train.txt) and [custom/valid.txt](custom/valid.txt), then set up the directory structure such that from yolov/custom:
        * the path to \*.jpg for "task5" is `../../tasks/tasks/task5/*.jpg`
        * the path to \*.jpg for "task6" is `../../tasks/task6/obj_train_data/*.jpg`

    2. If you want to regenerate [custom/train.txt](custom/train.txt) and [custom/valid.txt](custom/valid.txt), you should put the exported datasets into a single folder, then modify and run [custom/format.py](custom/format.py). This script recursevly searches for images in the directory specified by `TASKS_DIR` and separates the data into training/validation according to the fraction specified by `TRAIN_SPLIT`. The `BATCH_SIZE` of 128 means that every 128 frames are either in training or validation, and not separated.

#### Training
Run: `python train.py --epochs 30 --batch-size 128 --accumulate 1 --cfg custom/yolov3-spp-nonrecurrent.cfg --data custom/custom.data`

This will train using the initial weights in `weights/yolov3-spp-ultralytics.pt`. Use the pretrained Agot weights by adding the flag `--weights weights/yolov3-spp-nonrecurrent.pt`. Use no initial weights with the flag `--weights ''`. While training, the most recent weights are stored in `weights/last.pt` and the best weights (based on the validation set) are stored in `weights/best.pt`. If you want to resume training from where it last left off, add the `--resume` flag. Other command line options can be found in yolov3/train.py.

#### Testing
Run: `python test.py --cfg custom/yolov3-spp-nonrecurrent.cfg --data custom/custom.data --weights weights/yolov3-spp-custom.pt --batch-size 128`

This will run the model on the validation set and output metrics. You can see our output in the file [Yolo Baseline Results.xlsx](Yolo%20Baseline%20Results.xlsx).

#### Detection
Run: `python detect.py --cfg custom/yolov3-spp-nonrecurrent.cfg --names custom/custom.names --weights weights/yolov3-spp-custom.pt --source <source video or image>`

This runs the model on an input image or video and outputs another image or video with drawn labels and boxes. The output is stored in the `output` directory.

#### Tips
- Most of our changes are in the [custom](custom) directory. For more information on what changed, you can diff between the `base` branch and the `nonrecurrent` branch.
- We had to reduce the GLOU loss gain and disabled mixed precision in order to avoid gradients going to infinity. We're not sure why.
- Training should take 15 minutes per epoch on 4 NVIDIA Tesla V100 GPUs. We achieved peak accuracy within 30 epochs.
- Using Apex did not improve training speed.
- Using the `--cache-images` flag did not improve training speed.

## Part 2: Recurrent YOLO
Switch to the `master` branch.

This branch uses a hybrid shuffling mechanism and a Convolutional LSTM, as described in the paper. The ConvLSTM implementation is in [convlstm.py](convlstm.py), and incoporated into [models.py](models.py). The hybrid shuffling preprocessing is done using [generate_clips.py](generate_clips.py), which generates numpy files of train/valid paths. The data loading is done using `VideoDataLoader` in [utils/datasets.py](utils/datasets.py), which makes use of a modified version of the original `LoadImagesAndLabels` Dataset. See the paper for details on the hybrid shuffling mechanism.

#### ConvLSTM and Hybrid Shuffling files
- [convlstm.py](convlstm.py): convolutional lstm implementation
- [models.py](models.py): modified to incoporate convlstm
- [utils/datasets.py](utils/datasets.py): added VideoDataLoader and modified LoadImagesAndLabels dataset
- [custom/train.npy](custom/train.npy): image paths for each training clip
- [custom/valid.npy](custom/valid.npy): image paths for each validation clip
- [custom/custom.data](custom/custom.data): modified to refer to the above npy files
- [custom/generate_clips.py](custom/generate_clips.py): generate train/valid clips

#### Model configuration files
- [custom/yolov3-spp-lstm1.cfg](custom/yolov3-spp-lstm1.cfg): model configuration for single ConvLSTM
- [custom/yolov3-spp-lstm2.cfg](custom/yolov3-spp-lstm2.cfg): model configuration for two stacked ConvLSTMs
- [custom/yolov3-spp-lstm3.cfg](custom/yolov3-spp-lstm3.cfg): model configuration for three stacked ConvLSTMs

#### Pretrained weight files
These are weight files for the recurrent architectures, with all weights prior to the ConvLSTM layers copied from the best weights for the nonrecurrent architecture. See the [Prerequisites](#Prerequisites) section for how to obtain these weight files.

- `weights/yolov3-spp-lstm1.pt`: initial weights for single ConvLSTM
- `weights/yolov3-spp-lstm2.pt`: initial weights for two stacked ConvLSTM
- `weights/yolov3-spp-lstm3.pt`: initial weights for three stacked ConvLSTM
- [copy_model.py](copy_model.py): use this helper script to convert model weights for one Recurrent YOLO architecture to weights for another new architecture, by copying all weights other than those of the ConvLSTM layer. For example, this was used to generate yolov3-spp-lstm2.pt and yolov3-spp-lstm3.pt from yolov3-spp-lstm1.pt.

#### Training/Testing/Detection
The training/testing/detection procedure is the same as before, but you'll want to change the model configuration to one of the mentioned `.cfg` files and the initial weights to the matching `.pt` file.

#### Notes
- cannot use multiple GPUs
- takes 2 hours per epoch on a Tesla V100 GPU
- 0% precision/recall/mAP after 30 epochs
- see the paper for potential improvements to this architecture
- check the conv-lstm and hybrid shuffling implementations for bugs
- even trying to overfit on a small subset of data doesn't work; troubling
