# autoRM: an Automatic Retinotopic Mapping Tool for Mice

version 1.0

release date 2021/4/19

written by Ruix. Li

---
**autoRM** provides a fully automatic tool for mice retinotopic mapping. It can help you to locate the primary and several higher-order visual cortex of mice with calcium or optical imaging (figure from ref [1]).
![visual areas of mouse](./imgs/_mouseVisualAreas.jpg)

## What you need to use autoRM

1. **Psychopy3** (>=2020.1.3) to present visual stimulus
2. **NI-DAQ** USB-6501 digital I/O Device and NI-DAQmx driver for synchronization
3. **MATLAB** (>=2018a) with image processing toolbox

## The content of autoRM

* `RetinotopicMappingv5.py` is a Python script to present visual stimulus for retinotopic mapping, a typical experiment last about 30 minutes.
* `RMDegMap.m` is a MATLAB function to calculate visual degree, naming **azimuth** and **elevation**.
* `RMSetParam.m` is a MATLAB app helps you to determine parameters used in `RMAreaMAp.m`.
* `RMAreaMap.m` is a MATLAB function to identify visual areas, see ref [2] for details.
* `autoRM.m` is ***the MATLAB function you use***, it calls `RMDegMap` `RMSetParam` and `RMAreaMap`, usually you don't need to use other functions.

## How to use

1. MATLAB image processing toolbox is required.
2. Run `RetinotopicMappingv5.py` with psychopy3 before start recording. Recommend using a NI-DAQ digital I/O device to synchronize your camera with the visual stimulus.
3. The Python program will return the frame number required for recording. ***Set the frame number in your camera control interface.***

![psychopy set frame number](./imgs/_psychopyInterface.jpg)

4. After stimulus finish, `RetinotopicMappingv5.py` will save a txt log file and a json configuration file. ***The json file is required in the following steps.***
5. Convert your recording data into .mat data.
6. Add `RMDegMap.m`, `RMSetParam.m` and `RMAreaMap.m` to your MATLAB path, then just call `autoRM` in MATLAB command window and follow the instructions to select recording data `.mat` file and `.json` configration files.
7. A GUI will pop-up for you to adjust parameters.

![adjust parameter](./imgs/_parameterInterface.jpg)

8. `autoRM` will create a figure for you at the path of `.json` config file. This figure can be used as retinotopic mapping reference for your subsequential experiments.

![final results](./imgs/_areaMapResult.jpg)

---

## Endnote

References:

[1] Marshel, James H., et al. "Functional specialization of seven mouse visual cortical areas." Neuron 72.6 (2011): 1040-1054.

[2] Juavinett, Ashley L., et al. "Automated identification of mouse visual areas with intrinsic signal imaging." Nature protocols 12.1 (2017): 32.

[3] Zhuang, Jun, et al. "An extended retinotopic map of mouse cortex." Elife 6 (2017): e18372.
