"""
marketplace_auth.py
───────────────────
Handles the full browser-based OAuth login flow for the PolyAssetVault addon.

Flow:
  1. UB_OT_MarketplaceLogin.invoke() calls start_auth_flow()
  2. start_auth_flow() picks a free port, starts OAuthCallbackServer in a
     daemon thread, opens the browser to /addon-login?state=X&port=PORT
  3. The user logs in on the website; the site redirects to:
       http://localhost:PORT/callback?token=JWT&state=X
  4. OAuthCallbackServer catches the redirect, verifies state, stores JWT
     in _auth_state, then shuts itself down
  5. The modal timer in UB_OT_MarketplaceLogin polls _auth_state every 0.5s
  6. On success: exchanges the JWT for a 30-day device token via the API,
     then stores the token in addon preferences
"""

import bpy
import threading
import secrets
import webbrowser
import socket
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime

from ..utils.addon_logger import addon_logger
from ..utils import addon_info
from .marketplace_api import MarketplaceAPI

import bpy.utils


# ── Shared auth state (written by server thread, read by modal operator) ──────

_auth_lock = threading.Lock()
_auth_state: dict = {}          # keys: completed, error, jwt, username


def _set_auth_state(**kwargs):
    with _auth_lock:
        _auth_state.clear()
        _auth_state.update(kwargs)


def get_auth_state() -> dict:
    with _auth_lock:
        return dict(_auth_state)


def clear_auth_state():
    with _auth_lock:
        _auth_state.clear()


# ── Local callback HTTP server ────────────────────────────────────────────────

_server_instance: HTTPServer | None = None


class _CallbackHandler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        """Handle CORS preflight — browser sends this before fetch() to localhost."""
        print(f"[MARKETPLACE] CORS preflight OPTIONS received from {self.client_address}")
        self.send_response(200)
        self._add_cors_headers()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        print(f"[MARKETPLACE] GET received: {self.path}")
        parsed = urlparse(self.path)

        if parsed.path != "/callback":
            print(f"[MARKETPLACE] Ignored non-callback path: {parsed.path}")
            self._respond(404, "Not Found")
            return

        params = parse_qs(parsed.query)
        token = params.get("token", [None])[0]
        state = params.get("state", [None])[0]

        expected_state = self.server.expected_state
        print(f"[MARKETPLACE] Callback — token present: {bool(token)}, state match: {state == expected_state}")

        if not token or state != expected_state:
            print(f"[MARKETPLACE] Callback rejected — state expected={expected_state!r} got={state!r}")
            self._respond(400, "Invalid callback — state mismatch or missing token.")
            _set_auth_state(error="Login failed: invalid callback received.")
            self._shutdown_later()
            return

        # Success — store JWT for the modal operator to pick up
        print("[MARKETPLACE] Callback accepted — JWT stored, waiting for modal to exchange it")
        _set_auth_state(jwt=token, completed=False)
        self._respond(200, '{"ok":true}', content_type="application/json")
        self._shutdown_later()

    def _add_cors_headers(self):
        """Allow the marketplace website to call our local callback server."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _respond(self, code: int, body: str, content_type: str = "text/plain"):
        encoded = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self._add_cors_headers()
        self.end_headers()
        self.wfile.write(encoded)

    def _shutdown_later(self):
        t = threading.Thread(target=self.server.shutdown, daemon=True)
        t.start()

    def log_message(self, format, *args):
        addon_logger.debug(f"OAuth callback: {format % args}")


def _find_free_port() -> int:
    """Find a free port in the ephemeral range (49152–65535)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


# ── Public API ────────────────────────────────────────────────────────────────

def start_auth_flow() -> str | None:
    """
    Start the OAuth flow. Opens the browser and starts the local callback server.
    Returns an error string on failure, or None on success.
    """
    global _server_instance

    clear_auth_state()

    try:
        prefs = addon_info.get_addon_prefs()
        base_url = prefs.marketplace_api_url.rstrip("/")
        state = secrets.token_urlsafe(24)
        port = _find_free_port()

        server = HTTPServer(("127.0.0.1", port), _CallbackHandler)
        server.expected_state = state
        server.timeout = 1
        _server_instance = server

        def _serve():
            print(f"[MARKETPLACE] Callback server listening on 127.0.0.1:{port}")
            server.serve_forever()
            print(f"[MARKETPLACE] Callback server stopped")

        t = threading.Thread(target=_serve, daemon=True)
        t.start()

        login_url = f"{base_url}/addon-login?state={state}&port={port}"
        print(f"[MARKETPLACE] Opening browser: {login_url}")
        webbrowser.open(login_url)

        return None

    except Exception as e:
        print(f"[MARKETPLACE] ERROR starting auth flow: {e}")
        addon_logger.exception("Failed to start auth flow")
        return f"Could not start login: {e}"


def abort_auth_flow():
    """Shut down the callback server if it is still running (e.g. on timeout)."""
    global _server_instance
    if _server_instance:
        try:
            _server_instance.shutdown()
        except Exception:
            pass
        _server_instance = None
    clear_auth_state()


def exchange_and_save_token(jwt: str) -> tuple[bool, str]:
    """
    Exchange a short-lived JWT for a 30-day device token and save it to prefs.
    Returns (success, error_message_or_empty).
    """
    try:
        import platform
        from .. import bl_info as addon_bl_info

        prefs = addon_info.get_addon_prefs()
        api = MarketplaceAPI(prefs.marketplace_api_url)

        meta = {
            "deviceName": f"Blender Addon — {platform.system()}",
            "blenderVersion": bpy.app.version_string,
            "addonVersion": ".".join(str(x) for x in addon_bl_info["version"]),
            "platform": platform.system(),
        }

        print(f"[MARKETPLACE] Exchanging JWT for device token at {prefs.marketplace_api_url}")
        ok, data = api.exchange_jwt_for_device_token(jwt, meta)
        print(f"[MARKETPLACE] Token exchange response — ok={ok}, data={data}")

        if not ok:
            msg = data.get("message", "Unknown error during token exchange.")
            print(f"[MARKETPLACE] Token exchange FAILED: {msg}")
            addon_logger.error(f"Token exchange failed: {msg}")
            return False, msg

        prefs.addon_device_token = data.get("deviceToken", "")
        prefs.addon_token_expires = data.get("expiresAt", "")
        prefs.addon_username = data.get("username", "")
        prefs.addon_user_id = str(data.get("userId", ""))
        bpy.ops.wm.save_userpref()

        print(f"[MARKETPLACE] Logged in as: {prefs.addon_username}")
        addon_logger.info(f"Logged in as {prefs.addon_username}")
        return True, ""

    except Exception as e:
        print(f"[MARKETPLACE] EXCEPTION in exchange_and_save_token: {e}")
        addon_logger.exception("Unexpected error exchanging token")
        return False, str(e)


def logout() -> tuple[bool, str]:
    """Revoke the stored device token and clear prefs."""
    try:
        prefs = addon_info.get_addon_prefs()

        if prefs.addon_device_token:
            api = MarketplaceAPI(prefs.marketplace_api_url, prefs.addon_device_token)
            ok, data = api.revoke_token()
            if not ok:
                addon_logger.warning(f"Token revocation failed: {data.get('message')}")

        prefs.addon_device_token = ""
        prefs.addon_token_expires = ""
        prefs.addon_username = ""
        prefs.addon_user_id = ""
        bpy.ops.wm.save_userpref()

        addon_logger.info("Logged out of PolyAssetVault")
        return True, ""

    except Exception as e:
        addon_logger.exception("Error during logout")
        return False, str(e)


# 401 messages the server sends when the token is no longer valid
_TOKEN_INVALID_MESSAGES = (
    "Addon device token has expired. Please log in again.",
    "Addon device token has been revoked. Please log in again.",
    "Invalid addon device token.",
    "Addon device token required in X-Addon-Token header.",
)


def _is_token_invalid_response(data: dict) -> bool:
    """Return True if the API response message signals the token must be cleared."""
    return data.get("message", "") in _TOKEN_INVALID_MESSAGES


def clear_token_if_invalid(ok: bool, data: dict) -> bool:
    """
    Call after any API request. If the server says the token is invalid/expired,
    clears the stored token so the UI shows the login button again.
    Returns True if the token was cleared.
    """
    if not ok and _is_token_invalid_response(data):
        try:
            prefs = addon_info.get_addon_prefs()
            prefs.addon_device_token = ""
            prefs.addon_token_expires = ""
            prefs.addon_username = ""
            prefs.addon_user_id = ""
            _clear_token_file()
            bpy.ops.wm.save_userpref()
            addon_logger.info("Token cleared after server rejected it.")
        except Exception:
            addon_logger.exception("Failed to clear token after invalid response")
        return True
    return False


def is_logged_in() -> bool:
    """Return True if a non-expired device token is stored locally."""
    try:
        prefs = addon_info.get_addon_prefs()
        if not prefs.addon_device_token:
            return False
        if prefs.addon_token_expires:
            from datetime import timezone
            expires = datetime.fromisoformat(
                prefs.addon_token_expires.replace("Z", "+00:00")
            )
            if expires < datetime.now(timezone.utc):
                return False
        return True
    except Exception:
        return False


def verify_token_with_server() -> bool:
    """
    Call /api/addon/auth/me to confirm the stored token is still valid server-side.
    Clears the token and returns False if the server rejects it.
    """
    if not is_logged_in():
        return False
    api = get_api()
    ok, data = api.verify_token()
    if clear_token_if_invalid(ok, data):
        return False
    return ok


def get_api() -> MarketplaceAPI:
    """Return a ready-to-use MarketplaceAPI instance using the stored token."""
    prefs = addon_info.get_addon_prefs()
    return MarketplaceAPI(prefs.marketplace_api_url, prefs.addon_device_token)


# ── Operators ─────────────────────────────────────────────────────────────────

class UB_OT_MarketplaceLogin(bpy.types.Operator):
    bl_idname = "ub.marketplace_login"
    bl_label = "Login to PolyAssetVault"
    bl_description = "Open the browser to log in to your PolyAssetVault account"
    bl_options = {'REGISTER'}

    _timer = None
    _elapsed: float = 0.0
    _timeout: float = 120.0   # 2 minutes

    @classmethod
    def poll(cls, context):
        return not is_logged_in()

    def invoke(self, context, event):
        error = start_auth_flow()
        if error:
            self.report({'ERROR'}, error)
            return {'CANCELLED'}

        self._elapsed = 0.0
        self._timer = context.window_manager.event_timer_add(0.5, window=context.window)
        context.window_manager.modal_handler_add(self)
        # Tag the area so "Waiting for browser..." appears immediately
        context.area.tag_redraw()
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        self._elapsed += 0.5
        state = get_auth_state()

        # Server received the callback and stored a JWT
        if "jwt" in state and not state.get("completed"):
            print("[MARKETPLACE] Modal picked up JWT — starting token exchange")
            jwt = state["jwt"]
            _set_auth_state(completed=True)   # prevent double-processing
            ok, err = exchange_and_save_token(jwt)
            self._finish(context)
            if ok:
                prefs = addon_info.get_addon_prefs()
                self.report({'INFO'}, f"Logged in as {prefs.addon_username}")
                context.area.tag_redraw()
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, f"Login failed: {err}")
                return {'CANCELLED'}

        if state.get("error"):
            print(f"[MARKETPLACE] Modal got error state: {state['error']}")
            self._finish(context)
            self.report({'ERROR'}, state["error"])
            return {'CANCELLED'}

        if self._elapsed >= self._timeout:
            self._finish(context)
            abort_auth_flow()
            self.report({'WARNING'}, "Login timed out. Please try again.")
            return {'CANCELLED'}

        context.area.tag_redraw()
        return {'PASS_THROUGH'}

    def _finish(self, context):
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
        clear_auth_state()


class UB_OT_MarketplaceCancelLogin(bpy.types.Operator):
    bl_idname = "ub.marketplace_cancel_login"
    bl_label = "Cancel Login"
    bl_description = "Cancel the pending PolyAssetVault login"
    bl_options = {'REGISTER'}

    def execute(self, context):
        abort_auth_flow()
        context.area.tag_redraw()
        return {'FINISHED'}


class UB_OT_MarketplaceLogout(bpy.types.Operator):
    bl_idname = "ub.marketplace_logout"
    bl_label = "Logout"
    bl_description = "Log out of your PolyAssetVault account"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return is_logged_in()

    def execute(self, context):
        ok, err = logout()
        if ok:
            self.report({'INFO'}, "Logged out of PolyAssetVault")
        else:
            self.report({'ERROR'}, f"Logout error: {err}")
        context.area.tag_redraw()
        return {'FINISHED'}


# ── Registration ──────────────────────────────────────────────────────────────

classes = (
    UB_OT_MarketplaceLogin,
    UB_OT_MarketplaceCancelLogin,
    UB_OT_MarketplaceLogout,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    abort_auth_flow()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
