from viewer.utils import *
from viewer.modules import *
from viewer.plots import (water_weight, performance_level, subject_psych_curve,
                          motor_coordinates, subject_photos)
from viewer.updatable_figures import *
from viewer.busy_indicator import BusyIndicator


def subject_tab():

    table_columns = ['subject_fullname', 'user_id', 'sex', 'dob', 'location',
                     'line']

    def get_data_df(filter):

        df = pd.DataFrame((subject.Subject & filter).fetch(
            *table_columns, as_dict=True))
        if not len(df):
            # A filter combination can match nothing; keep the columns so the
            # table and its callbacks still have something well-formed to read.
            return pd.DataFrame({column: [] for column in table_columns})
        df['dob'] = pd.to_datetime(df['dob'], errors='coerce').dt.strftime('%Y-%m-%d')
        df['dob'] = df['dob'].replace('NaT', 'Unknown')
        return df

    all_subjects = (subject.Subject).fetch('subject_fullname').tolist()
    subjects = Select(title='Subject:', value='All', options=['All'] + all_subjects,
                      width=150)

    all_owners = (dj.U('user_id') & subject.Subject).fetch('user_id').tolist()
    owners = Select(title='Owner:', value='All', options=['All'] + all_owners,
                    width=150)

    all_sexes = [s for s in ('Male', 'Female', 'Unknown')
                 if subject.Subject & dict(sex=s)]
    sexes = Select(title='Sex:', value='All', options=['All'] + all_sexes,
                   width=150)

    all_rigs = (dj.U('location') & subject.Subject).fetch('location').tolist()
    rigs = Select(title='Training rig:', value='All', options=['All'] + all_rigs,
                  width=150)

    levels = Select(title='Level', value='All', options=['All'], width=150)

    busy = BusyIndicator()

    current_filter = dict()

    source = ColumnDataSource(get_data_df(current_filter))
    # Select the first available subject; the table may be empty under a filter.
    current_subject_fullname = None
    if len(source.data['subject_fullname']):
        source.selected.indices = [0]
        current_subject_fullname = source.data['subject_fullname'][0]

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
        .add_figure_creator(motor_coordinates.plot) \
        .add_figure_creator(subject_psych_curve.plot, dict(level='All')) \
        .build()

    # Figures are addressed positionally in updatable_list; name the indices so
    # inserting a plot above cannot silently re-point the level filter.
    water_index, performance_index, coordinates_index, psych_index = 0, 1, 2, 3

    # The photo grid is a gridplot rather than a single figure, so it is kept
    # outside the collection and updated alongside it.
    photos_grid, photos_subplots = subject_photos.plot()
    photos_figure = UpdatableFigure(photos_grid, photos_subplots)

    def update_level_filter(subj):

        nonlocal levels
        nonlocal figure_collection
        tasks = (dj.U('task') & (acquisition.Session & dict(subject_fullname=subj))).fetch('task')
        if not len(tasks):
            levels.options = ['All']
            levels.value = 'All'
            return
        task = tasks[0]
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

        figure_collection.updatable_list[psych_index][1] = dict(level=levels.value)
        levels.value = levels_value

    def callback_filter(attr, old, new, field):
        busy.run_busy(lambda: callback_filter_impl(new, field),
                      'Filtering subjects…')

    def callback_filter_impl(new, field):

        if field in current_filter.keys():
            current_filter.pop(field)

        if new != 'All':
            current_filter[field] = new

        source.data = get_data_df(current_filter)
        subjs = source.data['subject_fullname']
        # Keep the current subject selected if it survived the filter, otherwise
        # fall back to the first row so the figures always track the table.
        if len(subjs):
            if current_subject_fullname in list(subjs):
                index = list(subjs).index(current_subject_fullname)
            else:
                index = 0
            source.selected.indices = [index]
            # Already inside a busy block; go straight to the work.
            update_selected_subject()
        else:
            source.selected.indices = []

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
        busy.run_busy(lambda: callback_level_filter_impl(new),
                      'Loading psychometric curve…')

    def callback_level_filter_impl(new):

        figure_collection.updatable_list[psych_index][1] = dict(level=new)
        if current_subject_fullname is None:
            return
        figure_collection.updatable_list[psych_index][0].update(
            dict(subject_fullname=current_subject_fullname), dict(level=new))

    def update_selected_subject():
        nonlocal current_subject_fullname
        try:
            selected_index = source.selected.indices[0]
            current_subject_fullname = str(source.data['subject_fullname'][selected_index])
            update_level_filter(current_subject_fullname)
            figure_collection.update(dict(subject_fullname=current_subject_fullname))
            photos_figure.update(dict(subject_fullname=current_subject_fullname))
        except IndexError:
            pass

    def callback_update_data(attr, old, new):
        busy.run_busy(update_selected_subject, 'Loading subject data…')

    # callback functions
    if current_subject_fullname is not None:
        update_level_filter(current_subject_fullname)
        figure_collection.update(dict(subject_fullname=current_subject_fullname))
        photos_figure.update(dict(subject_fullname=current_subject_fullname))

    source.selected.on_change('indices', callback_update_data)

    subjects.on_change('value', partial(callback_filter, field='subject_fullname'))

    owners.on_change('value', partial(callback_filter, field='user_id'))

    sexes.on_change('value', partial(callback_filter, field='sex'))

    rigs.on_change('value', partial(callback_filter, field='location'))

    levels.on_change('value', callback_level_filter)

    data_table = DataTable(
        source=source,
        columns=columns,
        width=800,
        # Kept short enough that the photo panels below stay on screen without
        # scrolling; the table scrolls internally.
        height=360)

    return Panel(child=layout(row(column(row(owners, subjects),
                                         row(sexes, rigs),
                                         busy.div,
                                         data_table,
                                         # Photos go under the table, in space
                                         # the left column already has. Putting
                                         # them beside a plot pushed the page
                                         # past the width of a typical window.
                                         Div(text='<b>Latest position captures</b>'),
                                         photos_figure.fig),
                                  column(figure_collection.updatable_list[water_index][0].fig,
                                         figure_collection.updatable_list[performance_index][0].fig,
                                         figure_collection.updatable_list[coordinates_index][0].fig,
                                         levels,
                                         figure_collection.updatable_list[psych_index][0].fig))),
                 title='Subject')
