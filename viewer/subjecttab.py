from utils import *

def subject_tab():
    '''
    Creates the tab to view all subjects
    '''
    subject = dj.create_virtual_module('subject', 'u19_subject')
    action = dj.create_virtual_module('action', 'u19_action')

    all_subjects = (subject.Subject).fetch('subject_fullname').tolist()
    subjects = Select(title='Subject:',value = 'All', options = ['All'] + all_subjects,
                      width = 150)

    all_owners = (dj.U('user_id') & subject.Subject).fetch('user_id').tolist()
    owners = Select(title='Owner:',value = 'All', options = ['All'] + all_owners,
                    width = 150)

    current_filter = dict()

    def get_data_df(filter):

        return pd.DataFrame((subject.Subject & filter).fetch(
            'subject_fullname', 'user_id','sex', 'dob', 'location', 'line',
            as_dict=True))

    source = ColumnDataSource(get_data_df(current_filter))

    # Table for displaying subjects
    columns = [
        TableColumn(field="subject_fullname", title="Subject"),
        TableColumn(field="dob", title="DOB", formatter=DateFormatter()),
        TableColumn(field="sex", title="Gender"),
        TableColumn(field="user_id", title="Owner"),
        TableColumn(field="location", title="Location"),
        TableColumn(field="line", title="Line")
    ]

    def callback_filter(attr, old, new, field):

        if field in current_filter.keys():
            current_filter.pop(field)

        if new != 'All':
            current_filter[field] = new

        source.data = get_data_df(current_filter)

        if field == 'subject_fullname':
            if new != 'All':
                owner = (subject.Subject & 'subject_fullname="{}"'.format(new)).fetch('user_id').tolist()
                owners.options = ['All'] + owner
            else:
                all_owners = (dj.U('user_id') & subject.Subject).fetch('user_id').tolist()
                owners.options = ['All'] + all_owners

        if field == 'user_id':
            if new != 'All':
                all_subjects = (subject.Subject & 'user_id="{}"'.format(new)).fetch('subject_fullname').tolist()
                subjects.options = ['All'] + all_subjects
            else:
                all_subjects = subject.Subject.fetch('subject_fullname').tolist()
                subjects.options = ['All'] + all_subjects


    def create_water_weight_data(subject_fullname):
        subj = subject.Subject & {'subject_fullname': subject_fullname}
        water_info = (action.WaterAdministration & subj).fetch(format='frame').reset_index()
        weight_info = (action.Weighing.proj('weight') &
                       subj.proj()).fetch(format='frame').reset_index()

        data_water = {'water_dates': water_info['administration_date'].to_list(),
                      'earned'     : water_info['earned'].to_list(),
                      'supplement' : water_info['supplement'].to_list(),
                      'received'   : water_info['received'].to_list(),
                    }
        data_weight = {'weighing_dates': weight_info['weighing_time'].to_list(),
                       'weight'        : weight_info['weight'].to_list()
                    }

        return data_water, data_weight

    water_methods = ['earned', 'supplement', 'received']
    colors = ["#c9d9d3", "#718dbf", "#e84d60"]

    subjs = subject.Subject.fetch('subject_fullname')

    data_water, data_weight = create_water_weight_data(subjs[0])

    p = figure(x_axis_type="datetime", plot_width=600, plot_height=300, title='Water and Weight',
               x_axis_label = 'Date',
               y_axis_label = 'Water Intake [mL]')
    p.y_range = Range1d(0, 5)
    water_plot = p.vbar_stack(water_methods, x='water_dates',
                              width=datetime.timedelta(days=0.4),
                              color=colors, source=data_water,
                              legend_label=water_methods)

    p.x_range.range_padding = 0.1
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

    def callback_update_water_weight(attr, old, new):
        try:
            selected_index = source.selected.indices[0]
            subject_fullname = str(source.data['subject_fullname'][selected_index])

            data_water, data_weight = create_water_weight_data(subject_fullname)

            for i in np.arange(3):
                water_plot[i].data_source.data = data_water

            weight_plot.data_source.data = data_weight

        except IndexError:
            pass

    source.selected.on_change('indices', callback_update_water_weight)

    subjects.on_change('value', partial(callback_filter, field='subject_fullname'))

    owners.on_change('value', partial(callback_filter, field='user_id'))

    data_table = DataTable(
        source=source,
        columns=columns,
        width=800,
        height=600)

    return Panel(child=layout(row(column(row(owners, subjects), data_table), p)), title='Subject')
