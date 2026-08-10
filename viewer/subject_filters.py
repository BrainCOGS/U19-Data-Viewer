'''
Shared subject filtering: which subjects are still alive, and which rigs a
subject has actually trained on.

Both the subject tab and the compare tab need the same notions, and the "alive"
predicate in particular is easy to get subtly wrong, so it lives in one place.
'''

from viewer.modules import subject, action, acquisition
from viewer.utils import *


# Housing locations that mean the subject is gone. Distinct from a Dead status:
# measured against the live database, 436 subjects have a Dead status without
# being in valhalla and 69 are in valhalla without one, so both are checked.
GRAVE_LOCATIONS = ['valhalla']

# Accounts whose subjects are test fixtures rather than real animals. They are
# 205 of the 466 living subjects, so leaving them in means nearly half the
# default view is noise.
TEST_USERS = ['testuser']


def dead_subject_names():
    '''
    Names of subjects that are dead, by either signal.

    SubjectStatus is keyed by effective_date, so status is a history: only the
    most recent row counts. A subject with no status row at all is treated as
    alive rather than unknown, otherwise the 213 subjects that have never had
    one would disappear from the viewer.

    Returns names rather than a query expression: the two signals have to be
    unioned, and datajoint cannot restrict by a Union.
    '''
    latest = dj.U('subject_fullname').aggr(
        action.SubjectStatus, effective_date='max(effective_date)')
    by_status = (action.SubjectStatus & latest &
                 'subject_status="Dead"').fetch('subject_fullname')

    grave = ' OR '.join('location="{}"'.format(location)
                        for location in GRAVE_LOCATIONS)
    by_location = (subject.Subject & grave).fetch('subject_fullname')

    return set(by_status) | set(by_location)


def real_subjects():
    '''subject.Subject without the test accounts' fixtures.'''
    if not TEST_USERS:
        return subject.Subject
    excluded = ' OR '.join('user_id="{}"'.format(user) for user in TEST_USERS)
    return subject.Subject & 'NOT ({})'.format(excluded)


def living_subjects():
    '''
    Subjects that are neither dead, in a grave, nor owned by a test account.
    This is what the viewer shows by default.
    '''
    dead = dead_subject_names()
    if not dead:
        return real_subjects()
    return real_subjects() - [dict(subject_fullname=name) for name in dead]


def subject_source(include_dead=False):
    '''
    The subject table to filter against. Test fixtures are always excluded;
    include_dead only relaxes the dead/grave test.
    '''
    return real_subjects() if include_dead else living_subjects()


def rigs_of(subject_fullname):
    '''
    Every rig a subject has trained on, most-used first.

    Training rig comes from acquisition.Session.session_location, not
    Subject.location: the latter is only ever 'vivarium' or 'valhalla' (where
    the animal is housed), while sessions record the rig they ran on. Usually
    one rig, but a subject can move, so this returns a list.
    '''
    sessions = acquisition.Session & dict(subject_fullname=subject_fullname)
    counts = dj.U('session_location').aggr(sessions, n='count(*)')
    return [row['session_location']
            for row in counts.fetch(order_by='n DESC', as_dict=True)
            if row['session_location']]


def all_rigs():
    '''Every rig that has hosted a session, for populating a filter.'''
    counts = dj.U('session_location').aggr(acquisition.Session, n='count(*)')
    return [row['session_location']
            for row in counts.fetch(order_by='n DESC', as_dict=True)
            if row['session_location']]


def subjects_on_rig(rig):
    '''Subjects with at least one session on the given rig.'''
    return dj.U('subject_fullname') & (
        acquisition.Session & dict(session_location=rig))
