# PolyAssetVault — Blender Addon Backend Integration Spec

**For:** Backend developer / AI implementing on the Market backend
**Repo:** The existing PolyAssetVault Market backend
**Purpose:** Add a dedicated auth and API surface for the BullTools Blender addon

---

## Overview

The Blender addon needs to authenticate users and access marketplace data from inside Blender.
The auth flow works as follows:

1. User clicks "Login" inside Blender
2. Addon opens the browser to `https://polyassetvault.com/addon-login?state=XXXX&port=PORT`
3. User logs in on the website as normal (all existing auth, 2FA, trusted devices apply)
4. Site redirects to `http://localhost:PORT/callback?token=JWT&state=XXXX`
5. Addon catches the redirect locally, extracts the JWT
6. Addon calls `POST /api/addon/auth/device-token` with the JWT as Bearer token
7. Server issues a 30-day addon device token, returns it
8. JWT is discarded. All subsequent addon API calls use `X-Addon-Token: <device_token>`

---

## What Already Exists (Do NOT duplicate)

- `protect` middleware in `backend/middleware/authMiddleware.js` — JWT verification
- `protectGpuDevice` middleware in `backend/middleware/gpuDeviceMiddleware.js` — GPU device token auth
- `GpuNode` model in `backend/models/GpuNode.js` — GPU node device tokens
- All routes in `backend/routes/` — none of these are addon routes
- `/api/auth/login` — standard user login (not for addon use)
- `/api/orders` — order endpoints (not to be used directly by addon)

**Verified: no `/api/addon` routes exist anywhere in the codebase.**

---

## Files to Create

### 1. `backend/models/AddonDevice.js`

```javascript
const crypto = require('crypto');
const mongoose = require('mongoose');

const addonDeviceSchema = mongoose.Schema(
  {
    userId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User',
      required: true,
      index: true,
    },
    tokenHash: {
      type: String,
      required: true,
      unique: true,
      index: true,
      select: false, // Never returned in queries by default
    },
    deviceName: {
      type: String,
      default: 'Blender Addon',
      maxlength: 120,
    },
    blenderVersion: {
      type: String,
      default: '',
      maxlength: 32,
    },
    addonVersion: {
      type: String,
      default: '',
      maxlength: 32,
    },
    platform: {
      type: String,
      default: '',
      maxlength: 64,
    },
    issuedAt: {
      type: Date,
      default: Date.now,
    },
    expiresAt: {
      type: Date,
      required: true,
      index: true,
    },
    lastUsedAt: {
      type: Date,
      default: null,
    },
    revokedAt: {
      type: Date,
      default: null,
    },
  },
  { timestamps: true }
);

// Issue a new raw device token. Returns the raw token (returned once to the caller).
// Stores only the SHA256 hash.
addonDeviceSchema.statics.issueToken = function (userId, meta = {}) {
  const rawToken = crypto.randomBytes(32).toString('hex');
  const ttlDays = 30;
  const expiresAt = new Date(Date.now() + ttlDays * 24 * 60 * 60 * 1000);

  const doc = new this({
    userId,
    tokenHash: crypto.createHash('sha256').update(rawToken).digest('hex'),
    expiresAt,
    deviceName: meta.deviceName || 'Blender Addon',
    blenderVersion: meta.blenderVersion || '',
    addonVersion: meta.addonVersion || '',
    platform: meta.platform || '',
  });

  return { doc, rawToken };
};

// Verify a raw token. Returns the AddonDevice document or null.
addonDeviceSchema.statics.verifyToken = async function (rawToken) {
  const tokenHash = crypto.createHash('sha256').update(rawToken).digest('hex');
  return this.findOne({ tokenHash }).select('+tokenHash').populate('userId');
};

addonDeviceSchema.index({ userId: 1, revokedAt: 1 });
addonDeviceSchema.index({ expiresAt: 1 }); // For cleanup job

const AddonDevice = mongoose.model('AddonDevice', addonDeviceSchema);
module.exports = AddonDevice;
```

---

### 2. `backend/middleware/addonAuthMiddleware.js`

```javascript
const crypto = require('crypto');
const AddonDevice = require('../models/AddonDevice');

/**
 * Middleware: authenticate requests from the Blender addon.
 * Reads the raw device token from the X-Addon-Token header.
 * Sets req.user (populated User doc) and req.addonDevice on success.
 */
async function protectAddon(req, res, next) {
  const rawToken = req.headers['x-addon-token'];

  if (!rawToken || typeof rawToken !== 'string') {
    return res.status(401).json({ message: 'Addon device token required in X-Addon-Token header.' });
  }

  const device = await AddonDevice.verifyToken(rawToken);

  if (!device) {
    return res.status(401).json({ message: 'Invalid addon device token.' });
  }

  if (device.revokedAt) {
    return res.status(401).json({ message: 'Addon device token has been revoked. Please log in again.' });
  }

  if (device.expiresAt && device.expiresAt.getTime() <= Date.now()) {
    return res.status(401).json({ message: 'Addon device token has expired. Please log in again.' });
  }

  // Update last used timestamp (fire-and-forget, don't block the request)
  device.lastUsedAt = new Date();
  device.save().catch(() => {});

  req.addonDevice = device;
  req.user = device.userId;
  req.userId = device.userId._id;

  next();
}

module.exports = { protectAddon };
```

---

### 3. `backend/controllers/addonController.js`

```javascript
const asyncHandler = require('express-async-handler');
const crypto = require('crypto');
const AddonDevice = require('../models/AddonDevice');
const Order = require('../models/Order');
const Product = require('../models/Product');

// ─── Auth ────────────────────────────────────────────────────────────────────

/**
 * POST /api/addon/auth/device-token
 * Protected by standard JWT `protect` middleware.
 * Exchanges a short-lived JWT for a 30-day addon device token.
 * Call this immediately after the browser OAuth callback delivers the JWT.
 */
const issueDeviceToken = asyncHandler(async (req, res) => {
  const { deviceName, blenderVersion, addonVersion, platform } = req.body;

  const { doc, rawToken } = AddonDevice.issueToken(req.user._id, {
    deviceName: deviceName || 'Blender Addon',
    blenderVersion: blenderVersion || '',
    addonVersion: addonVersion || '',
    platform: platform || '',
  });

  await doc.save();

  res.status(201).json({
    deviceToken: rawToken,           // Raw token — addon must store this securely
    expiresAt: doc.expiresAt,
    userId: req.user._id,
    username: req.user.username,
    userType: req.user.userType,
  });
});

/**
 * DELETE /api/addon/auth/device-token
 * Protected by `protectAddon` middleware.
 * Revokes the current addon device token (logout).
 */
const revokeDeviceToken = asyncHandler(async (req, res) => {
  req.addonDevice.revokedAt = new Date();
  await req.addonDevice.save();

  res.status(200).json({ message: 'Logged out successfully.' });
});

/**
 * GET /api/addon/auth/me
 * Protected by `protectAddon` middleware.
 * Returns the current user's profile and token metadata.
 * Use this to verify the stored token is still valid on addon startup.
 */
const getMe = asyncHandler(async (req, res) => {
  const user = req.user;

  res.status(200).json({
    userId: user._id,
    username: user.username,
    email: user.email,
    userType: user.userType,
    profileImage: user.profileImage || null,
    tokenExpiresAt: req.addonDevice.expiresAt,
  });
});

// ─── Purchases ───────────────────────────────────────────────────────────────

/**
 * GET /api/addon/purchases
 * Protected by `protectAddon` middleware.
 * Returns all products the user has purchased and paid for.
 */
const getPurchases = asyncHandler(async (req, res) => {
  const userId = req.user._id;

  const orders = await Order.find({
    userId,
    paymentStatus: 'paid',
    status: { $in: ['completed', 'processing'] },
  })
    .populate({
      path: 'items.productId',
      select: 'title shortDescription category tags thumbnails shortName userId status',
      populate: { path: 'userId', select: 'username' },
    })
    .select('items createdAt')
    .lean();

  // Flatten order items into a list of purchased products
  const purchased = [];
  const seen = new Set();

  for (const order of orders) {
    for (const item of order.items) {
      const product = item.productId;
      if (!product || seen.has(String(product._id))) continue;
      if (product.status !== 'published') continue;
      seen.add(String(product._id));

      purchased.push({
        productId: product._id,
        title: product.title,
        shortDescription: product.shortDescription || '',
        category: product.category,
        tags: product.tags || [],
        thumbnail: (product.thumbnails && product.thumbnails[0]) || null,
        author: product.userId?.username || 'Unknown',
        purchasedAt: order.createdAt,
      });
    }
  }

  res.status(200).json({ purchases: purchased, total: purchased.length });
});

// ─── Browse ───────────────────────────────────────────────────────────────────

/**
 * GET /api/addon/products
 * Protected by `protectAddon` middleware.
 * Browse/search published marketplace products.
 *
 * Query params:
 *   search   - text search on title/tags
 *   category - filter by category slug
 *   page     - page number (default: 1)
 *   limit    - results per page (default: 20, max: 50)
 */
const browseProducts = asyncHandler(async (req, res) => {
  const page = Math.max(1, parseInt(req.query.page) || 1);
  const limit = Math.min(50, Math.max(1, parseInt(req.query.limit) || 20));
  const skip = (page - 1) * limit;

  const query = { status: 'published', isActive: true };

  if (req.query.category) {
    query.category = req.query.category;
  }

  if (req.query.search) {
    const escaped = req.query.search.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    query.$or = [
      { title: { $regex: escaped, $options: 'i' } },
      { tags: { $regex: escaped, $options: 'i' } },
    ];
  }

  const [products, total] = await Promise.all([
    Product.find(query)
      .populate('userId', 'username profileImage')
      .select('title shortDescription price pricingType currency category tags thumbnails userId createdAt')
      .sort({ createdAt: -1 })
      .skip(skip)
      .limit(limit)
      .lean(),
    Product.countDocuments(query),
  ]);

  const formattedProducts = products.map((p) => ({
    productId: p._id,
    title: p.title,
    shortDescription: p.shortDescription || '',
    price: p.price,
    pricingType: p.pricingType,
    currency: p.currency,
    category: p.category,
    tags: p.tags || [],
    thumbnail: (p.thumbnails && p.thumbnails[0]) || null,
    author: p.userId?.username || 'Unknown',
    createdAt: p.createdAt,
  }));

  res.status(200).json({
    products: formattedProducts,
    total,
    page,
    pages: Math.ceil(total / limit),
  });
});

/**
 * GET /api/addon/products/:id
 * Protected by `protectAddon` middleware.
 * Returns full detail for a single product.
 */
const getProduct = asyncHandler(async (req, res) => {
  const product = await Product.findOne({
    _id: req.params.id,
    status: 'published',
    isActive: true,
  })
    .populate('userId', 'username profileImage')
    .lean();

  if (!product) {
    return res.status(404).json({ message: 'Product not found.' });
  }

  // Check if the requesting user owns this product
  const owned = await Order.exists({
    userId: req.user._id,
    'items.productId': product._id,
    paymentStatus: 'paid',
    status: { $in: ['completed', 'processing'] },
  });

  res.status(200).json({
    productId: product._id,
    title: product.title,
    shortDescription: product.shortDescription || '',
    description: product.description || '',
    price: product.price,
    pricingType: product.pricingType,
    currency: product.currency,
    category: product.category,
    tags: product.tags || [],
    thumbnails: product.thumbnails || [],
    author: product.userId?.username || 'Unknown',
    createdAt: product.createdAt,
    owned: !!owned,
  });
});

// ─── Download ─────────────────────────────────────────────────────────────────

/**
 * POST /api/addon/products/:id/download
 * Protected by `protectAddon` middleware.
 * Verifies the user owns the product, then streams the file directly from disk.
 *
 * Assets are stored on the local server filesystem.
 * The file path is derived from product.shortName (or product._id as fallback).
 *
 * Expected file location on disk (adjust ASSETS_ROOT to match your setup):
 *   {ASSETS_ROOT}/products/{shortName}/download.blend   (or .zip)
 *
 * Set ASSETS_ROOT in your .env:
 *   ASSETS_ROOT=/path/to/your/assets/folder
 */
const getDownloadUrl = asyncHandler(async (req, res) => {
  const path = require('path');
  const fs = require('fs');
  const productId = req.params.id;
  const userId = req.user._id;

  // Verify ownership
  const order = await Order.findOne({
    userId,
    'items.productId': productId,
    paymentStatus: 'paid',
    status: { $in: ['completed', 'processing'] },
  }).lean();

  if (!order) {
    return res.status(403).json({ message: 'You do not own this product.' });
  }

  const product = await Product.findById(productId).lean();

  if (!product || product.status !== 'published') {
    return res.status(404).json({ message: 'Product not found.' });
  }

  // Resolve file path on the local server
  const assetsRoot = process.env.ASSETS_ROOT || path.join(__dirname, '../../assets');
  const productFolder = product.shortName || String(product._id);

  // Try .blend first, then .zip — adjust priority to match how your files are stored
  let filePath = path.join(assetsRoot, 'products', productFolder, 'download.blend');
  let filename = `${productFolder}.blend`;

  if (!fs.existsSync(filePath)) {
    filePath = path.join(assetsRoot, 'products', productFolder, 'download.zip');
    filename = `${productFolder}.zip`;
  }

  // Security: ensure resolved path stays within assetsRoot (prevent path traversal)
  const resolvedPath = path.resolve(filePath);
  const resolvedRoot = path.resolve(assetsRoot);
  if (!resolvedPath.startsWith(resolvedRoot)) {
    return res.status(400).json({ message: 'Invalid product path.' });
  }

  if (!fs.existsSync(resolvedPath)) {
    return res.status(503).json({ message: 'Download file not yet available for this product.' });
  }

  const stat = fs.statSync(resolvedPath);

  // Stream the file directly — the Blender addon will download it via HTTP
  res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
  res.setHeader('Content-Type', 'application/octet-stream');
  res.setHeader('Content-Length', stat.size);

  const readStream = fs.createReadStream(resolvedPath);
  readStream.pipe(res);
});

module.exports = {
  issueDeviceToken,
  revokeDeviceToken,
  getMe,
  getPurchases,
  browseProducts,
  getProduct,
  getDownloadUrl,
};
```

---

### 4. `backend/routes/addonRoutes.js`

```javascript
const express = require('express');
const router = express.Router();
const { protect } = require('../middleware/authMiddleware');
const { protectAddon } = require('../middleware/addonAuthMiddleware');
const {
  issueDeviceToken,
  revokeDeviceToken,
  getMe,
  getPurchases,
  browseProducts,
  getProduct,
  getDownloadUrl,
} = require('../controllers/addonController');

// ── Auth ──────────────────────────────────────────────────────────────────────
// Uses standard JWT protect — call immediately after browser OAuth delivers JWT
router.post('/auth/device-token', protect, issueDeviceToken);

// Uses addon device token for all routes below
router.delete('/auth/device-token', protectAddon, revokeDeviceToken);
router.get('/auth/me', protectAddon, getMe);

// ── Purchases ─────────────────────────────────────────────────────────────────
router.get('/purchases', protectAddon, getPurchases);

// ── Browse ────────────────────────────────────────────────────────────────────
router.get('/products', protectAddon, browseProducts);
router.get('/products/:id', protectAddon, getProduct);

// ── Download ──────────────────────────────────────────────────────────────────
// GET streams the file directly from disk — no pre-signed URL needed
router.get('/products/:id/download', protectAddon, getDownloadUrl);

module.exports = router;
```

---

### 5. Frontend: Addon Login Page

Create a dedicated page at the route `/addon-login` in your frontend (React/Next.js/etc.).

**Behavior:**
1. Read `state` and `port` from the URL query string
2. Validate `port` is in range `49152–65535` (refuse anything outside this range)
3. If the user is **already logged in** (valid session cookie/token): immediately redirect to the callback URL (see below)
4. If the user is **not logged in**: show the standard login form. On successful login, redirect to the callback URL
5. Never show this page in the main navigation — it's only for the addon flow

**Callback redirect URL** (constructed server-side after login succeeds):
```
http://localhost:{port}/callback?token={JWT}&state={state}
```

**Security rules for this page:**
- `port` must be a valid integer in range `49152–65535`. Reject anything outside this range with a 400 error page.
- `state` is treated as opaque — just pass it through unchanged.
- The redirect target is always `http://localhost:{port}/callback` — never any other host.
- The JWT in the redirect URL is the same short-lived 24-hour JWT issued by the standard login flow.
- Add this note in your CSP/CORS config: the redirect to `localhost` is intentional and is how desktop OAuth works (RFC 8252).

**Example minimal React page:**
```jsx
// pages/addon-login.jsx  (or equivalent in your frontend framework)
import { useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../hooks/useAuth'; // your existing auth hook

export default function AddonLoginPage() {
  const router = useRouter();
  const { state, port } = router.query;
  const { user, token } = useAuth();

  // Validate port
  const portNum = parseInt(port, 10);
  const portValid = portNum >= 49152 && portNum <= 65535;

  useEffect(() => {
    if (!portValid || !state) return;
    if (user && token) {
      // Already logged in — redirect immediately
      window.location.href = `http://localhost:${portNum}/callback?token=${token}&state=${state}`;
    }
  }, [user, token, portValid]);

  if (!portValid || !state) {
    return <div>Invalid addon login request.</div>;
  }

  if (user) {
    return <div>Redirecting back to Blender...</div>;
  }

  // Render your existing login form here.
  // After successful login, redirect to:
  //   http://localhost:{portNum}/callback?token={newJWT}&state={state}
  return <YourExistingLoginForm onSuccess={(jwt) => {
    window.location.href = `http://localhost:${portNum}/callback?token=${jwt}&state=${state}`;
  }} />;
}
```

---

## Files to Modify

### `backend/routes/index.js`

Add the addon routes. Insert after the `gpuRoutes` line:

```javascript
// Add this require at the top of the function body with the others:
const addonRoutes = require('./addonRoutes');

// Add this mount line after  app.use('/api/gpu', gpuRoutes):
app.use('/api/addon', addonRoutes);
```

**Full updated `mountRoutes` function excerpt:**
```javascript
  const addonRoutes = require('./addonRoutes');   // ADD THIS LINE
  // ... existing requires ...

  app.use('/api/gpu', gpuRoutes);
  app.use('/api/addon', addonRoutes);             // ADD THIS LINE
```

---

## File Storage — Local Server

Since assets are stored on the local server filesystem, the download endpoint streams files directly.

**Required `.env` variable:**
```
ASSETS_ROOT=/path/to/your/assets/folder
```

**Expected folder structure on disk:**
```
{ASSETS_ROOT}/
└── products/
    └── {product.shortName}/
        └── download.blend   (or download.zip)
```

The controller tries `.blend` first, then falls back to `.zip`. Adjust the order in `getDownloadUrl` if your files are stored differently.

No changes to `Product.js` are required for downloads — the file path is derived from `product.shortName` which already exists.

---

## API Reference for the Blender Addon

Once deployed, the addon will call these endpoints in order:

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `POST` | `/api/addon/auth/device-token` | Bearer JWT | Exchange browser-login JWT for 30-day device token |
| `GET` | `/api/addon/auth/me` | X-Addon-Token | Verify token on startup, get user info |
| `DELETE` | `/api/addon/auth/device-token` | X-Addon-Token | Logout / revoke token |
| `GET` | `/api/addon/purchases` | X-Addon-Token | List purchased products |
| `GET` | `/api/addon/products` | X-Addon-Token | Browse marketplace (`?search=&category=&page=&limit=`) |
| `GET` | `/api/addon/products/:id` | X-Addon-Token | Single product detail |
| `GET` | `/api/addon/products/:id/download` | X-Addon-Token | Stream download file for owned product |

**Headers the addon sends on every protected request:**
```
X-Addon-Token: <30-day device token>
Content-Type: application/json
```

**Error responses the addon handles:**
```json
{ "message": "Addon device token has expired. Please log in again." }  // 401
{ "message": "Addon device token has been revoked. Please log in again." }  // 401
{ "message": "You do not own this product." }  // 403
```

---

## Optional: Token Cleanup Cron Job

Add a scheduled job to purge expired/revoked addon devices. Add to your existing cron setup:

```javascript
// Clean up expired or revoked AddonDevice records older than 7 days
const AddonDevice = require('../models/AddonDevice');

const cleanupAddonDevices = async () => {
  const cutoff = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
  await AddonDevice.deleteMany({
    $or: [
      { expiresAt: { $lt: cutoff } },
      { revokedAt: { $lt: cutoff } },
    ],
  });
};

// Run daily — add to wherever your other cron jobs are registered
setInterval(cleanupAddonDevices, 24 * 60 * 60 * 1000);
```

---

## Security Notes

- Device tokens are stored as SHA256 hashes only — the raw token is returned once and never stored
- All addon endpoints require device token auth except `POST /api/addon/auth/device-token` (which requires a short-lived JWT instead)
- The `/addon-login` frontend page must validate that `port` is in range 49152–65535 and that the redirect host is always `localhost` — never an external domain
- `X-Addon-Token` header name is distinct from `X-Device-Token` (GPU nodes) — no collision
- The `tokenHash` field on `AddonDevice` has `select: false` — it is never returned in API responses
- Download streams directly from disk — no S3 or signed URLs needed since assets live on the local server
- Path traversal is prevented by resolving and comparing against `ASSETS_ROOT` before serving any file

---

## Testing Checklist

- [ ] `POST /api/addon/auth/device-token` with valid JWT → returns `deviceToken` and `expiresAt`
- [ ] `POST /api/addon/auth/device-token` with invalid/expired JWT → 401
- [ ] `GET /api/addon/auth/me` with valid device token → returns user object
- [ ] `GET /api/addon/auth/me` with expired token → 401 with `"Token has expired"` message
- [ ] `GET /api/addon/auth/me` with revoked token → 401 with `"Token has been revoked"` message
- [ ] `DELETE /api/addon/auth/device-token` → 200, subsequent requests with same token → 401
- [ ] `GET /api/addon/purchases` → returns only products from paid+completed orders
- [ ] `GET /api/addon/products?search=wood` → returns matching published products
- [ ] `GET /api/addon/products?category=materials` → returns filtered results
- [ ] `GET /api/addon/products/:id` for owned product → `owned: true`
- [ ] `GET /api/addon/products/:id` for unowned product → `owned: false`
- [ ] `POST /api/addon/products/:id/download` for owned product → returns download URL
- [ ] `POST /api/addon/products/:id/download` for unowned product → 403
