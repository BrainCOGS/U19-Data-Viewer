from viewer.utils import *
from viewer.modules import *
from viewer.plots import water_weight, performance_level, subject_psych_curve
from viewer.updatable_figures import *


def subject_tab():

    def get_data_df(filter):

        df = pd.DataFrame((subject.Subject & filter).fetch(
            'subject_fullname', 'user_id', 'sex', 'dob', 'location', 'line',
            as_dict=True))
        df['dob'] = pd.to_datetime(df['dob'], errors='coerce').dt.strftime('%Y-%m-%d')
        df['dob'] = df['dob'].replace('NaT', 'Unknown')
        return df

    all_subjects = (subject.Subject).fetch('subject_fullname').tolist()
    subjects = Select(title='Subject:', value='All', options=['All'] + all_subjects,
                      width=150)

    all_owners = (dj.U('user_id') & subject.Subject).fetch('user_id').tolist()
    owners = Select(title='Owner:', value='All', options=['All'] + all_owners,
                    width=150)

    levels = Select(title='Level', value='All', options=['All'], width=150)

    current_filter = dict()

    source = ColumnDataSource(get_data_df(current_filter))
    source.selected.indices = [5]
    current_subject_fullname = source.data['subject_fullname'][5]

    # Table for displaying subjects
    columns = [
        TableColumn(field="subject_fullname", title="Subject"),
        TableColumn(field="dob", title="DOB"),
        TableColumn(field="sex", title="Gender"),
        TableColumn(field="user_id", title="Owner"),
        TableColumn(field="location", title="Location"),
        TableColumn(field="line", title="Line")
    ]

    figure_collection = UpdatableFigureCollectionFactory() \
        .add_figure_creator(water_weight.plot) \
        .add_figure_creator(performance_level.plot) \
        .add_figure_creator(subject_psych_curve.plot, dict(level='All')) \
        .build()

    def update_level_filter(subj):

        nonlocal levels
        nonlocal figure_collection
        task = (dj.U('task') & (acquisition.Session & dict(subject_fullname=subj))).fetch('task')[0]
        if task == 'AirPuffs':
            all_levels = list((dj.U('psych_level') &
                               (puffs.PuffsSubjectCumulativePsychLevel &
                                dict(subject_fullname=subj))).fetch('psych_level'))
        elif task == 'Towers':
            all_levels = list((dj.U('psych_level') &
                               (behavior.TowersSubjectCumulativePsychLevel &
                                dict(subject_fullname=subj))).fetch('psych_level'))
        else:
            all_levels = []

        all_levels_str = [str(level) for level in all_levels]
        levels_options = ['All'] + all_levels_str
        levels_value = levels.value
        if levels_value not in levels_options:
            levels_value = 'All'
        levels.options = levels_options
        levels.value = 'All'

        figure_collection.updatable_list[2][1] = dict(level=levels.value)
        levels.value = levels_value

    def callback_filter(attr, old, new, field):

        if field in current_filter.keys():
            current_filter.pop(field)

        if new != 'All':
            current_filter[field] = new

        source.data = get_data_df(current_filter)
        subjs = source.data['subject_fullname']
        if len(subjs) == 1:
            source.selected.indices = [0]
            figure_collection.update(dict(subject_fullname=subjs[0]))

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

    def callback_level_filter(attr, old, new):

        figure_collection.updatable_list[2][1] = dict(level=new)
        figure_collection.updatable_list[2][0].update(
            dict(subject_fullname=current_subject_fullname), dict(level=new))

    def callback_update_data(attr, old, new):
        nonlocal current_subject_fullname
        try:
            selected_index = source.selected.indices[0]
            current_subject_fullname = str(source.data['subject_fullname'][selected_index])
            update_level_filter(current_subject_fullname)
            figure_collection.update(dict(subject_fullname=current_subject_fullname))
        except IndexError:
            pass

    # callback functions
    figure_collection.update(dict(subject_fullname=current_subject_fullname))

    source.selected.on_change('indices', callback_update_data)

    subjects.on_change('value', partial(callback_filter, field='subject_fullname'))

    owners.on_change('value', partial(callback_filter, field='user_id'))

    levels.on_change('value', callback_level_filter)

    data_table = DataTable(
        source=source,
        columns=columns,
        width=800,
        height=800)

    return Panel(child=layout(row(column(row(owners, subjects), data_table),
                                  column(figure_collection.updatable_list[0][0].fig,
                                         figure_collection.updatable_list[1][0].fig,
                                         levels,
                                         figure_collection.updatable_list[2][0].fig))), title='Subject')
