from cv2 import rotate
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.colors as mcolors
DARK_GREEN = 'darkgreen'
GREEN = 'green'
YELLOW = 'yellow'
RED = 'red'
profiler_times = {
    "Profile":          40,
    "yappi CPU":        5,
    "yappi wallclock":  3,
    "pprofile (det)":   40,
    "cProfile":         2,
    "pyinstrument":     1.5,
    "line\_profiler":   7,
    # "SNOOPY":           1.2,
    "py-spy":           1,
    "SnooPy":    1.2,
    "Austin":           1,
    "pprofile (stat)":  1,
}
profiler_colors = {
    "Profile":          RED,
    "yappi CPU":        YELLOW,
    "yappi wallclock":  YELLOW,
    "pprofile (det)":   RED,
    "cProfile":         YELLOW,
    "pyinstrument":     GREEN,
    "line\_profiler":   YELLOW,
    "py-spy":           DARK_GREEN,
    "SnooPy":    DARK_GREEN,
    "Austin":           DARK_GREEN,
    "pprofile (stat)":  DARK_GREEN,
}
monospace_font = 'Andale Mono' # 'Courier New'
default_font = 'Arial'

# x_labelparams = {'style' : 'italic', 'weight' : 'bold', 'font' : default_font, 'size' : 12 }
y_labelparams = {'style' : 'italic', 'weight' : 'bold', 'font' : default_font, 'size' : 12 }
title_params = {'weight' : 'bold', 'font' : default_font, 'size' : 18 }
subtitle_params = {'weight' : 'bold', 'font' : default_font, 'size' : 16 }
x_label = plt.xlabel("data type")# , x_labelparams)
y_label = plt.ylabel("Overhead (multiple of Python runtime)", y_labelparams)


def graph():
    profiler_colors_t = [(color, profiler_times[name]) for name, color in profiler_colors.items()]
    profiler_items = sorted(list(profiler_times.items()), key= lambda x : x[1])
    print(profiler_items)
    sorted_profiler_colors =  [z[0] for z in sorted(profiler_colors_t, key= lambda x : x[1])]
    sns.set(font=default_font,
    rc={
        'font.size' : 16,
        'axes.titlesize' : 24,
        # 'axes.labelsize' : 14,
        'axes.axisbelow': False,
        'axes.edgecolor': 'lightgrey',
        'axes.facecolor': 'None',
        'axes.grid': False,
        'axes.labelcolor': 'dimgrey',
        'axes.spines.right': False,
        'axes.spines.top': False,
        'figure.facecolor': 'white',
        'lines.solid_capstyle': 'round',
        'patch.edgecolor': 'w',
        'patch.force_edgecolor': True,
        'text.color': 'black',
        'xtick.bottom': False,
        'xtick.color': 'dimgrey',
        'xtick.direction': 'out',
        'xtick.top': False,
        'ytick.color': 'dimgrey',
        'ytick.direction': 'out',
        'ytick.left': False,
        'ytick.right': False})

    # from graphdefaults import *
    plt.style.use('ggplot')
    width = 0.35
    # font_params = {'font.family' : default_font, 'font.size' : 14 } # Courier New' }
    # plt.rcParams.update(font_params)
    # legend = plt.legend() 
    # plt.setp(legend.get_texts(), fontsize='14', family=default_font)
    ax = plt.gca()
    xs, ys = list(zip(*profiler_items))
    ys = list(map(round, ys))
    ind = np.arange(len(ys))
    x_ticks = plt.xticks(list(range(len(xs))), xs, rotation=90)
    print(sorted_profiler_colors)
    b1 = plt.bar(ind, ys, color=sorted_profiler_colors)
    ax.bar_label(b1,  color='black')
    for tick in ax.get_xticklabels():
        tick.set_fontweight("bold")
        tick.set_horizontalalignment("left")
    plt.savefig('plots/bars.pdf')

if __name__ == '__main__':
    graph()