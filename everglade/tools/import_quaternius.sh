#!/bin/sh
# Re-imports the Quaternius Stylized Nature MegaKit (CC0) foliage used by
# Everglade. MEGAKIT points at the pack's glTF folder.
set -e
MEGAKIT=${MEGAKIT:-../tilakpatell/tilakverse-assets/quaternius/stylized-nature-megakit/glTF}
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
