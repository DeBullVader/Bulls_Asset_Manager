from . import marketplace_auth
from . import marketplace_ui_auth
from . import marketplace_download
from . import marketplace_ui_profile
from . import marketplace_ui_browse


def register():
    marketplace_auth.register()
    marketplace_download.register()
    marketplace_ui_auth.register()
    marketplace_ui_profile.register()
    marketplace_ui_browse.register()


def unregister():
    marketplace_ui_browse.unregister()
    marketplace_ui_profile.unregister()
    marketplace_ui_auth.unregister()
    marketplace_download.unregister()
    marketplace_auth.unregister()
