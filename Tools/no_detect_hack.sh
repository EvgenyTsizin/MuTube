#!/bin/bash
find . -type d | while read -r dir; do
  if [[ -f "$dir/image_links.json" && ! -f "$dir/image_links_hands_sorted.json" ]]; then
    cp "$dir/image_links.json" "$dir/image_links_hands_sorted.json"
    echo "Copied image_links.json to image_links_hands_sorted.json in $dir"
  fi
done

