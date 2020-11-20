from viewer.modules import subject, action
from viewer.utils import *


def plot(key=None):

    def get_water_data(key):
        water_info = (action.WaterAdministration & key).fetch(format='frame').reset_index()
        data_water = {'water_dates': water_info['administration_date'].to_list(),
                      'earned'     : water_info['earned'].to_list(),
                      'supplement' : water_info['supplement'].to_list(),
                      'received'   : water_info['received'].to_list()}

        return data_water

    def get_weight_data(key):
        weight_info = (action.Weighing.proj('weight') &
                       key).fetch(format='frame').reset_index()

        data_weight = {'weighing_dates': weight_info['weighing_time'].to_list(),
                       'weight'        : weight_info['weight'].to_list()}
        return data_weight


    water_methods = ['earned', 'supplement', 'received']
    colors = ["#c9d9d3", "#718dbf", "#e84d60"]

    if key is None:
        key = dict(subject_fullname='emanuele_B208')

    data_water = get_water_data(key)
    data_weight = get_weight_data(key)

    p = figure(x_axis_type="datetime", plot_width=600, plot_height=300, title='Water and Weight',
               x_axis_label='Date',
               y_axis_label='Water Intake [mL]')
    p.y_range = Range1d(0, 5)
    water_plot = p.vbar_stack(
        water_methods, x='water_dates',
        width=datetime.timedelta(days=0.4),
        color=colors, source=data_water,
        legend_label=water_methods)

    p.xgrid.grid_line_color = None
    p.outline_line_color = None
    p.legend.location = (20, 180)
    p.legend.orientation = "horizontal"

    p.extra_y_ranges['weight'] = Range1d(20, 35)
    p.add_layout(LinearAxis(y_range_name="weight",
                            axis_label='Weight [g]'), 'right')

    weight_plot = p.scatter(x='weighing_dates', y='weight',
                            y_range_name="weight",
                            source=data_weight, color='black')

    return p, [(water_plot, get_water_data, None),
               (weight_plot, get_weight_data, None)]


if __name__ == '__main__':

    p, subplots = plot()
    show(p)
