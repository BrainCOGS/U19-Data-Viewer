from viewer.utils import *
from viewer.modules import subject, behavior


def psych_curve(psych_data, psych_error, psych_fit, title, label=None):

    p = figure(plot_width=550, plot_height=300,
               title=title,
               x_axis_label='#R - #L',
               y_axis_label='% went R')

    p.y_range = Range1d(0, 100)

    fit_plot = p.line(x='x', y='y',
                      source=psych_fit, color='gray', legend_label='Fit')

    error_plot = p.line(x='x', y='y',
                        source=psych_error, color='gray', legend_label='Data')

    data_plot = p.scatter(x='x', y='y',
                          source=psych_data, color='black', legend_label='Data')

    if label:
        subject_label = Label(x_offset=-180, y_offset=200, text=label, text_font_size='9pt')
        p.add_layout(subject_label)

    p.xgrid.grid_line_color = None
    p.outline_line_color = None


    p.legend.location = (330, 10)

    if label:
        return p, [data_plot, error_plot, fit_plot, subject_label]
    else:
        return p, [data_plot, error_plot, fit_plot]
