from viewer.utils import *
from viewer.modules import subject, behavior, acquisition, puffs
from viewer.plots.psych_curve import psych_curve
import pdb

default_data = {'x': [np.nan], 'y': [np.nan]}


def plot(key=None, plot_filter=None):

    def create_query(key, plot_filter):
        if not plot_filter or plot_filter['level'] == 'All':
            if acquisition.Session & key & 'task="AirPuffs"':
                cpsych = puffs.PuffsSubjectCumulativePsych
            else:
                cpsych = behavior.TowersSubjectCumulativePsych
        else:
            if acquisition.Session & key & 'task="AirPuffs"':
                cpsych = puffs.PuffsSubjectCumulativePsychLevel & \
                    dict(psych_level=int(plot_filter['level']))
            else:
                cpsych = behavior.TowersSubjectCumulativePsychLevel & \
                    dict(psych_level=int(plot_filter['level']))

        return cpsych & (acquisition.Session &
                         (dj.U('subject_fullname', 'session_start_time') & (subject.Subject & key).aggr(
            acquisition.Session & cpsych,
            session_start_time='max(session_start_time)')))

    def get_psych_data(key, plot_filter):

        data = default_data
        q = create_query(key, plot_filter)
        if len(q):
            psych = q.fetch1()
            data = {'x': np.squeeze(psych['subject_delta_data']).tolist(),
                    'y': np.squeeze(psych['subject_pright_data']).tolist()}

        return data

    def get_psych_error(key, plot_filter):

        data = default_data
        q = create_query(key, plot_filter)
        if len(q):
            psych = q.fetch1()
            data = {'x': np.squeeze(psych['subject_delta_error']).tolist(),
                    'y': np.squeeze(psych['subject_pright_error']).tolist()}

        return data

    def get_psych_fit(key, plot_filter):

        data = default_data
        q = create_query(key, plot_filter)
        if len(q):
            psych = q.fetch1()
            data = {'x': np.squeeze(psych['subject_delta_fit']).tolist(),
                    'y': np.squeeze(psych['subject_pright_fit']).tolist()}
        return data

    def get_label(key, plot_filter):
        if not plot_filter:
            level = 'All'
        else:
            level = plot_filter['level']
        return f'Subject {key["subject_fullname"]} \nLevel {level}'

    if key is None:
        key = dict(subject_fullname='emanuele_B208')

    psych_data = get_psych_data(key, plot_filter)
    psych_error = get_psych_error(key, plot_filter)
    psych_fit = get_psych_fit(key, plot_filter)
    psych_label = get_label(key, plot_filter)

    p, plots = psych_curve(psych_data, psych_error, psych_fit,
                           'Subject cumulative psychometric curve so far',
                           psych_label)

    return p, [(plots[0], get_psych_data, None),
               (plots[1], get_psych_error, None),
               (plots[2], get_psych_fit, None),
               (plots[3], get_label, None)]


if __name__ == '__main__':

    p, subplots = plot()
    show(p)
