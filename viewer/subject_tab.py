from viewer.utils import *
from viewer.modules import *
from viewer.plots import (water_weight, performance_level, subject_psych_curve,
                          motor_coordinates, subject_photos)
from viewer.updatable_figures import *
from viewer.busy_indicator import BusyIndicator
from viewer import subject_filters


def subject_tab():

    table_columns = ['subject_fullname', 'user_id', 'sex', 'dob', 'location',
                     'line']

    # Training rig is not a column on subject.Subject, so it restricts through
    # sessions rather than sitting in the plain field filter.
    current_rig = dict(value='All')
    show_dead = dict(value=False)

    def subject_query(filter):
        query = subject_filters.subject_source(show_dead['value']) & filter
        if current_rig['value'] != 'All':
            query = query & subject_filters.subjects_on_rig(current_rig['value'])
        return query

    # 'rig' is derived from sessions rather than fetched, so it is listed
    # separately from the columns that come off subject.Subject.
    display_columns = table_columns + ['rig']

    def get_data_df(filter):

        query = subject_query(filter)
        df = pd.DataFrame(query.fetch(*table_columns, as_dict=True))
        if not len(df):
            # A filter combination can match nothing; keep the columns so the
            # table and its callbacks still have something well-formed to read.
            return pd.DataFrame({column: [] for column in display_columns})
        df['dob'] = pd.to_datetime(df['dob'], errors='coerce').dt.strftime('%Y-%m-%d')
        df['dob'] = df['dob'].replace('NaT', 'Unknown')

        # One grouped query for every visible subject, not one per row. Most
        # subjects train on a single rig; the rest are listed most-used first.
        rigs = subject_filters.rigs_by_subject(query.proj())
        df['rig'] = [', '.join(rigs.get(name, [])) or 'None'
                     for name in df['subject_fullname']]
        return df

    all_subjects = subject_query({}).fetch('subject_fullname').tolist()
    subjects = Select(title='Subject:', value='All', options=['All'] + all_subjects,
                      width=150)

    all_owners = (dj.U('user_id') & subject_filters.living_subjects()).fetch(
        'user_id').tolist()
    owners = Select(title='Owner:', value='All', options=['All'] + all_owners,
                    width=150)

    all_sexes = [s for s in ('Male', 'Female', 'Unknown')
                 if subject.Subject & dict(sex=s)]
    sexes = Select(title='Sex:', value='All', options=['All'] + all_sexes,
                   width=150)

    rigs = Select(title='Training rig:', value='All',
                  options=['All'] + subject_filters.all_rigs(), width=150)

    # Most subjects in the database are dead, so they are hidden by default.
    include_dead = CheckboxGroup(labels=['Include dead subjects'], active=[],
                                 width=200)

    download = Button(label='Download table (CSV)', button_type='primary',
                      width=200)

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
        TableColumn(field="rig", title="Training rig"),
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

    def callback_rig(attr, old, new):
        def apply():
            current_rig['value'] = new
            refresh_table()
            # Keep the subject list in step with the rig.
            subjects.options = ['All'] + subject_query({}).fetch(
                'subject_fullname').tolist()
        busy.run_busy(apply, 'Filtering by rig…')

    def callback_include_dead(attr, old, new):
        def apply():
            show_dead['value'] = bool(new)
            refresh_table()
            subjects.options = ['All'] + subject_query({}).fetch(
                'subject_fullname').tolist()
        busy.run_busy(apply, 'Reloading subjects…')

    def refresh_table():
        '''Re-read the table under the current filters and keep a row selected.'''
        source.data = get_data_df(current_filter)
        subjs = source.data['subject_fullname']
        if len(subjs):
            if current_subject_fullname in list(subjs):
                index = list(subjs).index(current_subject_fullname)
            else:
                index = 0
            source.selected.indices = [index]
            update_selected_subject()
        else:
            source.selected.indices = []

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

        # The companion dropdowns follow the same alive/rig scope as the table.
        if field == 'subject_fullname':
            if new != 'All':
                owner = subject_query(
                    dict(subject_fullname=new)).fetch('user_id').tolist()
                owners.options = ['All'] + owner
            else:
                all_owners = (dj.U('user_id') & subject_query({})).fetch(
                    'user_id').tolist()
                owners.options = ['All'] + all_owners

        if field == 'user_id':
            if new != 'All':
                all_subjects = subject_query(
                    dict(user_id=new)).fetch('subject_fullname').tolist()
                subjects.options = ['All'] + all_subjects
            else:
                all_subjects = subject_query({}).fetch(
                    'subject_fullname').tolist()
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

    rigs.on_change('value', callback_rig)

    include_dead.on_change('active', callback_include_dead)

    levels.on_change('value', callback_level_filter)

    # The download has to happen in the browser: a bokeh server callback cannot
    # hand the client a file. The data is already in the ColumnDataSource, so
    # the CSV is built from that and saved through a temporary blob URL.
    download.js_on_click(CustomJS(
        args=dict(source=source,
                  fields=[c.field for c in columns],
                  headers=[c.title for c in columns]),
        code='''
        const data = source.data;
        const n = (data[fields[0]] || []).length;

        // Quote every field and double any embedded quotes: the rig column
        // holds a comma-separated list when a subject moved between rigs.
        const cell = (value) => {
            const text = (value === null || value === undefined) ? '' : String(value);
            return '"' + text.replace(/"/g, '""') + '"';
        };

        const lines = [headers.map(cell).join(',')];
        for (let i = 0; i < n; i++) {
            lines.push(fields.map((f) => cell((data[f] || [])[i])).join(','));
        }

        const stamp = new Date().toISOString().slice(0, 10);
        const blob = new Blob([lines.join('\\n')], {type: 'text/csv;charset=utf-8;'});
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = 'u19_subjects_' + stamp + '.csv';
        link.click();
        URL.revokeObjectURL(link.href);
        '''))

    data_table = DataTable(
        source=source,
        columns=columns,
        width=800,
        # Kept short enough that the photo panels below stay on screen without
        # scrolling; the table scrolls internally.
        height=360)

    # Order matches the compare tab: owner, rig, sex, subject, then the
    # include-dead checkbox.
    return Panel(child=layout(row(column(row(owners, rigs),
                                         row(sexes, subjects),
                                         row(include_dead, download),
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
