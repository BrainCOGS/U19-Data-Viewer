from utils import *

def session_tab():
    '''
    Creates the tab to view all sessions
    '''

    subject = dj.create_virtual_module('subject', 'u19_subject')
    acquisition = dj.create_virtual_module('acquisition', 'u19_acquisition')


    all_subjects = (subject.Subject & acquisition.Session).fetch('subject_fullname').tolist()
    subjects = Select(title='Subject:',value = 'All', options = ['All'] + all_subjects,
                      width = 150)

    all_tasks = (dj.U('task') & acquisition.Session).fetch('task').tolist()
    tasks = Select(title='Task:',value = 'All', options = ['All'] + all_tasks,
                   width = 150)


    def get_data_df(filter):

        return pd.DataFrame((
            acquisition.Session & filter).fetch(
                'subject_fullname', 'session_date', 'session_number', 'session_location',
                'task', 'level', 'session_protocol', 'session_performance',
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
    ]


    def callback_subject_filter(attr, old, new):

        if 'subject_fullname' in current_filter.keys():
            current_filter.pop('subject_fullname')

        if new != 'All':
            current_filter['subject_fullname'] = new

        source.data = get_data_df(current_filter)


    def callback_task_filter(attr, old, new):

        if 'task' in current_filter.keys():
            current_filter.pop('task')

        if new != 'All':
            current_filter['task'] = new

        source.data = get_data_df(current_filter)

    subjects.on_change('value', callback_subject_filter)
    tasks.on_change('value', callback_task_filter)

    data_table = DataTable(source=source,
                           columns=columns,
                           width=800,
                           height=600)

    return Panel(child=layout(column(row(subjects, tasks), data_table)), title='Session')
