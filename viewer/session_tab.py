from utils import *
from modules import subject, acquisition, behavior
from viewer.plots import session_psych_curve
from viewer.updatable_figures import *
import pdb


def session_tab():
    '''
    Creates the tab to view all sessions
    '''

    all_subjects = (subject.Subject & acquisition.Session).fetch('subject_fullname').tolist()
    subjects = Select(title='Subject:', value='All', options=['All'] + all_subjects,
                      width=150)

    all_levels = (dj.U('level') & acquisition.Session).fetch('level').tolist()
    all_levels_str = [str(level) for level in all_levels]
    levels = Select(title='Level:', value='All',
                    options=['All'] + all_levels_str,
                    width=150)

    all_tasks = (dj.U('task') & acquisition.Session).fetch('task').tolist()
    tasks = Select(title='Task:', value='All', options=['All'] + all_tasks,
                   width=150)

    def get_data_df(filter):

        return pd.DataFrame((
            acquisition.Session & filter).fetch(
                'subject_fullname', 'session_date', 'session_number', 'session_location',
                'task', 'level', 'session_protocol', 'session_performance', 'num_trials',
                'is_bad_session', 'session_comments',
                as_dict=True))

    current_filter = dict()
    sessions_df = get_data_df(current_filter)

    source = ColumnDataSource(sessions_df)
    # Table for displaying sessions
    columns = [
        TableColumn(field="subject_fullname", title="Subject"),
        TableColumn(field="session_date", title="Date", formatter=DateFormatter()),
        TableColumn(field="session_number", title="Session Number"),
        TableColumn(field="session_location", title="Location"),
        TableColumn(field="task", title="Task"),
        TableColumn(field="level", title="Level"),
        TableColumn(field="session_protocol", title="Protocol"),
        TableColumn(field="session_performance", title="Performance"),
        TableColumn(field="num_trials", title="Trial Counts"),
        TableColumn(field="is_bad_session", title="Is Bad"),
        TableColumn(field="session_comments", title="Comments"),
    ]

    def callback_subject_filter(attr, old, new):

        if 'subject_fullname' in current_filter.keys():
            current_filter.pop('subject_fullname')

        if new != 'All':
            current_filter['subject_fullname'] = new
            subject_levels = (
                dj.U('level') &
                (acquisition.Session & current_filter)).fetch('level').tolist()
            subject_levels_str = [str(level) for level in subject_levels]
            levels.options = ['All'] + subject_levels_str

            subject_tasks = (
                dj.U('task') &
                (acquisition.Session & current_filter)).fetch('task').tolist()

            tasks.options = ['All'] + subject_tasks

        source.data = get_data_df(current_filter)

    def callback_level_filter(attr, old, new):

        if 'level' in current_filter.keys():
            current_filter.pop('level')

        if new != 'All':
            current_filter['level'] = int(new)

            level_subjects = (
                dj.U('subject_fullname') & (acquisition.Session & current_filter)
            ).fetch('subject_fullname').tolist()

            subjects.options = ['All'] + level_subjects

            level_tasks = (
                dj.U('task') & (acquisition.Session & current_filter)
            ).fetch('task').tolist()

            tasks.options = ['All'] + level_tasks

        source.data = get_data_df(current_filter)

    def callback_task_filter(attr, old, new):

        if 'task' in current_filter.keys():
            current_filter.pop('task')

        if new != 'All':
            current_filter['task'] = new

        task_subjects = (
            dj.U('subject_fullname') & (acquisition.Session & current_filter)
        ).fetch('subject_fullname').tolist()

        subjects.options = ['All'] + task_subjects

        task_levels = (
            dj.U('level') &
            (acquisition.Session & current_filter)).fetch('level').tolist()
        task_levels_str = [str(level) for level in task_levels]
        levels.options = ['All'] + task_levels_str

        source.data = get_data_df(current_filter)

    def callback_update_data(attr, old, new):
        try:
            selected_index = source.selected.indices[0]
            subject_fullname = str(source.data['subject_fullname'][selected_index])
            session_date = source.data['session_date'][selected_index]
            figure_collection.update(dict(subject_fullname=subject_fullname,
                                          session_date=session_date))

        except IndexError:
            pass

    figure_collection = UpdatableFigureCollectionFactory() \
        .add_figure_creator(session_psych_curve.plot) \
        .build()

    source.selected.on_change('indices', callback_update_data)
    subjects.on_change('value', callback_subject_filter)
    levels.on_change('value', callback_level_filter)
    tasks.on_change('value', callback_task_filter)

    data_table = DataTable(source=source,
                           columns=columns,
                           width=1000,
                           height=600)

    return Panel(child=layout(row(column(row(subjects, levels, tasks), data_table),
                              column(figure_collection.updatable_list[0].fig))), title='Session')
