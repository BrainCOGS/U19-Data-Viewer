'''
This module contains classes that allow convient updates upon selection events
'''


class UpdatableFigure:

    def __init__(self, fig, subplots):

        self.fig = fig
        self.subplots = subplots

    def update(self, key, plot_filter=None):

        # Several subplots of a figure usually share one get_data (a line and
        # its markers, say), and each call is a round trip to the database.
        # Memoize per update so a shared getter is fetched once, not once per
        # glyph. Scoped to this call: the next update re-queries as before.
        fetched = {}

        def fetch(get_data):
            if get_data not in fetched:
                if plot_filter:
                    fetched[get_data] = get_data(key, plot_filter)
                else:
                    fetched[get_data] = get_data(key)
            return fetched[get_data]

        for (subplot, get_data, update_view) in self.subplots:
            new_data = fetch(get_data)

            if type(subplot) == list:
                for sp in subplot:
                    sp.data_source.data = new_data
                    if update_view:
                        update_view(self.fig, sp, new_data)
            else:
                try:
                    subplot.data_source.data = new_data
                except AttributeError:
                    subplot.text = new_data
                if update_view:
                    update_view(self.fig, subplot, new_data)


class UpdatableFigureCollection:

    def __init__(self, figure_list):

        self.updatable_list = figure_list

    def update(self, key):

        for (fig, plot_filter) in self.updatable_list:
            if plot_filter:
                fig.update(key, plot_filter)
            else:
                fig.update(key)


class UpdatableFigureCollectionFactory:

    def __init__(self):

        self.figure_creator_list = []

    def add_figure_creator(self, creator, plot_filter=None):

        self.figure_creator_list.append([creator, plot_filter])
        return self

    def build(self):

        updatable_figure_list = []
        for (creator, plot_filter) in self.figure_creator_list:
            if plot_filter:
                p, subplots = creator(None, plot_filter)
            else:
                p, subplots = creator()
                plot_filter = None
            updatable_figure_list.append(
                [UpdatableFigure(p, subplots), plot_filter])

        return UpdatableFigureCollection(updatable_figure_list)
