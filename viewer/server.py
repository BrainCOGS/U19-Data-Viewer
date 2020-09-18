import pandas as pd
import os
from os.path import join as pjoin
from bokeh.server.server import Server
from bokeh.models.widgets import Tabs
from subject_tab import subject_tab
from session_tab import session_tab

import datajoint as dj

def datajoint_dot():
    from bokeh.models import Div
    from bokeh.layouts import layout
    from bokeh.models.widgets import Panel

    subject = dj.create_virtual_module('subject', 'u19_subject')
    action = dj.create_virtual_module('action', 'u19_action')
    acquisition = dj.create_virtual_module('acquisition', 'u19_acquisition')

    try:
        svg = (dj.Diagram(subject) + dj.Diagram(action) + dj.Diagram(acquisition)).make_dot().create_svg()
        div = Div(text = '<object data={0}'.format(svg.decode('utf-8')))
        # for some reason div can handle incomplete tags, completing is has artifact.
    except:
        print('Could not get diagram, did you install graphviz and pydotplus??')
        div = Div(text='installation not complete')
    return Panel(child=layout([div]),title='Overview')


def bkapp(doc):

    tabs = Tabs(tabs=[datajoint_dot(), subject_tab(), session_tab()], active=1)

    doc.add_root(tabs)
    doc.title = 'Princeton U19 DataJoint Interface'

def main():
    import sys
    from argparse import ArgumentParser
    parser = ArgumentParser(
        description='Princeton U19 DataJoint Interface')
    parser.add_argument('-p','--port',
                        type=int,
                        default=5900,
                        help='port for the bokeh server',
                        action='store')
    parser.add_argument('-n','--num-proc',
                        type=int,
                        default=1,
                        help='number of processes for the bokeh server (zero is auto)',
                        action='store')
    parser.add_argument('-b','--browser',
                        default = False,
                        action='store_true')


    ops = parser.parse_args()
    port = ops.port
    nproc = ops.num_proc
    browser = ops.browser
    import socket
    hostname = socket.gethostname()
    ipaddress = socket.gethostbyname(hostname)
    os.environ['BOKEH_ALLOW_WS_ORIGIN']='localhost:{0},0.0.0.0:{0}'.format(
        port, hostname, ipaddress)

    os.environ['BOKEH_ALLOW_WS_ORIGIN']=','.join(['localhost:{0}',
                                                  '0.0.0.0:{0}',
                                                  '{1}:{0},{2}:{0}',
                                                  '{1}.princeton.edu:{0}']).format(
        port, hostname, ipaddress)

    server = Server({'/': bkapp},
                    address='0.0.0.0',
                    port=port,num_procs=nproc)
    server.start()
    print('Opening Bokeh application on http://localhost:{0}/'.format(server.port))
    if browser:
        server.io_loop.add_callback(server.show,'/')
    else:
        server.io_loop.add_callback(server.show,'/','')
    server.io_loop.start()

if __name__ == '__main__':
    main()
