# Pre-Publish Checklist

Things to clean up before releasing the addon to end users.

---

## Remove Debug Print Statements

These `print()` calls were added during development for debugging. They log
sensitive session info (usernames, token state, API responses) to the terminal
and should be removed before publishing.

### `__init__.py`
- [ ] Line ~108: `print(f"[BullTools] Bulls Asset Manager v... loaded")`
  — module-level load confirmation, not needed in production

### `utils/addon_logger.py`
- [ ] Line ~38: `print(addon_directory)`
  — prints the addon install path on every load

### `marketplace/marketplace_auth.py`
All `[MARKETPLACE]` prefixed prints:
- [ ] `start_auth_flow()` — server start, browser URL
- [ ] `_CallbackHandler.do_OPTIONS()` — preflight log
- [ ] `_CallbackHandler.do_GET()` — logs full callback URL including JWT
- [ ] `exchange_and_save_token()` — logs full API response including token hash
- [ ] `_restore_token_from_session()` — logs username
- [ ] `UB_OT_MarketplaceLogin.modal()` — logs JWT pickup

Also restore silent HTTP server logging:
- [ ] `_CallbackHandler.log_message()` — change back to `pass`

### `marketplace/marketplace_ui_profile.py`
- [ ] `_fetch_purchases()` — prints full purchases API response

### `marketplace/marketplace_ui_browse.py`
- [ ] `_fetch_products()` — prints full products API response

---

## Security Check

- [ ] Confirm no `print()` call outputs `addon_device_token` raw value
  (currently none do — token exchange response is logged but contains the
  hashed server token, not a password)
- [ ] `bpy.app.driver_namespace` session cache is **fine to keep** — it is
  in-memory only, lives within the Blender session, and holds the same token
  already stored in preferences

---

## General Polish

- [ ] Set `addon_logger` level back to `logging.WARNING` in `addon_logger.py`
  (currently INFO, which is verbose for end users)
- [ ] Review all `addon_logger.info()` calls — keep warnings/errors, consider
  removing routine info messages
- [ ] Remove `ADDON_BACKEND_SPEC.md` and `ADDON_BACKEND_PLAN_REVIEW.txt`
  from the distributed package (internal dev docs, not for users)

---

## Release Flow

1. Complete items above on the `dev` branch
2. Run a full test: login → browse → purchases → download
3. Merge `dev` → `main`
4. Tag a release version in `bl_info["version"]`
5. Zip the addon folder (excluding `.git`, `.claude`, `error_logs`, `__pycache__`)
