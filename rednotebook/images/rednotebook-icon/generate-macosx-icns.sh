#! /bin/bash
#
# based on:
# https://stackoverflow.com/questions/9853325/how-to-convert-a-svg-to-a-png-with-imagemagick
inkscape -w 1024 -h 1024 rednotebook.svg -o rn-1024.png
inkscape -w 512 -h 512 rednotebook.svg -o rn-512.png

# based on:
# https://stackoverflow.com/questions/12306223/how-to-manually-create-icns-files-using-iconutil
# https://stackoverflow.com/questions/15192173/os-x-iconutil-reports-invalid-iconset
mkdir rednotebook.iconset
sips -z 16 16     rn-1024.png --out rednotebook.iconset/icon_16x16.png
sips -z 32 32     rn-1024.png --out rednotebook.iconset/icon_16x16@2x.png
sips -z 32 32     rn-1024.png --out rednotebook.iconset/icon_32x32.png
sips -z 64 64     rn-1024.png --out rednotebook.iconset/icon_32x32@2x.png
sips -z 128 128   rn-1024.png --out rednotebook.iconset/icon_128x128.png
sips -z 256 256   rn-1024.png --out rednotebook.iconset/icon_128x128@2x.png
sips -z 256 256   rn-1024.png --out rednotebook.iconset/icon_256x256.png
sips -z 512 512   rn-1024.png --out rednotebook.iconset/icon_256x256@2x.png
sips -z 512 512   rn-1024.png --out rednotebook.iconset/icon_512x512.png
cp rn-1024.png rednotebook.iconset/icon_512x512@2x.png
iconutil -c icns rednotebook.iconset
rm -rf rednotebook.iconset
