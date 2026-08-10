from viewer.modules import subject, acquisition, behavior, puffs
from viewer.utils import *
from viewer import subject_filters


def plot(key=None):

    no_data = {
        'session_dates': [np.nan],
        'performance'  : [np.nan],
        'level'        : [np.nan],
        'n_trials'     : [np.nan]}

    def get_data(key):

        # A subject may have no sessions at all, or sessions across more than
        # one task, so take the tasks as a set rather than assuming exactly one.
        tasks = (dj.U('task') & (acquisition.Session & key)).fetch('task')
        if not len(tasks):
            return dict(no_data)

        if 'AirPuffs' in tasks:
            q = (acquisition.Session & key).aggr(puffs.PuffsSession.Trial.proj(), n_trials='count(*)') * acquisition.Session
        else:
            q = (acquisition.Session & key).proj(..., n_trials='num_trials')

        if len(q):
            performance_info = q.fetch(
                format='frame').reset_index()

            data_performance = pd.DataFrame({
                'session_dates': performance_info['session_date'],
                'performance'  : performance_info['session_performance'],
                'level'        : performance_info['level'],
                'n_trials'     : performance_info['n_trials']})
            data_performance['session_dates'] = pd.to_datetime(data_performance['session_dates'])
        else:
            data_performance = dict(no_data)

        return data_performance

    def update_view(p, subplot, data_performance):

        if subplot.y_range_name == 'default':
            if np.isnan(data_performance['level'][0]):
                p.y_range = Range1d(0, 10, min_interval=2)
            else:
                p.y_range = Range1d(
                    0, max([max(data_performance['level']), 10]), min_interval=2)
        elif subplot.y_range_name == 'performance':
            p.extra_y_ranges[subplot.y_range_name] = Range1d(0, 100)
        else:
            if np.isnan(data_performance[subplot.y_range_name][0]):
                p.extra_y_ranges[subplot.y_range_name] = Range1d(
                    0, 300)
            else:
                p.extra_y_ranges[subplot.y_range_name] = Range1d(
                    0, max([300, max(data_performance[subplot.y_range_name])]))

    BASE_TITLE = 'Performance, trial counts, and task level'

    def get_title(key):
        '''
        Name the rig(s) the subject trained on in the title. Usually one, but a
        subject can move between rigs, so all are listed most-used first.
        '''
        rigs = subject_filters.rigs_of(key.get('subject_fullname'))
        if not rigs:
            return BASE_TITLE
        return '{} — rig: {}'.format(BASE_TITLE, ', '.join(rigs))

    if key is None:
        key = dict(subject_fullname='emanuele_B208')

    data_performance = get_data(key)

    p = figure(x_axis_type="datetime", width=600, height=300,
               title=get_title(key),
               x_axis_label='Date',
               y_axis_label='Task level', y_axis_location='right')

    p.xaxis.formatter = DatetimeTickFormatter(days='%m/%d/%y')

    p.y_range = Range1d(0, max([max(data_performance['level']), 10]), min_interval=2)
    level_plot = p.vbar(
        x='session_dates', top='level',
        source=data_performance, color='lightblue',
        legend_label='Level', width=datetime.timedelta(days=0.4))

    p.extra_y_ranges['performance'] = Range1d(0, 100)
    p.extra_y_ranges['n_trials'] = Range1d(0, max([300, max(data_performance['n_trials'])]))

    p.add_layout(LinearAxis(y_range_name="performance",
                            axis_label='Performance [%]'), 'left')
    p.add_layout(LinearAxis(y_range_name="n_trials",
                            axis_label='Trial counts'), 'left')

    performance_plot_line = p.line(
        x='session_dates', y='performance', y_range_name='performance',
        source=data_performance, color='gray', legend_label='Performance')

    performance_plot_dot = p.scatter(
        x='session_dates', y='performance', y_range_name='performance',
        source=data_performance, color='black', legend_label='Performance')

    trial_counts_plot_line = p.line(
        x='session_dates', y='n_trials', y_range_name='n_trials',
        source=data_performance, color='pink', legend_label='Trial counts')

    trial_counts_plot_dot = p.scatter(
        x='session_dates', y='n_trials', y_range_name='n_trials',
        source=data_performance, color='red', legend_label='Trial counts')

    p.xgrid.grid_line_color = None
    p.outline_line_color = None

    p.legend.location = (290, 10)

    # p.title has no data_source, so UpdatableFigure falls through to setting
    # .text on it: that is how the rig name follows the selected subject.
    return p, [(performance_plot_line, get_data, update_view),
               (performance_plot_dot, get_data, update_view),
               (trial_counts_plot_line, get_data, update_view),
               (trial_counts_plot_dot, get_data, update_view),
               (level_plot, get_data, update_view),
               (p.title, get_title, None)]


if __name__ == '__main__':

    p, subplots = plot()
    show(p)
