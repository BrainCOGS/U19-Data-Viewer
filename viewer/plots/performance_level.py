from viewer.modules import subject, acquisition
from viewer.utils import *


def plot(key=None):

    def get_data(key):

        q = acquisition.Session & key

        if len(q):
            performance_info = q.fetch(
                format='frame').reset_index()

            data_performance = {
                'session_dates': performance_info['session_date'].to_list(),
                'performance'  : performance_info['session_performance'].to_list(),
                'level'        : performance_info['level']}
        else:
            data_performance = {
                'session_dates': [np.nan],
                'performance'  : [np.nan],
                'level'        : [np.nan]}

        return data_performance

    if key is None:
        key = dict(subject_fullname='emanuele_B208')

    data_performance = get_data(key)

    p = figure(x_axis_type="datetime", plot_width=600, plot_height=300, title='Performance and task level',
            x_axis_label = 'Date',
            y_axis_label = 'Task level', y_axis_location='right')
    p.y_range = Range1d(0, 10, min_interval=2)
    level_plot = p.vbar(
        x='session_dates', top='level',
        source=data_performance, color='lightblue',
        legend_label='Level', width=datetime.timedelta(days=0.4))

    p.extra_y_ranges['performance'] = Range1d(0, 100)
    p.add_layout(LinearAxis(y_range_name="performance",
                            axis_label='Performance [%]'), 'left')

    performance_plot_line = p.line(
        x='session_dates', y='performance', y_range_name='performance',
        source=data_performance, color='gray', legend_label='Performance')

    performance_plot_dot = p.scatter(
        x='session_dates', y='performance', y_range_name='performance',
        source=data_performance, color='black', legend_label='Performance')

    p.xgrid.grid_line_color = None
    p.outline_line_color = None

    p.legend.location = (320, 10)

    return p, [(performance_plot_line, get_data), (performance_plot_dot, get_data), (level_plot, get_data)]


if __name__ == '__main__':

    p, subplots = plot()
    show(p)
