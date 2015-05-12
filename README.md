Required python 2.7 modules:
    - IPython
    - numpy
    - matplotlib
    - sklearn
    - skimage

HOW TO RUN:
-----------

Run cmm.py
>> python cmm.py


Configuring: (scroll towards the end of cmm.py)
Edit pieces in cmm.py to select source pieces:
    pieces = ["mid/hilarity.mid", "mid/froglegs.mid", "mid/easywinners.mid"]

Toggle between two modes: mixture or segmentation (I haven't had a chance to figure out a way to combine the two):
    segmentation = True
    all_keys = False


NOTES:
------

- The cached folder holds cached computations. Delete them if they are costing you problems. Note that recalculating stuff will take a while.

- All midi files in mid are properly quantized (i.e. each note type has a regular number of ticks). The music generation system requires that additional midi files must also be properly quantized to function properly.

