# AGRF Manifest Options

Below are extra options you can put in a `gorender` `manifest.md` that will be instead consumed by AGRF, controlling various aspects of rendering behavior.

The current list is AI-generated summary, which is still better than nothing since one sometimes just needs such a list. I will update this list when I have time.

## Sprite Configuration

### `agrf_subset`
- **Type**: Array or special value
- **Description**: Controls which sprites/indices to use from the spritesheet

### `agrf_unnaturalness`
- **Type**: Number
- **Description**: Controls sprite dimension adjustments for non-standard sizes

### `agrf_scale`
- **Type**: Number
- **Description**: Scale factor applied to sprites

### `agrf_scales`
- **Type**: Array of Numbers
- **Description**: List of scale values for sprites

### `agrf_zdiff`
- **Type**: Number
- **Description**: Z-axis offset for sprite positioning

### `agrf_real_x`
- **Type**: Number
- **Description**: Real X dimension (used in road mode calculations)

## Rendering Modes

### `agrf_road_mode`
- **Type**: Boolean
- **Description**: Enable road-specific rendering mode
- **Example**: `"agrf_road_mode": true`

### `agrf_cargo_mode`
- **Type**: Boolean
- **Description**: Enable cargo-specific rendering mode
- **Example**: `"agrf_cargo_mode": true`

## Palette Configuration

### `agrf_palette`
- **Type**: String
- **Description**: Path to palette file for rendering
- **Example**: `"agrf_palette": "path/to/palette.pal"`

## Sprite Positioning and Offsets

### `agrf_deltas`
- **Type**: Array
- **Description**: Delta values for spritesheet positioning

### `agrf_ydeltas`
- **Type**: Array
- **Description**: Y-delta values for spritesheet positioning

### `agrf_offsets`
- **Type**: Array
- **Description**: Offset values for spritesheet positioning

### `agrf_yoffsets`
- **Type**: Array
- **Description**: Y-offset values for spritesheet positioning

### `agrf_bpps`
- **Type**: Array
- **Description**: Bits per pixel values for sprites

### `agrf_bbox_joggle`
- **Type**: Number or Array
- **Description**: Bounding box adjustment

## Child Sprite Configuration

### `agrf_childsprite`
- **Type**: Array or Object
- **Description**: Child sprite configuration for complex objects

### `agrf_relative_childsprite`
- **Type**: Boolean
- **Description**: Use relative positioning for child sprites
- **Example**: `"agrf_relative_childsprite": true`

## Cropping Configuration

### `agrf_manual_crop`
- **Type**: Boolean
- **Description**: Enable manual cropping mode
- **Example**: `"agrf_manual_crop": true`

### `agrf_manual_crop_keep_br_space`
- **Type**: Boolean
- **Description**: Keep bottom-right space when manually cropping
- **Example**: `"agrf_manual_crop_keep_br_space": true`

## Mask Configuration

### `agrf_no_mask`
- **Type**: Boolean
- **Description**: Disable masking for sprites
- **Example**: `"agrf_no_mask": true`
