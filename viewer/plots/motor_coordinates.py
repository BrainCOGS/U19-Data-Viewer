from viewer.modules import action
from viewer.utils import *


# Coordinate columns of action.DailySubjectPositionData, with the colors used
# to distinguish them both within a plot and across compared subjects.
COORDINATES = [('ml_position', 'ML', '#1f77b4'),
               ('ap_position', 'AP', '#d62728'),
               ('dv_position', 'DV', '#2ca02c')]

default_data = {'capture_times': [np.nan],
                'ml_position'  : [np.nan],
                'ap_position'  : [np.nan],
                'dv_position'  : [np.nan]}


def plot(key=None, plot_filter=None):

    def get_data(key, plot_filter=None):

        position_info = (action.DailySubjectPositionData.proj(
            'capture_time', *[c for c, _, _ in COORDINATES]) &
            key).fetch(format='frame').reset_index()

        if not len(position_info):
            return dict(default_data)

        data_position = pd.DataFrame({
            'capture_times': pd.to_datetime(position_info['capture_time']),
            'ml_position'  : position_info['ml_position'],
            'ap_position'  : position_info['ap_position'],
            'dv_position'  : position_info['dv_position']})
        data_position = data_position.sort_values('capture_times')

        for column, _, _ in COORDINATES:
            data_position[column] = pd.to_numeric(
                data_position[column], errors='coerce')

        return data_position

    def update_view(p, subplot, data_position):
        # Motor coordinates share a single axis but sit at arbitrary offsets, so
        # rescale to the data instead of keeping a fixed range.
        values = np.concatenate([
            np.atleast_1d(np.asarray(data_position[column], dtype=float))
            for column, _, _ in COORDINATES])
        values = values[np.isfinite(values)]

        if not values.size:
            p.y_range.start, p.y_range.end = 0, 1
            return

        low, high = float(values.min()), float(values.max())
        margin = max((high - low) * 0.1, 0.1)
        p.y_range.start, p.y_range.end = low - margin, high + margin

    if key is None:
        key = dict(subject_fullname='emanuele_B208')

    data_position = get_data(key)

    title = 'Motor coordinates over time'
    if plot_filter and plot_filter.get('title'):
        title = plot_filter['title']

    p = figure(x_axis_type="datetime", width=600, height=300,
               title=title,
               x_axis_label='Date',
               y_axis_label='Position [mm]')

    p.xaxis.formatter = DatetimeTickFormatter(days='%m/%d/%y')
    p.y_range = Range1d(0, 1)

    subplots = []
    for column, label, color in COORDINATES:
        line = p.line(x='capture_times', y=column, source=data_position,
                      color=color, legend_label=label)
        dot = p.scatter(x='capture_times', y=column, source=data_position,
                        color=color, size=4, legend_label=label)
        subplots.append((line, get_data, update_view))
        subplots.append((dot, get_data, update_view))

    update_view(p, None, data_position)

    p.xgrid.grid_line_color = None
    p.outline_line_color = None
    p.legend.location = 'top_left'
    p.legend.click_policy = 'hide'

    return p, subplots


if __name__ == '__main__':

    p, subplots = plot()
    show(p)
