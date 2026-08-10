import os
import datajoint as dj


def _relocate_stores():
    '''
    Re-root the external blob stores onto this host's mount point.

    dj_local_conf.json is untracked per-deployment config (it carries the
    database password) and is shared with the container through the repo bind
    mount, so its paths cannot suit both a macOS host and a Linux container.
    DJ_STORE_ROOT rewrites the prefix at startup instead: the file keeps
    whatever the host uses and the container overrides it.
    '''
    store_root = os.environ.get('DJ_STORE_ROOT')
    if not store_root:
        return

    old_root = os.environ.get('DJ_STORE_ROOT_REPLACES', '/Volumes/u19_dj')
    stores = dj.config.get('stores') or {}
    for name, store in stores.items():
        location = store.get('location')
        if location and location.startswith(old_root):
            store['location'] = store_root + location[len(old_root):]
    dj.config['stores'] = stores


_relocate_stores()

lab = dj.create_virtual_module('lab', 'u19_lab')
subject = dj.create_virtual_module('subject', 'u19_subject')
action = dj.create_virtual_module('action', 'u19_action')
acquisition = dj.create_virtual_module('acquisition', 'u19_acquisition')
behavior = dj.create_virtual_module('behavior', 'u19_behavior')
puffs = dj.create_virtual_module('puffs', 'u19_puffs')
