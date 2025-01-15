#!/bin/bash

mkdir -p output

# Find XML files for specific MCU families
find STM32_open_pin_data/mcu -name "STM32*.xml" | while read xml; do
    # Extract the MCU family from filename (F4, F7, H7, G4)
    family=$(echo $xml | grep -oP 'STM32[FHKG][4-7]' | cut -c6-7)

    # Check if this is one of our target families
    case $family in
        F4|F7|H7|G4)
            echo "Processing $(basename $xml)..."
            python3 generate.py "$xml"
            # Move any generated timer_*.c files to output directory
            find . -maxdepth 1 -name "timer_*.c" -exec mv {} output/ \;
            ;;
    esac
done

echo "Done! Generated files are in output/"
