# SQDViz

*SQDViz* is the visualisation tool used to slice multidimensional data into 1D or 2D plots. The software also provides:

- Realtime dataprocessing with a completely reconfigurable pipeline (all in-situ) with custom data processors
- Cursors to help view the data cuts along the x and y axes
- Analysis cursors to define regions that link with the realtime data processors

There are additionally UI elements present to make it easy to view data generated from *SQDToolz* and older CSV tables (like that produced by UQTools).

## Installation instructions

The basic requirements are:

- H5PY 3.1.0 - later versions have a file locking issue when using SWMR mode
- NumPy/SciPy - used in the data processing
- Matplotlib - in the older version, this is the actual viewer, while in the newer version it is just there for the colour schemes...

The older version uses Matplotlib and Tkinter (found natively in all Python 3 distributions). However, the latest version utilises QT for a faster experience and the ability to view much larger datasets:

- PySide 6 - this is the free version of QT
- PyQTgraph

Currently **Anaconda is not supported** for there is some bug in QT. To install with normal Python, first install a *Python 3.9* or later distribution for optimal performance (e.g. from [here](https://www.python.org/downloads/release/python-390/); just install into `C:\Python39` etc.). Then create a virtual environment in some folder:

```
C:\Python39\python -m venv name_of_venv
```

Note that if there is only one Python distribution on the system, just use `python` instead of including the path in the above command. Now activate the environment in the usual manner (i.e. run the script `activate` in the /Scripts folder inside the new virtual environment folder) in command line. Now choose a different folder (i.e. not in the virtual environment folder) to house the SQDViz folder (idea is to create an editable folder such that the code can be modified and pushed). Once navigating to this folder, run the usual GIT clone:

```
cd C:/Users/....../myFolder/
git clone https://github.com/sqdlab/sqdviz.git
```

Now (noting that the command line is still inside the active virtual environment), run:

```
cd sqdviz
pip install -r Requirements.txt
```
This should install all required dependencies. Now create a batch file (to create a handy shortcut) with the following commands:

```batch
cd C:/Users/....../myFolder/sqdviz
pathToEnvironment/name_of_venv/python.exe MainFormQT.py
```

Replace *MainFormQT.py* with *Main.py* if one wishes to run the previous Tkinter version.
