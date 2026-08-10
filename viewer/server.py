import pandas as pd
import os
from os.path import join as pjoin
from bokeh.server.server import Server
from bokeh.models import Tabs
from subject_tab import subject_tab
from session_tab import session_tab
from viewer.compare_tab import compare_tab

import datajoint as dj


def datajoint_dot():
    from bokeh.models import Div
    from bokeh.layouts import layout
    from bokeh.models import TabPanel as Panel

    subject = dj.create_virtual_module('subject', 'u19_subject')
    action = dj.create_virtual_module('action', 'u19_action')
    acquisition = dj.create_virtual_module('acquisition', 'u19_acquisition')

    try:
        svg = (dj.Diagram(subject) + dj.Diagram(action) + dj.Diagram(acquisition)).make_dot().create_svg()
        # Inline the markup rather than pointing an <object data=...> at it:
        # the SVG is already a document, and embedding it in an attribute made
        # the browser request its "<?xml" prolog as a URL (a 404 per load).
        svg = svg.decode('utf-8')
        div = Div(text=svg[svg.find('<svg'):] if '<svg' in svg else svg)
    except Exception as error:
        print('Could not get diagram, did you install graphviz and pydotplus??',
              error, flush=True)
        div = Div(text='installation not complete')
    return Panel(child=layout([div]),title='Overview')


def bkapp(doc):
    from bokeh.models import Div, TabPanel as Panel
    from bokeh.layouts import layout

    # Building every tab up front costs the sum of all their queries before the
    # page can paint. Only the initially active tab is built eagerly; the rest
    # show a placeholder and are constructed the first time they are opened.
    ACTIVE = 1
    builders = [('Overview', datajoint_dot),
                ('Subject', subject_tab),
                ('Session', session_tab),
                ('Compare', compare_tab)]

    def placeholder(title, message=None):
        text = message or 'Loading {}…'.format(title)
        return Panel(child=layout([Div(
            text='<p style="padding:12px;color:#856404;background:#fff3cd;'
                 'border-radius:3px;display:inline-block;">⏳ {}</p>'.format(text))]),
            title=title)

    tabs = Tabs(tabs=[placeholder(title) for title, _ in builders],
                active=ACTIVE)
    built = set()

    def build(index):
        # Marked before building, so a tab already under construction is never
        # started a second time; callbacks are serialized on the session's IO
        # loop, so the panel is always swapped in before anything else runs.
        if index in built:
            return
        built.add(index)
        title, builder = builders[index]
        try:
            panel = builder()
        except Exception as error:
            print('Could not build the {} tab: {}'.format(title, error),
                  flush=True)
            panel = Panel(child=layout(
                [Div(text='<p>Could not load {}: {}</p>'.format(title, error))]),
                title=title)
        # Replace in place so the active index keeps pointing at this tab.
        tabs.tabs[index] = panel

    def callback_active(attr, old, new):
        if new in built:
            return
        # Let the placeholder paint before the build blocks the loop, so the
        # click visibly registers instead of the tab appearing to hang.
        title = builders[new][0]
        tabs.tabs[new] = placeholder(title, 'Loading {} from the database…'
                                     .format(title))
        doc.add_next_tick_callback(lambda: build(new))

    tabs.on_change('active', callback_active)
    build(ACTIVE)

    # Optionally warm the remaining tabs after the first one paints, so they are
    # ready before they are clicked.
    #
    # Off by default, and deliberately so: every session runs its own chain, and
    # the builds share one IO loop with all other sessions. Measured across
    # three sequential page loads with prewarming on, each load waited behind
    # the previous session's warm-up (3.1s, 11.5s, 23.5s). On demand, each tab
    # costs its own build once and nobody queues behind anyone else. Enable it
    # only for a single-user deployment.
    PREWARM_ORDER = [3, 2, 0]  # Compare (~4s), Session (~7s), Overview (~14s)

    def prewarm(remaining):
        if not remaining:
            return
        index, rest = remaining[0], remaining[1:]
        build(index)
        if rest:
            doc.add_next_tick_callback(lambda: prewarm(rest))

    if os.environ.get('PREWARM_TABS', '').lower() in ('1', 'true', 'yes'):
        doc.add_next_tick_callback(
            lambda: prewarm([i for i in PREWARM_ORDER if i != ACTIVE]))

    doc.add_root(tabs)
    doc.title = 'Princeton U19 DataJoint Interface'


def main():
    import sys
    from argparse import ArgumentParser
    parser = ArgumentParser(
        description='Princeton U19 DataJoint Interface')
    parser.add_argument('-p', '--port',
                        type=int,
                        default=5000,
                        help='port for the bokeh server',
                        action='store')
    parser.add_argument('-n', '--num-proc',
                        type=int,
                        default=1,
                        help='number of processes for the bokeh server (zero is auto)',
                        action='store')
    parser.add_argument('-b', '--browser',
                        default=False,
                        action='store_true')


    ops = parser.parse_args()
    port = ops.port
    nproc = ops.num_proc
    browser = ops.browser
    import socket
    hostname = socket.gethostname()
    try:
        ipaddress = socket.gethostbyname(hostname)
    except socket.gaierror:
        ipaddress = '127.0.0.1'
    origins = ','.join(['localhost:{0}',
                        '0.0.0.0:{0}',
                        '{1}:{0},{2}:{0}',
                        '{1}.princeton.edu:{0}',
                        'braincogs01.pni.princeton.edu',
                        'braincogs01-test0.pni.princeton.edu',
                        'braincogs01-test1.pni.princeton.edu']).format(
        port, hostname, ipaddress)

    # When the server is published on a host port that differs from the one it
    # listens on (docker's "5001:5000", say), the browser's Origin carries the
    # host port and is not in the list above. EXTRA_WS_ORIGINS lets the
    # deployment name those, as a comma-separated list of host:port.
    extra_origins = os.environ.get('EXTRA_WS_ORIGINS', '').strip()
    if extra_origins:
        origins = ','.join([origins, extra_origins])

    os.environ['BOKEH_ALLOW_WS_ORIGIN'] = origins

    # Bokeh signs a session token into the page and rejects the websocket if it
    # is redeemed later than this. The default of 300s is easily exceeded by a
    # slow first render or a tab left open before it connects, which shows up
    # as a blank page and "Token is expired" in the log.
    server = Server({'/': bkapp},
                    address='0.0.0.0',
                    port=port, num_procs=nproc,
                    session_token_expiration=int(
                        # Blank counts as unset: compose forwards the variable
                        # even when it has no value.
                        os.environ.get('SESSION_TOKEN_EXPIRATION') or 3600))
    server.start()
    print('Opening Bokeh application on http://localhost:{0}/'.format(server.port))
    if browser:
        server.io_loop.add_callback(server.show,'/')
    else:
        server.io_loop.add_callback(server.show,'/','')
    server.io_loop.start()


if __name__ == '__main__':
    main()
