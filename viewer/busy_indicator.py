'''
A small "working…" banner shared by the tabs.

Bokeh only pushes model changes to the browser between callbacks, so a handler
that flips an indicator on and then runs its queries never shows anything: the
browser sees both changes at once when the handler returns. `run_busy` splits
that in two, showing the banner in one callback and doing the work on the next
tick, so the user gets immediate feedback that their click registered.
'''

from bokeh.models import Div


BUSY_STYLE = ('padding:4px 10px;border-radius:3px;'
              'font-size:12px;font-weight:bold;')


class BusyIndicator:

    def __init__(self, width=260):
        self.div = Div(text='', width=width,
                       styles={'padding': '4px 0', 'font-size': '12px'})
        self._depth = 0

    def _render(self, message=None):
        if message:
            self.div.text = (
                '<span style="{}background:#fff3cd;color:#856404;">'
                '⏳ {}</span>'.format(BUSY_STYLE, message))
        else:
            self.div.text = ''

    def show(self, message='Loading…'):
        self._depth += 1
        self._render(message)

    def hide(self):
        self._depth = max(0, self._depth - 1)
        if not self._depth:
            self._render(None)

    def run_busy(self, work, message='Loading data…'):
        '''
        Show the banner, then run `work` on the next tick so the browser has a
        chance to paint it first. Falls back to running inline when the widget
        is not attached to a server document (scripts, tests).
        '''
        self.show(message)

        def finish():
            try:
                work()
            finally:
                self.hide()

        # Use the document this widget actually belongs to; curdoc() is the
        # module-global one and is not reliably the session's document.
        doc = self.div.document
        if doc is None:
            finish()
            return

        doc.add_next_tick_callback(finish)
