from viewer.utils import *
from viewer.modules import *
from viewer.plots import water_weight, performance_level, subject_psych_curve
from viewer.updatable_figures import *


def subject_tab():
    '''
    Creates the tab to view all subjects
    '''

    all_subjects = (subject.Subject).fetch('subject_fullname').tolist()
    subjects = Select(title='Subject:',value = 'All', options = ['All'] + all_subjects,
                      width = 150)

    all_owners = (dj.U('user_id') & subject.Subject).fetch('user_id').tolist()
    owners = Select(title='Owner:',value = 'All', options = ['All'] + all_owners,
                    width = 150)

    current_filter = dict()

    def get_data_df(filter):

        return pd.DataFrame((subject.Subject & filter).fetch(
            'subject_fullname', 'user_id', 'sex', 'dob', 'location', 'line',
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

    def callback_update_data(attr, old, new):
        try:
            selected_index = source.selected.indices[0]
            subject_fullname = str(source.data['subject_fullname'][selected_index])
            figure_collection.update(dict(subject_fullname=subject_fullname))

        except IndexError:
            pass

    figure_collection = UpdatableFigureCollectionFactory() \
        .add_figure_creator(water_weight.plot) \
        .add_figure_creator(performance_level.plot) \
        .add_figure_creator(subject_psych_curve.plot) \
        .build()

    figure_collection.update(dict(subject_fullname=all_subjects[0]))

    source.selected.on_change('indices', callback_update_data)

    subjects.on_change('value', partial(callback_filter, field='subject_fullname'))

    owners.on_change('value', partial(callback_filter, field='user_id'))

    data_table = DataTable(
        source=source,
        columns=columns,
        width=800,
        height=800)

    return Panel(child=layout(row(column(row(owners, subjects), data_table),
                                  column(figure_collection.updatable_list[0].fig,
                                         figure_collection.updatable_list[1].fig,
                                         figure_collection.updatable_list[2].fig))), title='Subject')
