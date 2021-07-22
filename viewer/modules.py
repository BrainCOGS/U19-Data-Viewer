import datajoint as dj

lab = dj.create_virtual_module('lab', 'u19_lab')
subject = dj.create_virtual_module('subject', 'u19_subject')
action = dj.create_virtual_module('action', 'u19_action')
acquisition = dj.create_virtual_module('acquisition', 'u19_acquisition')
behavior = dj.create_virtual_module('behavior', 'u19_behavior')
puffs = dj.create_virtual_module('puffs', 'u19_puffs')
