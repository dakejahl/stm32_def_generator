#!/bin/bash

# Create output directory if it doesn't exist
mkdir -p output

# Process each XML file in the mcu directory
for xml in STM32_open_pin_data/mcu/STM32*.xml; do
    # Extract the MCU family from filename (F4, F7, H7, G4)
    family=$(echo $xml | grep -oP 'STM32[FHKG][4-7]' | cut -c6-7)

    # Check if this is one of our target families
    case $family in
        F4|F7|H7|G4)
            echo "Processing $(basename $xml)..."
            python3 generate.py "$xml"
            # Move generated file to output directory
            mv "timer_$(basename ${xml%.*}).c" output/
            ;;
    esac
done

echo "Done! Generated files are in output/"
