from viewer.utils import *
from viewer.modules import subject, behavior, puffs, acquisition
from viewer.plots.psych_curve import psych_curve
import datetime
import pdb

default_data = {'x': [np.nan], 'y': [np.nan]}


def plot(key=None):

    def create_query(key):
        if (acquisition.Session & key).fetch1('task') == 'AirPuffs':
            return puffs.PuffsSessionPsych & key
        else:
            return behavior.TowersSessionPsych & key

    def get_psych_data(key):

        data = default_data
        q = create_query(key)
        if len(q):
            psych = q.fetch1()
            data = {'x': np.squeeze(psych['session_delta_data']).tolist(),
                    'y': np.squeeze(psych['session_pright_data']).tolist()}

        return data

    def get_psych_error(key):

        data = default_data
        q = create_query(key)
        if len(q):
            psych = q.fetch1()
            data = {'x': np.squeeze(psych['session_delta_error']).tolist(),
                    'y': np.squeeze(psych['session_pright_error']).tolist()}

        return data

    def get_psych_fit(key):

        data = default_data
        q = create_query(key)
        if len(q):
            psych = q.fetch1()
            data = {'x': np.squeeze(psych['session_delta_fit']).tolist(),
                    'y': np.squeeze(psych['session_pright_fit']).tolist()}
        return data

    if key is None:
        key = dict(subject_fullname='emanuele_B208',
                   session_date=datetime.date(2018, 7, 17))

    psych_data = get_psych_data(key)
    psych_error = get_psych_error(key)
    psych_fit = get_psych_fit(key)

    p, plots = psych_curve(psych_data, psych_error, psych_fit,
                           'Session psychometric curve')

    return p, [(plots[0], get_psych_data, None),
               (plots[1], get_psych_error, None),
               (plots[2], get_psych_fit, None)]


if __name__ == '__main__':

    p, subplots = plot()
    show(p)
