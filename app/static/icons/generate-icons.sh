#!/bin/bash

# Script to generate PWA icons from SVG or PNG
# Uses ImageMagick (install: apt-get install imagemagick)

# Create a simple diamond icon using ImageMagick
convert -size 512x512 xc:none \
  -fill "#8B5CF6" \
  -draw "polygon 256,50 450,256 256,462 62,256" \
  -fill "#A78BFA" \
  -draw "polygon 256,50 256,256 450,256" \
  icon-512x512.png

# Generate all required sizes
for size in 72 96 128 144 152 192 384 512; do
  convert icon-512x512.png -resize ${size}x${size} icon-${size}x${size}.png
  echo "Generated icon-${size}x${size}.png"
done

echo "All icons generated!"
