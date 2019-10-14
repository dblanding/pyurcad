# pyurcad
PYurCAD (pronounced PureCAD) requires only python3 (tested with 3.5.3) and the
python standard libraries. It is a rewrite of Cadvas version 0.5.2 but without
the use of the AppShell framework (and Python Mega Widgets).
The impetus to do this came after I discovered a 3D graphics example in Bhaskar
Chaudhary's recent book: "Tkinter GUI Application Development Blueprints, 2nd 
Edition". I had not realized that it was possible to do 3D graphics on the
tkinter canvas. In his book, he also presents a "Paint" app which has a simple,
clean and functional interface that I thought would work well for my CAD app.
So here is the result of a couple of days of effort, the first step toward what
will hopefully become a 3D CAD application written in Pure Python.

Since no additional libraries are required, running it is very simple.
Just download (or clone) this repository and run the file pyurcad.py.

Further research on the topic of "3D graphics on tkinter canvas" turned up
https://sites.google.com/site/3dprogramminginpython/ which shows several
interesting 3D examples (for Python2). My next goal is to extend PyurCad to
be able to extrude and display some basic 3D shapes.