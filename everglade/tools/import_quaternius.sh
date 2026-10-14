#!/bin/sh
# Re-imports the Quaternius Stylized Nature MegaKit (CC0) foliage used by
# Everglade. MEGAKIT points at the pack's glTF folder.
set -e
MEGAKIT=${MEGAKIT:-../../tilakpatell/tilakverse-assets/quaternius/stylized-nature-megakit/glTF}
BLENDER_PY=${BLENDER_PY:-/tmp/bvenv/bin/python}
$BLENDER_PY tools/import_quaternius.py -- "$MEGAKIT" assets/models \
  CommonTree_5:tree:green:4.4:q_tree_round_a \
  CommonTree_3:tree:deep:5.2:q_tree_round_c \
  TwistedTree_1:tree:green:7.4:q_tree_round_b \
  Birch_2:tree:birch:6.0:q_tree_birch \
  CherryBlossom_1:tree:blossom:5.2:q_tree_blossom \
  TwistedTree_2:tree:gold:6.0:q_tree_golden \
  CommonTree_2:tree:orange:5.0:q_tree_orange \
  CommonTree_4:tree:teal:5.4:q_tree_teal \
  Pine_1:tree:pine:5.6:q_tree_pine_a \
  Pine_5:tree:pine:4.2:q_tree_pine_b \
  GiantPine_2:tree:pine:8.0:q_tree_cedar \
  Bush_Common:tree:green:1.0:q_bush_a \
  Bush_Large:tree:gold:1.2:q_bush_golden \
  Grass_Common_Short:grass:x:0.3:q_grass_short \
  Grass_Common_Tall:grass:x:0.42:q_grass_tall \
  Grass_Wispy_Tall:grass:x:0.42:q_grass_wispy \
  Grass_Wide_Tall:grass:x:0.4:q_grass_wide \
  Grass_Wispy_Tall:grass:x:0.75:q_grass_wild
mkdir -p assets/textures/foliage assets/third_party
for t in Leaves_NormalTree Leaves_Birch Leaves_CherryBlossom Leaves_TwistedTree Leaf_Pine Leaves_GiantPine; do
  cp "$MEGAKIT/$t.png" assets/textures/foliage/
done
cp "$MEGAKIT/../License_Source.txt" assets/third_party/QUATERNIUS_STYLIZED_NATURE_MEGAKIT_LICENSE.txt

# Textured models: Medieval Village MegaKit details/props and Nature MegaKit
# flowers, stones and ground plants (see tools/import_quaternius_tex.py).
VILLAGE=${VILLAGE:-"../../assetsrc/MouthOfGod_System/Assets/ArtisticResources/ThirdParty/Quaternius/Medieval Village MegaKit[Standard]/glTF"}
$BLENDER_PY tools/import_quaternius_tex.py -- "$MEGAKIT" "$VILLAGE" assets/models \
  QM/Door_1_Round:fit=door:q_door \
  QM/Window_Wide_Round1:fit=window_frame:q_window_frame \
  QM/WindowShutters_Wide_Round_Open:fit=shutters:q_shutters \
  QM/Prop_Chimney:fit=chimney:q_chimney \
  QM/Prop_MetalFence_Ornament:fit=fence_ornate:q_fence_ornate:dec=0.25 \
  QM/Prop_WoodenFence_Single:fit=fence_rail:q_fence_rail:part=rails \
  QM/Prop_Wagon:fit=cart:q_cart \
  QM/Prop_Crate:fit=crate:q_crate \
  QN/Flower_1_Group:h=0.5:q_flowers_white \
  QN/Flower_3_Group:h=0.5:q_flowers_pink \
  QN/Flower_2_Group:h=0.45:q_flowers_blue \
  QN/Flower_4_Group:h=0.5:q_flowers_yellow \
  QN/Flower_7_Group:h=0.42:q_flowers_red \
  QN/Bush_Common_Flowers:h=0.9:q_bush_b \
  QN/Bush_Large_Flowers:h=1.15:q_bush_berries \
  QN/Mushroom_RedCap:h=0.2:q_mushrooms \
  QN/Pebble_Round_1:fit=stepping_stone:q_stepping_stone \
  QN/Pebble_Round_2:fit=cobble_a:q_cobble_a \
  QN/Pebble_Round_3:fit=cobble_b:q_cobble_b \
  QN/Fern_1:h=0.6:q_fern \
  QN/Plant_1:h=0.5:q_plant \
  QN/Grass_Wheat:h=0.7:q_wheat
mkdir -p assets/textures/qkit
while read pack tex; do
  if [ "$pack" = QM ]; then cp "$VILLAGE/../Textures/$tex" assets/textures/qkit/; else cp "$MEGAKIT/$tex" assets/textures/qkit/; fi
done < assets/textures/qkit_list.txt
rm assets/textures/qkit_list.txt
# 1024 px is plenty on a phone screen
python3 -c "
import glob
from PIL import Image
for f in glob.glob('assets/textures/qkit/*.png'):
    im = Image.open(f)
    if max(im.size) > 1024:
        im.resize((1024, 1024), Image.LANCZOS).save(f)
"
cp "$VILLAGE/../License_Standard.txt" assets/third_party/QUATERNIUS_MEDIEVAL_VILLAGE_MEGAKIT_LICENSE.txt

# Rounded wall stones (the "Rounded" wall pattern), simplified for phones
$BLENDER_PY tools/import_quaternius_tex.py -- "$MEGAKIT" "$VILLAGE" assets/models \
  QM/Prop_Brick1:h=1.0:q_stone_1:dec=0.3 QM/Prop_Brick2:h=1.0:q_stone_2:dec=0.3 \
  QM/Prop_Brick3:h=1.0:q_stone_3:dec=0.3 QM/Prop_Brick4:h=1.0:q_stone_4:dec=0.3
rm -f assets/textures/qkit_list.txt
