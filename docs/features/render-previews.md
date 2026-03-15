# Rendering Previews

Bulls Asset Manager lets you render high-quality thumbnails for your assets directly inside Blender using a dedicated preview scene.

---

## How It Works

The addon uses a pre-configured render scene (`PreviewRenderScene`) loaded from a bundled `.blend` template. This scene contains a camera, lights, backdrop plane, floor, and preset render objects (shaderball, cube, plane, cylinder, etc.).

Each asset type is rendered using a different strategy:

| Asset Type | How it renders |
|---|---|
| **Object** | Duplicated, scaled to fit, camera aligned |
| **Collection** | Instanced, scaled to fit, camera aligned |
| **Material** | Applied to a preset object (shaderball, cube, etc.) |
| **Material Node Group** | A test material is built and applied automatically |
| **Geometry Node Group** | Applied via modifier to a test object |

---

## Step by Step

### 1. Select your assets
Select the objects, materials, or node groups you want to render previews for in the 3D Viewport or Outliner.

### 2. Adjust the camera (optional)
Click **Adjust Preview Camera** in the Asset Manager panel. This enters a local view where you can position the camera manually. Click the button again to exit.

### 3. Choose a light setup and HDRI
In the **Render Settings** tab, pick a light setup and HDRI environment that suits your asset.

### 4. Render
Click **Render Previews**. The addon will loop through each selected asset, render it, and assign the result as the asset's thumbnail automatically.

---

## Tips

- Use **Set Pivot to Bottom** before rendering objects that should sit on the floor
- The **Preview Rotation** sliders let you rotate the asset during render without moving it in your scene
- Enable **Transparent Background** for assets you want to display on colored backgrounds

---

## Next Step

[Light Setups & HDRIs →](light-setups.md)
