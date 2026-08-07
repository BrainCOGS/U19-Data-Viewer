from viewer.modules import action
from viewer.utils import *

from bokeh.layouts import gridplot

# Images stored on action.DailySubjectPositionData, in display order.
IMAGE_COLUMNS = [('top_image', 'Top'), ('lateral_image', 'Lateral')]

# Number of most recent captures to show.
N_CAPTURES = 2


def _empty_image():
    return {'image': [], 'x': [], 'y': [], 'dw': [], 'dh': []}


def _as_image_data(raw):
    '''
    Normalize a stored image blob into a 2-D array Bokeh can render.
    Color images are averaged to grayscale; anything unusable yields None.
    '''
    if raw is None:
        return None

    image = np.asarray(raw)
    if image.ndim == 3:
        image = image.mean(axis=2)
    if image.ndim != 2 or not image.size:
        return None

    # Bokeh draws images bottom-up; flip so they appear the right way round.
    return np.flipud(image.astype(float))


def plot(key=None, plot_filter=None):
    '''
    Show the most recent captures for a subject as a grid of images: one row
    per capture, one column per camera angle.
    '''

    def make_get_data(position, column):

        def get_data(key, plot_filter=None):

            captures = (action.DailySubjectPositionData & key).fetch(
                'capture_time', column, order_by='capture_time DESC',
                limit=N_CAPTURES, as_dict=True)

            if position >= len(captures):
                return _empty_image()

            image = _as_image_data(captures[position][column])
            if image is None:
                return _empty_image()

            height, width = image.shape
            return {'image': [image], 'x': [0], 'y': [0],
                    'dw': [width], 'dh': [height]}

        return get_data

    def make_update_view(image_figure):
        # UpdatableFigure hands update_view the collection's top-level figure,
        # which here is the enclosing grid, so close over the real target.

        def update_view(_grid, subplot, data):
            # Keep the frame matched to the image so it is not letterboxed.
            if not len(data['dw']):
                return
            image_figure.x_range.start, image_figure.x_range.end = 0, data['dw'][0]
            image_figure.y_range.start, image_figure.y_range.end = 0, data['dh'][0]

        return update_view

    if key is None:
        key = dict(subject_fullname='emanuele_B208')

    figures = []
    subplots = []

    for position in range(N_CAPTURES):
        for column, angle in IMAGE_COLUMNS:
            get_data = make_get_data(position, column)
            data = get_data(key)

            p = figure(width=260, height=200,
                       title='{} — capture {}'.format(angle, position + 1),
                       x_axis_location=None, y_axis_location=None,
                       toolbar_location=None)
            p.grid.grid_line_color = None
            p.outline_line_color = '#cccccc'

            if len(data['dw']):
                p.x_range = Range1d(0, data['dw'][0])
                p.y_range = Range1d(0, data['dh'][0])
            else:
                p.x_range = Range1d(0, 1)
                p.y_range = Range1d(0, 1)

            glyph = p.image(image='image', x='x', y='y', dw='dw', dh='dh',
                            palette='Greys256', source=data)

            subplots.append((glyph, get_data, make_update_view(p)))
            figures.append(p)

    grid = gridplot(figures, ncols=len(IMAGE_COLUMNS),
                    toolbar_location=None)

    return grid, subplots


if __name__ == '__main__':

    p, subplots = plot()
    show(p)
