"""
marketplace_ui_auth.py
───────────────────────
Login / logout panel shown in the BullTools N-panel.

States:
  - Not logged in   → "Login to PolyAssetVault" button
  - Login pending   → "Waiting for browser..." + Cancel button
  - Logged in       → username + "Logout" button
"""

import bpy
import threading
from bpy.utils import register_classes_factory

from ..utils import addon_info
from . import marketplace_auth

# Verify the stored token against the server once at startup (non-blocking)
def _verify_on_startup():
    from ..utils import addon_info
    prefs = addon_info.get_addon_prefs()
    token = prefs.addon_device_token
    expires = prefs.addon_token_expires
    username = prefs.addon_username
    print(f"[MARKETPLACE] Startup check — token present: {bool(token)}, expires: {expires!r}, username: {username!r}")
    result = marketplace_auth.verify_token_with_server()
    print(f"[MARKETPLACE] Startup verify result: {result}, still logged in: {marketplace_auth.is_logged_in()}")

def _start_startup_check():
    t = threading.Thread(target=_verify_on_startup, daemon=True)
    t.start()


def _login_pending() -> bool:
    """True while the modal operator is waiting for the browser callback."""
    state = marketplace_auth.get_auth_state()
    # State dict is populated once the flow starts and cleared when done
    return bool(state) and not state.get("completed")


class UB_PT_MarketplaceAuth(bpy.types.Panel):
    bl_idname = "UB_PT_MarketplaceAuth"
    bl_label = "PolyAssetVault"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BullTools"
    bl_parent_id = "VIEW3D_PT_BBPS_MAIN_ADDON_PANEL"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 10

    def draw(self, context):
        layout = self.layout
        prefs = addon_info.get_addon_prefs()

        if marketplace_auth.is_logged_in():
            self._draw_logged_in(layout, prefs)
        elif _login_pending():
            self._draw_pending(layout)
        else:
            self._draw_logged_out(layout)

    def _draw_logged_out(self, layout):
        col = layout.column(align=True)
        col.scale_y = 1.4
        col.operator(
            "ub.marketplace_login",
            text="Login to PolyAssetVault",
            icon='URL',
        )

    def _draw_pending(self, layout):
        col = layout.column(align=True)
        col.label(text="Waiting for browser login...", icon='TIME')
        col.separator(factor=0.5)
        col.operator(
            "ub.marketplace_cancel_login",
            text="Cancel",
            icon='X',
        )

    def _draw_logged_in(self, layout, prefs):
        box = layout.box()
        col = box.column(align=True)
        col.label(text=f"Logged in as:", icon='USER')
        col.label(text=prefs.addon_username)
        col.separator(factor=1)
        col.operator(
            "ub.marketplace_logout",
            text="Logout",
            icon='PANEL_CLOSE',
        )


classes = (UB_PT_MarketplaceAuth,)

register_classes, unregister_classes = register_classes_factory(classes)


def register():
    register_classes()
    _start_startup_check()


def unregister():
    unregister_classes()
