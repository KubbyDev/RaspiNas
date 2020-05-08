#!/bin/bash

cd /home/raspinas/nas/storage

# Colorspace problems
shopt -s nocaseglob # Case insensitive
shopt -s nullglob # Doesn't crash when one type has no member
shopt -s extglob # Extended pattern matching (for the @)
find *.@(png|jpg|jpeg) | while read -r file
do 
	convert "$file" -colorspace sRGB -type truecolor "$file"
done

