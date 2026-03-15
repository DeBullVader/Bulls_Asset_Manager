"""
marketplace_download.py
────────────────────────
Modal download operator for PolyAssetVault products.

Downloads to: <lib_path>/PolyAssetVault/<product_id>.blend
Progress is tracked via a background thread + modal timer + WM progress bar.
"""

import bpy
import threading
import os
from bpy.utils import register_classes_factory

from ..utils import addon_info
from ..utils.addon_logger import addon_logger
from . import marketplace_auth


# ── Download state (one download at a time) ───────────────────────────────────

_dl_lock = threading.Lock()
_dl_state: dict = {}   # keys: running, progress, total, error, done, product_name


def _set_dl_state(**kwargs):
    with _dl_lock:
        _dl_state.update(kwargs)


def get_dl_state() -> dict:
    with _dl_lock:
        return dict(_dl_state)


def is_downloading() -> bool:
    with _dl_lock:
        return bool(_dl_state.get("running"))


# ── Operator ──────────────────────────────────────────────────────────────────

class UB_OT_MarketplaceDownload(bpy.types.Operator):
    bl_idname = "ub.marketplace_download"
    bl_label = "Download Asset"
    bl_description = "Download this product to your local asset library"
    bl_options = {'REGISTER'}

    product_id: bpy.props.StringProperty()
    product_name: bpy.props.StringProperty()

    _timer = None

    @classmethod
    def poll(cls, context):
        return marketplace_auth.is_logged_in() and not is_downloading()

    def invoke(self, context, event):
        prefs = addon_info.get_addon_prefs()
        lib_path = prefs.lib_path

        if not lib_path:
            self.report({'ERROR'}, "No library path set. Set it in addon preferences.")
            return {'CANCELLED'}

        dest_dir = os.path.join(lib_path, "PolyAssetVault")
        dest_path = os.path.join(dest_dir, f"{self.product_id}.blend")

        with _dl_lock:
            _dl_state.clear()
        _set_dl_state(
            running=True,
            progress=0,
            total=None,
            error=None,
            done=False,
            product_name=self.product_name,
            dest_path=dest_path,
        )

        product_id = self.product_id  # capture for thread

        def _download():
            api = marketplace_auth.get_api()

            def _progress(received, total):
                _set_dl_state(progress=received, total=total)

            ok, err = api.download_product(product_id, dest_path, _progress)
            if ok:
                addon_logger.info(f"Download complete: {product_id} → {dest_path}")
                _set_dl_state(running=False, done=True, error=None)
            else:
                addon_logger.warning(f"Download failed: {product_id}: {err}")
                _set_dl_state(running=False, done=False, error=err)

        t = threading.Thread(target=_download, daemon=True)
        t.start()

        self._timer = context.window_manager.event_timer_add(0.25, window=context.window)
        context.window_manager.modal_handler_add(self)
        context.window_manager.progress_begin(0, 100)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        state = get_dl_state()
        progress = state.get("progress", 0)
        total = state.get("total")

        if total:
            pct = int(progress / total * 100)
            context.window_manager.progress_update(pct)

        context.area.tag_redraw()

        if not state.get("running"):
            self._finish(context)
            if state.get("done"):
                name = state.get("product_name") or self.product_id
                self.report({'INFO'}, f"Downloaded: {name}")
                return {'FINISHED'}
            else:
                err = state.get("error", "Unknown error")
                self.report({'ERROR'}, f"Download failed: {err}")
                return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def _finish(self, context):
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
        context.window_manager.progress_end()
        with _dl_lock:
            _dl_state.clear()


# ── Registration ──────────────────────────────────────────────────────────────

classes = (UB_OT_MarketplaceDownload,)
register_classes, unregister_classes = register_classes_factory(classes)


def register():
    register_classes()


def unregister():
    unregister_classes()
