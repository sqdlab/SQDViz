Some notes:

- [PySide vs. PyQT](https://www.pythonguis.com/faq/pyqt6-vs-pyside6/)
- [Embedding PyQTGraph into QT](https://www.pythonguis.com/tutorials/embed-pyqtgraph-custom-widgets-qt-app/) - needs a [casting hack](https://stackoverflow.com/questions/61036166/embeding-pyqtgraph-in-qt-designer-using-pyside2) to let it work in PySide
- [Get QT Designer](https://build-system.fman.io/qt-designer-download)

Nice starter tutorials:
- https://www.pythonguis.com/tutorials/plotting-pyqtgraph/
- 

Okay 2D plots with uneven axes does not seem to be a feature - it's just an image...
- [Plottr doesn't do it](https://github.com/toolsforexperiments/plottr/blob/master/plottr/plot/pyqtgraph/plots.py)
- [This lad didn't get an answer either](https://stackoverflow.com/questions/63619065/pyqtgraph-use-arbitrary-values-for-axis-with-imageitem)

Icons:
- Use QT Designer and action editor to specify buttons with icons in the toolbar
- [The QRC file needs to be compiled and imported for the icons to show](https://www.pythonguis.com/tutorials/pyside-qresource-system/). The *Qt for Python* VSCode extension already does this automatically...
