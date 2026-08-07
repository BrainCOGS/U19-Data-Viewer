from viewer.utils import *
from viewer.modules import subject
from viewer.plots import (water_weight, performance_level, motor_coordinates,
                          subject_photos)
from viewer.updatable_figures import *


def _subject_panel(all_subjects, default_subject, label):
    '''
    One side of the comparison: a subject selector driving its own set of
    figures. Returns the layout column and the selector, so the caller can
    arrange two of these side by side without them sharing any state.
    '''

    subjects = Select(title='{} subject:'.format(label), value=default_subject,
                      options=all_subjects, width=260)

    figure_collection = UpdatableFigureCollectionFactory() \
        .add_figure_creator(performance_level.plot) \
        .add_figure_creator(motor_coordinates.plot) \
        .add_figure_creator(water_weight.plot) \
        .build()

    photos_grid, photos_subplots = subject_photos.plot()
    photos_figure = UpdatableFigure(photos_grid, photos_subplots)

    def refresh(subject_fullname):
        key = dict(subject_fullname=subject_fullname)
        figure_collection.update(key)
        photos_figure.update(key)

    def callback_subject(attr, old, new):
        refresh(new)

    subjects.on_change('value', callback_subject)

    if default_subject:
        refresh(default_subject)

    panel = column(subjects,
                   *[fig.fig for (fig, _) in figure_collection.updatable_list],
                   photos_grid)

    return panel, subjects


def compare_tab():
    '''
    Creates the tab for comparing two subjects side by side.
    '''

    all_subjects = subject.Subject.fetch('subject_fullname').tolist()

    if not all_subjects:
        return Panel(child=layout([Div(text='No subjects available.')]),
                     title='Compare')

    left_default = all_subjects[0]
    right_default = all_subjects[1] if len(all_subjects) > 1 else all_subjects[0]

    left_panel, _ = _subject_panel(all_subjects, left_default, 'Left')
    right_panel, _ = _subject_panel(all_subjects, right_default, 'Right')

    return Panel(child=layout(row(left_panel, right_panel)), title='Compare')
