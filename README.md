# MayaTrackGenerator

## Features

### 1. Side Selection
- The side selection offers two options: **Left** or **Right**.
- Each option corresponds to the side element in the namespace.

### 2. Track Shape Curve
- Users need to edit a **NURBS curve** to match the track shape.
- Assign the curve to this slot.

### 3. Track Segment
- Users need to assign the **track segment** to be used.
- The plugin will duplicate and distribute the segments along the curve.

### 4. Vehicle Width
- This value will be divided by 2.
- It is used as the offset value from the track to the world origin.

### 5. Control Mode
- **Wheel CTRL**:
  - The plugin generates **wheel controls**.
  - The track will be globally stretched when the wheels are moved.
- **Track Surface CTRL**:
  - The plugin generates controls on the **track surface**.
  - Users can manually control the global stretch effect of the track surface.

---

### Usage
1. Prepare a **NURBS curve** for the track shape.
2. Assign the **track segment** to the plugin.
3. Configure the **vehicle width** and **control mode** as needed.
4. Apply the plugin to generate the track with controls.
