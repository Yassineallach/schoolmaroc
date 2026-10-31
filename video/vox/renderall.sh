#!/bin/bash
cd "$(dirname "$0")"
V=/home/user/schoolmaroc/video
render() {
  case $1 in
    1) python3 -I act1_vox.py video $V/Act1_The_Mines.mp4 ;;
    2) python3 -I act2_vox.py video $V/Act2_The_Author.mp4 ;;
    3) python3 -I act3_vox.py video $V/Act3_A_World_Ruled_by_Color.mp4 ;;
    4) python3 -I act4_vox.py video $V/Act4_Eo_and_the_Lie.mp4 ;;
    5) python3 -I act5_vox.py video $V/Act5_The_Institute.mp4 ;;
    6) python3 -I act6_vox.py video $V/Act6_Rome_and_the_Cost.mp4 ;;
    7) python3 -I act7_vox.py video $V/Act7_Allies_and_Enemies.mp4 ;;
    8) python3 -I act8_vox.py video $V/Act8_Legacy.mp4 ;;
  esac > log_act$1.txt 2>&1
  echo "act $1: $(tail -n1 log_act$1.txt)"
}
export -f render; export V
printf '%s\n' 8 7 1 6 5 4 2 3 | xargs -P 4 -I{} bash -c 'render {}'
echo ALL_DONE
