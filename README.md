# morphing

This program creates morphing between two images

To run the program paste in your command line:

```python gui.py "before.jpg" "after.jpg"```

The gui provides differenet buttons:

1) Add constraint points - to add 2 constraint points you should make double click on the first image and after that double click on the second (otherwise nothing happens). Other buttons disable adding constraint points,  but before pressing them, you can add big amount of constraint pairs.
2) Hide constraints points - all lines and constraint points will be hidden
3) Show constraints points - all lines and constraint points will be shown
4) Start morphing - morphing process will be started (with number of frames are displayed)
5) Buttons for changing frames number (it's not recommended to set it too big because of poor speed of computations)
6) Close program - button from closing the program