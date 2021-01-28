'''
This module contains classes that allow convient updates upon selection events
'''


class UpdatableFigure:

    def __init__(self, fig, subplots):

        self.fig = fig
        self.subplots = subplots

    def update(self, key, filter=None):

        for (subplot, get_data, update_view) in self.subplots:
            new_data = get_data(key)
            if type(subplot) == list:
                for sp in subplot:
                    sp.data_source.data = new_data
                    if update_view:
                        update_view(self.fig, sp, new_data)
            else:
                subplot.data_source.data = new_data
                if update_view:
                    update_view(self.fig, subplot, new_data)


class UpdatableFigureCollection:

    def __init__(self, figure_list):

        self.updatable_list = figure_list

    def update(self, key):

        for fig in self.updatable_list:
            fig.update(key)


class UpdatableFigureCollectionFactory:

    def __init__(self):

        self.figure_creator_list = []

    def add_figure_creator(self, creator):

        self.figure_creator_list.append(creator)
        return self

    def build(self):

        updatable_figure_list = []
        for creator in self.figure_creator_list:
            p, subplots = creator()
            updatable_figure_list.append(UpdatableFigure(p, subplots))

        return UpdatableFigureCollection(updatable_figure_list)
