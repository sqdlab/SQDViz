import numpy as np
import matplotlib.pyplot as plt

raw_data = np.load('LEFILENAME', allow_pickle=True)

x_data = raw_data.item().get('x_data')
y_data = raw_data.item().get('y_data')

fig, ax = plt.subplots(1)
ax.plot(x_data, y_data)

plt.show()
