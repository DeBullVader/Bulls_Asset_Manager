"""
marketplace_ui_browse.py
─────────────────────────
"Browse Store" sub-panel — search and paginate all PolyAssetVault products.
Parented to UB_PT_MarketplaceAuth and only shown when logged in.

Search state (query, page) lives on WindowManager so it survives panel redraws.
"""

import bpy
import threading
from bpy.utils import register_classes_factory

from ..utils.addon_logger import addon_logger
from ..utils import addon_info
from . import marketplace_auth
from .marketplace_download import is_downloading


# ── Browse results cache ──────────────────────────────────────────────────────

_cache_lock = threading.Lock()
_browse_cache: dict = {}   # keys: loading, data, error, page, total_pages


def _set_cache(**kwargs):
    with _cache_lock:
        _browse_cache.update(kwargs)


def get_browse_cache() -> dict:
    with _cache_lock:
        return dict(_browse_cache)


def _fetch_products(search: str, category: str, page: int):
    """Run in a background thread — fetches products and updates the cache."""
    _set_cache(loading=True, error=None)
    try:
        api = marketplace_auth.get_api()
        ok, data = api.browse_products(search=search, category=category, page=page, limit=20)
        marketplace_auth.clear_token_if_invalid(ok, data)
        if ok:
            print(f"[MARKETPLACE] browse_products response — ok={ok}, keys={list(data.keys()) if isinstance(data, dict) else 'list'}")
            products = data.get("products", data if isinstance(data, list) else [])
            if products:
                print(f"[MARKETPLACE] First product entry: {products[0]}")
            total_pages = data.get("totalPages", data.get("total_pages", data.get("pages", 1)))
            _set_cache(
                loading=False,
                data=products,
                error=None,
                page=page,
                total_pages=max(1, total_pages),
            )
        else:
            msg = data.get("message", "Failed to fetch products.")
            _set_cache(loading=False, data=None, error=msg)
    except Exception as e:
        addon_logger.exception("Error fetching products")
        _set_cache(loading=False, data=None, error=str(e))


def fetch_products_async(search: str, category: str, page: int):
    t = threading.Thread(target=_fetch_products, args=(search, category, page), daemon=True)
    t.start()


# ── WindowManager PropertyGroup for search state ──────────────────────────────

class E_MarketplaceBrowse(bpy.types.PropertyGroup):
    search: bpy.props.StringProperty(
        name="Search",
        description="Search for products by name",
        default="",
    )
    category: bpy.props.StringProperty(
        name="Category",
        description="Filter by category (leave blank for all)",
        default="",
    )


# ── Operators ─────────────────────────────────────────────────────────────────

class UB_OT_MarketplaceBrowse(bpy.types.Operator):
    bl_idname = "ub.marketplace_browse"
    bl_label = "Search"
    bl_description = "Search PolyAssetVault products"
    bl_options = {'REGISTER'}

    page: bpy.props.IntProperty(default=1, options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return marketplace_auth.is_logged_in()

    def execute(self, context):
        browse = context.window_manager.marketplace_browse
        fetch_products_async(browse.search, browse.category, self.page)
        context.area.tag_redraw()
        return {'FINISHED'}


# ── Panel ─────────────────────────────────────────────────────────────────────

class UB_PT_MarketplaceBrowse(bpy.types.Panel):
    bl_idname = "UB_PT_MarketplaceBrowse"
    bl_label = "Browse Store"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BullTools"
    bl_parent_id = "UB_PT_MarketplaceAuth"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 2

    @classmethod
    def poll(cls, context):
        return marketplace_auth.is_logged_in()

    def draw(self, context):
        layout = self.layout
        browse = context.window_manager.marketplace_browse
        cache = get_browse_cache()

        # ── Search bar ─────────────────────────────────────────────────────
        col = layout.column(align=True)
        col.prop(browse, "search", text="", icon='VIEWZOOM')
        search_op = col.operator("ub.marketplace_browse", text="Search", icon='VIEWZOOM')
        search_op.page = 1

        layout.separator(factor=0.5)

        # ── Results ────────────────────────────────────────────────────────
        if cache.get("loading"):
            layout.label(text="Loading products...", icon='TIME')
            return

        if cache.get("error"):
            layout.label(text=cache["error"], icon='ERROR')
            return

        products = cache.get("data")
        if products is None:
            layout.label(text="Search to browse products", icon='INFO')
            return

        if not products:
            layout.label(text="No products found", icon='INFO')
        else:
            dl_active = is_downloading()
            col = layout.column(align=True)
            for product in products:
                # Mongoose adds a virtual 'id' field; fall back to '_id' if absent
                product_id = str(product.get("id") or product.get("_id", ""))
                product_name = product.get("name", product.get("title", product_id))
                owned = product.get("owned", False)

                box = col.box()
                row = box.row(align=True)
                icon = 'CHECKMARK' if owned else 'ASSET_MANAGER'
                row.label(text=product_name, icon=icon)

                if owned:
                    dl_op = row.operator(
                        "ub.marketplace_download",
                        text="",
                        icon='IMPORT',
                    )
                    dl_op.product_id = product_id
                    dl_op.product_name = product_name
                    if dl_active:
                        row.enabled = False
                else:
                    # Build the product page URL from shortName or id
                    short_name = product.get("shortName", product.get("slug", product_id))
                    prefs = addon_info.get_addon_prefs()
                    product_url = prefs.marketplace_api_url.rstrip("/") + "/products/" + short_name
                    buy_op = row.operator("bu.url_open", text="Purchase", icon='URL')
                    buy_op.url = product_url

        # ── Pagination ─────────────────────────────────────────────────────
        page = cache.get("page", 1)
        total_pages = cache.get("total_pages", 1)
        if total_pages > 1:
            row = layout.row(align=True)
            row.alignment = 'CENTER'
            prev_op = row.operator("ub.marketplace_browse", text="", icon='TRIA_LEFT')
            prev_op.page = max(1, page - 1)
            row.label(text=f"{page} / {total_pages}")
            next_op = row.operator("ub.marketplace_browse", text="", icon='TRIA_RIGHT')
            next_op.page = min(total_pages, page + 1)


# ── Registration ──────────────────────────────────────────────────────────────

classes = (
    E_MarketplaceBrowse,
    UB_OT_MarketplaceBrowse,
    UB_PT_MarketplaceBrowse,
)
register_classes, unregister_classes = register_classes_factory(classes)


def register():
    register_classes()
    bpy.types.WindowManager.marketplace_browse = bpy.props.PointerProperty(
        type=E_MarketplaceBrowse,
    )


def unregister():
    unregister_classes()
    del bpy.types.WindowManager.marketplace_browse
