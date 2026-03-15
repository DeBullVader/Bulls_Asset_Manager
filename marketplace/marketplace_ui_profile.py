"""
marketplace_ui_profile.py
──────────────────────────
"My Purchases" sub-panel — lists purchased products with per-item download buttons.
Parented to UB_PT_MarketplaceAuth and only shown when logged in.
"""

import bpy
import threading
from bpy.utils import register_classes_factory

from ..utils.addon_logger import addon_logger
from . import marketplace_auth
from .marketplace_download import is_downloading


# ── Purchases cache ───────────────────────────────────────────────────────────

_cache_lock = threading.Lock()
_purchases_cache: dict = {}   # keys: loading, data, error


def _set_cache(**kwargs):
    with _cache_lock:
        _purchases_cache.update(kwargs)


def get_purchases_cache() -> dict:
    with _cache_lock:
        return dict(_purchases_cache)


def _fetch_purchases():
    """Run in a background thread — fetches purchases and updates the cache."""
    _set_cache(loading=True, data=None, error=None)
    try:
        api = marketplace_auth.get_api()
        ok, data = api.get_purchases()
        print(f"[MARKETPLACE] get_purchases response — ok={ok}, data={data}")
        marketplace_auth.clear_token_if_invalid(ok, data)
        if ok:
            # API may return {"purchases": [...]} or a bare list
            purchases = data.get("purchases", data if isinstance(data, list) else [])
            if purchases:
                print(f"[MARKETPLACE] First purchase entry: {purchases[0]}")
            _set_cache(loading=False, data=purchases, error=None)
        else:
            msg = data.get("message", "Failed to fetch purchases.")
            _set_cache(loading=False, data=None, error=msg)
    except Exception as e:
        addon_logger.exception("Error fetching purchases")
        _set_cache(loading=False, data=None, error=str(e))


def fetch_purchases_async():
    t = threading.Thread(target=_fetch_purchases, daemon=True)
    t.start()


# ── Operators ─────────────────────────────────────────────────────────────────

class UB_OT_MarketplaceRefreshPurchases(bpy.types.Operator):
    bl_idname = "ub.marketplace_refresh_purchases"
    bl_label = "Refresh Purchases"
    bl_description = "Reload your purchased assets list from PolyAssetVault"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, _context):
        return marketplace_auth.is_logged_in()

    def execute(self, context):
        fetch_purchases_async()
        context.area.tag_redraw()
        return {'FINISHED'}


# ── Panel ─────────────────────────────────────────────────────────────────────

class UB_PT_MarketplaceProfile(bpy.types.Panel):
    bl_idname = "UB_PT_MarketplaceProfile"
    bl_label = "My Purchases"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BullTools"
    bl_parent_id = "UB_PT_MarketplaceAuth"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 1

    @classmethod
    def poll(cls, _context):
        return marketplace_auth.is_logged_in()

    def draw(self, _context):
        layout = self.layout
        cache = get_purchases_cache()

        row = layout.row(align=True)
        row.operator(
            "ub.marketplace_refresh_purchases",
            text="Refresh",
            icon='FILE_REFRESH',
        )

        if cache.get("loading"):
            layout.label(text="Loading purchases...", icon='TIME')
            return

        if cache.get("error"):
            layout.label(text=cache["error"], icon='ERROR')
            return

        purchases = cache.get("data")
        if purchases is None:
            layout.label(text="Press Refresh to load purchases", icon='INFO')
            return

        if not purchases:
            layout.label(text="No purchases found", icon='INFO')
            return

        dl_active = is_downloading()
        col = layout.column(align=True)
        for purchase in purchases:
            product_id = purchase.get("productId", "")
            product_name = purchase.get("title", purchase.get("name", product_id))

            box = col.box()
            row = box.row(align=True)
            row.label(text=product_name, icon='ASSET_MANAGER')
            dl_op = row.operator(
                "ub.marketplace_download",
                text="",
                icon='IMPORT',
            )
            dl_op.product_id = product_id
            dl_op.product_name = product_name
            if dl_active:
                row.enabled = False


# ── Registration ──────────────────────────────────────────────────────────────

classes = (
    UB_OT_MarketplaceRefreshPurchases,
    UB_PT_MarketplaceProfile,
)
register_classes, unregister_classes = register_classes_factory(classes)


def register():
    register_classes()


def unregister():
    unregister_classes()
