from viewer.utils import *
from viewer.modules import subject
from viewer.plots import (water_weight, performance_level, motor_coordinates,
                          subject_photos)
from viewer.updatable_figures import *
from viewer.busy_indicator import BusyIndicator
from viewer import subject_filters


def _subject_panel(default_subject, label, owners, rigs):
    '''
    One side of the comparison: owner / rig / sex / status prefilters narrowing a
    subject selector, which drives its own set of figures. Returns the layout
    column and the selector, so the caller can arrange two of these side by side
    without them sharing any state.
    '''

    owner_select = Select(title='Owner:', value='All',
                          options=['All'] + owners, width=260)
    rig_select = Select(title='Training rig:', value='All',
                        options=['All'] + rigs, width=260)
    sex_select = Select(title='Sex:', value='All',
                        options=['All', 'Male', 'Female', 'Unknown'], width=260)
    # Most subjects in the database are dead, so they are hidden by default.
    dead_check = CheckboxGroup(labels=['Include dead subjects'], active=[],
                               width=260)

    subjects = Select(title='{} subject:'.format(label), value=default_subject,
                      options=[default_subject], width=260)

    busy = BusyIndicator(width=260)

    def available_subjects():
        '''Subjects matching this side's prefilters.'''
        field_filter = {}
        if owner_select.value != 'All':
            field_filter['user_id'] = owner_select.value
        if sex_select.value != 'All':
            field_filter['sex'] = sex_select.value

        query = subject_filters.subject_source(
            bool(dead_check.active)) & field_filter
        if rig_select.value != 'All':
            query = query & subject_filters.subjects_on_rig(rig_select.value)

        return query.fetch('subject_fullname').tolist()

    def callback_prefilter(attr, old, new):
        def apply():
            options = available_subjects()
            subjects.options = options or ['(no matching subjects)']
            # Keep the current subject if it survived, else move to the first.
            if subjects.value not in subjects.options:
                subjects.value = subjects.options[0]
                if options:
                    refresh(subjects.value)
        busy.run_busy(apply, 'Filtering subjects…')

    figure_collection = UpdatableFigureCollectionFactory() \
        .add_figure_creator(performance_level.plot) \
        .add_figure_creator(motor_coordinates.plot) \
        .add_figure_creator(water_weight.plot) \
        .build()

    # Narrower panels here: two of these columns sit side by side.
    photos_grid, photos_subplots = subject_photos.plot(
        panel_width=290, panel_height=210)
    photos_figure = UpdatableFigure(photos_grid, photos_subplots)

    def refresh(subject_fullname):
        key = dict(subject_fullname=subject_fullname)
        figure_collection.update(key)
        photos_figure.update(key)

    def callback_subject(attr, old, new):
        if new.startswith('('):     # the "no matching subjects" sentinel
            return
        busy.run_busy(lambda: refresh(new),
                      'Loading {}…'.format(new))

    subjects.on_change('value', callback_subject)
    for widget in (owner_select, rig_select, sex_select):
        widget.on_change('value', callback_prefilter)
    dead_check.on_change('active', callback_prefilter)

    subjects.options = available_subjects() or [default_subject]
    if default_subject in subjects.options:
        subjects.value = default_subject
    else:
        subjects.value = subjects.options[0]

    if subjects.value and not subjects.value.startswith('('):
        refresh(subjects.value)

    panel = column(Div(text='<b>{}</b>'.format(label)),
                   owner_select,
                   rig_select,
                   sex_select,
                   dead_check,
                   subjects,
                   busy.div,
                   *[fig.fig for (fig, _) in figure_collection.updatable_list],
                   photos_grid)

    return panel, subjects


def compare_tab():
    '''
    Creates the tab for comparing two subjects side by side.
    '''

    # Default to living subjects, matching the prefilter each side starts on.
    all_subjects = subject_filters.living_subjects().fetch(
        'subject_fullname').tolist()

    if not all_subjects:
        return Panel(child=layout([Div(text='No subjects available.')]),
                     title='Compare')

    owners = (dj.U('user_id') & subject_filters.living_subjects()).fetch(
        'user_id').tolist()
    rigs = subject_filters.all_rigs()

    left_default = all_subjects[0]
    right_default = all_subjects[1] if len(all_subjects) > 1 else all_subjects[0]

    left_panel, _ = _subject_panel(left_default, 'Left', owners, rigs)
    right_panel, _ = _subject_panel(right_default, 'Right', owners, rigs)

    return Panel(child=layout(row(left_panel, right_panel)), title='Compare')
