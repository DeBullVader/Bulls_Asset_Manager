from . import addon_info
from . import addon_logger



def register():
   addon_info.register()

def unregister():
   addon_logger.unregister()
   addon_info.unregister()

   



