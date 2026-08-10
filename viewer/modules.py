import os
import datajoint as dj


#: Directory the share's contents sit under, whatever it is mounted on.
STORE_SUBDIRS = ('external_dj_blobs', 'external_files')


def _infer_old_root(locations):
    '''
    Work out the prefix the configured store paths share, by looking for the
    directory the share's contents are known to sit under. Inferring beats
    hardcoding a platform's mount point: the config comes from whichever machine
    wrote it, and this way no particular host layout is assumed.
    '''
    for location in locations:
        for subdir in STORE_SUBDIRS:
            marker = '/' + subdir
            if marker in location:
                return location[:location.index(marker)]
    return None


def _relocate_stores():
    '''
    Re-root the external blob stores onto this host's mount point.

    dj_local_conf.json is untracked per-deployment config (it carries the
    database password) and reaches the container through the repo bind mount, so
    one file has to serve both the host and the container even when they mount
    the share in different places. DJ_STORE_ROOT rewrites the prefix at startup:
    the file keeps whatever the host uses.
    '''
    # Treat an empty value as unset: compose passes the variable through even
    # when it is blank, and an empty prefix would match every path.
    store_root = os.environ.get('DJ_STORE_ROOT')
    if not store_root:
        return

    stores = dj.config.get('stores') or {}
    locations = [s.get('location') for s in stores.values() if s.get('location')]

    old_root = os.environ.get('DJ_STORE_ROOT_REPLACES') or _infer_old_root(
        locations)
    if not old_root or old_root == store_root:
        return

    for store in stores.values():
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
