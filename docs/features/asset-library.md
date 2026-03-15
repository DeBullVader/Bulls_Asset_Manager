# Asset Library

Bulls Asset Manager integrates with Blender's native **Asset Browser**, making it easy to build and organize a personal or studio asset library.

---

## Setting Up a Library

1. Go to **Edit → Preferences → Add-ons → Bulls Asset Manager**
2. Set the **Library Path** to a folder on your drive
3. The addon registers this folder as a Blender Asset Library automatically
4. Your assets will appear in Blender's Asset Browser under that library name

---

## Marking Assets

To add an asset to your library:

1. Select the object, collection, material, or node group
2. In the **Asset Manager panel → Operators tab**, click **Mark as Asset**
3. Fill in the metadata dialog:
   - **Author** — defaults to your preferences setting
   - **Description** — short description of the asset
   - **Tags** — comma-separated tags for filtering

The asset is now visible in the Asset Browser.

---

## Supported Asset Types

| Type | Notes |
|---|---|
| Objects | Mesh, armature, curve, and more |
| Collections | Groups of objects |
| Materials | PBR materials and shader setups |
| Material Node Groups | Reusable shader node groups |
| Geometry Node Groups | Procedural geometry setups |

---

## Unmarking Assets

Select the asset and click **Unmark Asset** in the Operators tab to remove it from the library without deleting the object.

---

## Next Step

[PolyAssetVault Marketplace →](../marketplace/overview.md)
