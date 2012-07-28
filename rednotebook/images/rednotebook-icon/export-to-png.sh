#! /bin/bash

set -e

SVG=rednotebook.svg

for SIZE in 22 32 48 64 128 192 256; do
    inkscape -e rn-"$SIZE".png --export-width=$SIZE --export-height=$SIZE "$SVG"
done
