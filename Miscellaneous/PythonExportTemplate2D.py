import numpy as np
import matplotlib.pyplot as plt
import matplotlib

raw_data = np.load('LEFILENAME', allow_pickle=True)

x_data = raw_data.item().get('x_data')
y_data = raw_data.item().get('y_data')
z_data = raw_data.item().get('z_data').T
#CURSORPREPARE
x_cursors = raw_data.item().get('cursor_x')
y_cursors = raw_data.item().get('cursor_y')
#CURSORPREPARE

pltKwargs = {}
pltKwargs['cmap'] = LECUSTOMCOLOURMAP

#HISTNORM
colMapMkrs = np.array(raw_data.item().get('colorbar'))
func_yinterp = lambda x: np.interp(x, colMapMkrs, np.linspace(0,1,colMapMkrs.size))
func_yinterpInv = lambda x: np.interp(x, np.linspace(0,1,colMapMkrs.size), colMapMkrs)
normFunc = matplotlib.colors.FuncNorm((func_yinterp, func_yinterpInv), vmin=0, vmax=1)
zMin, zMax = np.nanmin(z_data), np.nanmax(z_data)
z_data = (z_data-zMin)/(zMax-zMin)
pltKwargs['norm'] = normFunc
#HISTNORM

fig, ax = plt.subplots(1)
ax.pcolormesh(x_data, y_data, z_data, **pltKwargs)
#CURSORPLOT
#
fig, ax = plt.subplots(1)
for x_curse in x_cursors:
    ax.plot(x_data, x_curse)
#
fig, ax = plt.subplots(1)
for y_curse in y_cursors:
    ax.plot(y_data, y_curse)
#CURSORPLOT

plt.show()
