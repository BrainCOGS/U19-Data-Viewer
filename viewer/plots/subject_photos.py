from viewer.modules import action
from viewer.utils import *

from bokeh.models import LinearColorMapper

# Images stored on action.DailySubjectPositionData, in display order.
IMAGE_COLUMNS = [('top_image', 'Top'), ('lateral_image', 'Lateral')]

# Number of most recent captures to show.
N_CAPTURES = 2


def _placeholder_image(width=160, height=120):
    '''
    A light checkerboard standing in for a missing capture, so a panel always
    renders something recognisable rather than an empty frame.
    '''
    tile = 16
    rows, cols = np.indices((height, width))
    pattern = ((rows // tile + cols // tile) % 2).astype(np.uint8)
    # Two near-white greys: visible as "no photo here", never mistaken for one.
    return np.ascontiguousarray(np.where(pattern, 235, 215).astype(np.uint8))


def _no_image():
    '''Empty columns, for the glyph that is not showing this image.'''
    return {'image': [], 'x': [], 'y': [], 'dw': [], 'dh': [],
            'real': [], 'color': []}


def _empty_image():
    image = _placeholder_image()
    height, width = image.shape
    # 'real' distinguishes a stand-in from an actual capture; it rides along in
    # the data source so update_view can label the panel correctly.
    return {'image': [image], 'x': [0], 'y': [0],
            'dw': [width], 'dh': [height], 'real': [False], 'color': [False]}


def _to_rgba(image):
    '''
    Pack an (h, w, 3 or 4) array into the uint32 view bokeh's image_rgba wants.
    '''
    height, width = image.shape[:2]
    rgba = np.empty((height, width, 4), dtype=np.uint8)
    rgba[:, :, :3] = image[:, :, :3]
    if image.shape[2] == 4:
        rgba[:, :, 3] = image[:, :, 3]
    else:
        rgba[:, :, 3] = 255
    return rgba.view(np.uint32).reshape(height, width)


def _as_image_data(raw):
    '''
    Normalize a stored image blob into an array bokeh can render, returning
    (array, is_color). Color images are packed as RGBA rather than averaged to
    grey, so nothing is thrown away. Anything unusable yields (None, False).
    '''
    if raw is None:
        return None, False

    image = np.asarray(raw)
    is_color = image.ndim == 3 and image.shape[2] in (3, 4)

    if not is_color and image.ndim != 2:
        return None, False
    if not image.size:
        return None, False

    # Bokeh draws images bottom-up, so flip vertically to put them the right way
    # up; flip horizontally as well to match the orientation of the rig cameras.
    image = image[::-1, ::-1]

    if is_color:
        # view() needs a contiguous buffer, so materialize the flip first.
        return _to_rgba(np.ascontiguousarray(image, dtype=np.uint8)), True

    # np.flip returns a reversed *view*, and bokeh serializes the underlying
    # buffer, so a non-contiguous array reaches the browser as garbage. Force a
    # C-contiguous copy. uint8 keeps it a quarter of the bytes of float64.
    return np.ascontiguousarray(image, dtype=np.uint8), False


def plot(key=None, plot_filter=None, panel_width=390, panel_height=280):
    '''
    Show the most recent captures for a subject as a grid of images: one row
    per capture, one column per camera angle.
    '''

    # One fetch per column serves every position, so the panels for capture 1
    # and capture 2 share a single query instead of repeating it. Only the
    # current subject is held, so switching subjects always re-reads.
    captures_cache = {}

    def fetch_captures(key, column):
        subject_key = str(sorted(key.items()))
        if captures_cache.get('_subject') != subject_key:
            captures_cache.clear()
            captures_cache['_subject'] = subject_key

        cache_key = column
        if cache_key not in captures_cache:
            # Images live in an external blob store (blob@dailyposition) that
            # is only reachable where its volume is mounted, so treat the whole
            # fetch as best-effort rather than letting the tab fail to build.
            try:
                captures_cache[cache_key] = (
                    action.DailySubjectPositionData & key).fetch(
                    'capture_time', column, order_by='capture_time DESC',
                    limit=N_CAPTURES, as_dict=True)
            except Exception as error:
                print('Could not read {} from the external store: {}'.format(
                    column, error), flush=True)
                captures_cache[cache_key] = []
        return captures_cache[cache_key]

    def make_get_data(position, column):

        def get_data(key, plot_filter=None):

            captures = fetch_captures(key, column)

            if position >= len(captures):
                return _empty_image()

            image, is_color = _as_image_data(captures[position][column])
            if image is None:
                return _empty_image()

            height, width = image.shape
            return {'image': [image], 'x': [0], 'y': [0],
                    'dw': [width], 'dh': [height], 'real': [True],
                    'color': [is_color]}

        return get_data

    def make_update_view(image_figure, placeholder, grey_glyph, rgba_glyph):
        # UpdatableFigure hands update_view the collection's top-level figure,
        # which here is the enclosing grid, so close over the real target.

        def update_view(_grid, subplot, data):
            placeholder.visible = not any(data.get('real') or [False])
            if not len(data['dw']):
                return

            # A renderer cannot change glyph type once built, so both are
            # present and only the one matching this image is shown. The other
            # is emptied: a uint32 RGBA buffer drawn by the palette glyph (or
            # vice versa) would render as noise.
            is_color = bool((data.get('color') or [False])[0])
            shown, hidden = ((rgba_glyph, grey_glyph) if is_color
                             else (grey_glyph, rgba_glyph))
            shown.visible = True
            hidden.visible = False
            hidden.data_source.data = _no_image()
            shown.data_source.data = data

            # Keep the frame matched to the image so it is not letterboxed.
            image_figure.x_range.start, image_figure.x_range.end = 0, data['dw'][0]
            image_figure.y_range.start, image_figure.y_range.end = 0, data['dh'][0]

        return update_view

    if key is None:
        key = dict(subject_fullname='emanuele_B208')

    figures = []
    subplots = []

    for position in range(N_CAPTURES):
        # Not named `column`: that would shadow bokeh's column() layout helper
        # used below to assemble the grid.
        for image_column, angle in IMAGE_COLUMNS:
            get_data = make_get_data(position, image_column)
            data = get_data(key)

            p = figure(width=panel_width, height=panel_height,
                       title='{} — capture {}'.format(angle, position + 1),
                       x_axis_location=None, y_axis_location=None,
                       toolbar_location=None)
            p.grid.grid_line_color = None
            p.outline_line_color = '#cccccc'

            # Shown only while the image source is empty, so an unreachable
            # store or a subject without captures reads as intentional.
            placeholder = Label(x=panel_width // 2 - 25,
                                y=panel_height // 2 - 20,
                                x_units='screen', y_units='screen',
                                text='No image',
                                text_color='#999999', text_font_size='12px')
            p.add_layout(placeholder)

            p.x_range = Range1d(0, data['dw'][0])
            p.y_range = Range1d(0, data['dh'][0])

            placeholder.visible = not any(data.get('real') or [False])

            is_color = bool((data.get('color') or [False])[0])

            # Both glyphs exist up front and update_view shows whichever suits
            # the current image; a renderer's glyph type is fixed once built.
            #
            # Pin the mapper to the full 8-bit range. Left to infer its own
            # bounds it rescales per image, which changes apparent brightness
            # between captures and washes out low-contrast frames.
            grey_glyph = p.image(
                image='image', x='x', y='y', dw='dw', dh='dh',
                color_mapper=LinearColorMapper(palette='Greys256',
                                               low=0, high=255),
                source=_no_image() if is_color else data)
            rgba_glyph = p.image_rgba(
                image='image', x='x', y='y', dw='dw', dh='dh',
                source=data if is_color else _no_image())

            grey_glyph.visible = not is_color
            rgba_glyph.visible = is_color

            # Register the glyph that UpdatableFigure writes to; update_view
            # then routes the data to whichever glyph should display it.
            subplots.append((grey_glyph if not is_color else rgba_glyph,
                             get_data,
                             make_update_view(p, placeholder,
                                              grey_glyph, rgba_glyph)))
            figures.append(p)

    # Plain nested row/column rather than gridplot: a gridplot nested inside
    # another row did not lay out at all here, leaving blank space where the
    # panels should be. Rows of two keep one line per capture.
    ncols = len(IMAGE_COLUMNS)
    grid = column(*[row(*figures[i:i + ncols])
                    for i in range(0, len(figures), ncols)])

    return grid, subplots


if __name__ == '__main__':

    p, subplots = plot()
    show(p)
