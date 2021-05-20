from viewer.utils import *
from viewer.modules import subject, behavior, puffs, acquisition
from viewer.plots.psych_curve import psych_curve
import datetime
import pdb

default_data = {'x': [np.nan], 'y': [np.nan]}


def plot(key=None, blocks_type=None):

    def create_query(key, blocks_type=None):
        print(key)
        if (dj.U('task') & (acquisition.Session & key)).fetch1('task') == 'AirPuffs':
            return puffs.PuffsSessionPsych & key
        elif blocks_type:
            return behavior.TowersSessionPsychTask & key & {'blocks_type': blocks_type}
        else:
            return behavior.TowersSessionPsych & key

    def get_psych_data(key, blocks_type=None):

        data = default_data
        q = create_query(key, blocks_type)
        if len(q):
            psych = q.fetch1()
            delta_data = psych['blocks_delta_data'] if blocks_type else psych['session_delta_data']
            pright_data = psych['blocks_pright_data'] if blocks_type else psych['session_pright_data']

            if delta_data is None or type(delta_data) is float:
                return data
            data = {'x': np.squeeze(delta_data).tolist(),
                    'y': np.squeeze(pright_data).tolist()}
            if type(data['x']) is float:
                data['x'] = [data['x']]

            if type(data['y']) is float:
                data['y'] = [data['y']]

        return data

    def get_psych_error(key, blocks_type=None):

        data = default_data
        q = create_query(key, blocks_type)
        if len(q):
            psych = q.fetch1()
            delta_error = psych['blocks_delta_error'] if blocks_type else psych['session_delta_error']
            pright_error = psych['blocks_pright_error'] if blocks_type else psych['session_pright_error']

            if delta_error is None or type(delta_error) is float:
                return data
            data = {'x': np.squeeze(delta_error).tolist(),
                    'y': np.squeeze(pright_error).tolist()}

        return data

    def get_psych_fit(key, blocks_type=None):

        data = default_data
        q = create_query(key, blocks_type)
        if len(q):
            psych = q.fetch1()
            delta_fit = psych['blocks_delta_fit'] if blocks_type else psych['session_delta_fit']
            pright_fit = psych['blocks_pright_fit'] if blocks_type else psych['session_pright_fit']
            if delta_fit is None or type(delta_fit) is float:
                return data
            data = {'x': np.squeeze(delta_fit).tolist(),
                    'y': np.squeeze(pright_fit).tolist()}
        return data

    if key is None:
        key = dict(subject_fullname='emanuele_B208',
                   session_date=datetime.date(2018, 7, 17))

    psych_data = get_psych_data(key, blocks_type)
    psych_error = get_psych_error(key, blocks_type)
    psych_fit = get_psych_fit(key, blocks_type)

    if not blocks_type:
        blocks_type = 'all'
    p, plots = psych_curve(psych_data, psych_error, psych_fit,
                           'Session psychometric curve - ' + blocks_type)

    return p, [(plots[0], get_psych_data, None),
               (plots[1], get_psych_error, None),
               (plots[2], get_psych_fit, None)]


if __name__ == '__main__':

    p, subplots = plot()
    show(p)
