import xml.etree.ElementTree as ET
from collections import defaultdict
import os

def parse_timer_pins(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Define namespace
    ns = {'ns': 'http://dummy.com'}

    # Collect all timer pins
    timer_pins = []
    for pin in root.findall('.//ns:Pin', ns):
        pin_name = pin.get('Name', '').split('(')[0].strip()  # Remove anything in parentheses
        for signal in pin.findall('ns:Signal', ns):
            signal_name = signal.get('Name', '')
            if signal_name.startswith('TIM'):
                # Parse timer signal (e.g., "TIM1_CH1" -> timer="TIM1", channel="CH1")
                parts = signal_name.split('_')
                if len(parts) == 2:
                    timer_name, channel = parts
                    if channel.startswith('CH'):
                        timer_pins.append({
                            'pin': pin_name,
                            'timer': timer_name,
                            'channel': channel
                        })

    # Sort by timer number, then pin name
    return sorted(timer_pins, key=lambda x: (int(x['timer'].replace('TIM','')), x['pin']))

def generate_output_file(timer_pins):
    output = "// Auto-generated timer definitions\n\n"
    output += f"#define FULL_TIMER_CHANNEL_COUNT {len(timer_pins)}\n\n"
    output += "const timerHardware_t fullTimerHardware[FULL_TIMER_CHANNEL_COUNT] = {\n"

    # Group by port for cleaner output
    port_groups = defaultdict(list)
    for pin in timer_pins:
        port = pin['pin'][1]  # Get 'A' from 'PA0'
        port_groups[port].append(pin)

    # Generate definitions for each port
    for port in sorted(port_groups.keys()):
        output += f"\n// Port {port}\n"
        for pin in port_groups[port]:
            output += f"    DEF_TIM({pin['timer']}, {pin['channel']}, {pin['pin']}, 0, 0, 0),\n"

    output += "};\n"
    return output

def main():
    try:
        import sys

        # Use command line arg if provided, otherwise use default
        input_file = sys.argv[1] if len(sys.argv) > 1 else 'STM32H743IIKx.xml'
        processor = os.path.splitext(input_file)[0]  # Get filename without extension

        print("Parsing XML file...")
        timer_pins = parse_timer_pins(input_file)
        print(f"Found {len(timer_pins)} timer channel mappings")

        print("Generating output file...")
        output = generate_output_file(timer_pins)

        # Extract MCU name and convert to lowercase
        mcu = processor.lower()
        output_file = f"timer_{mcu}.c"
        print(f"Writing to {output_file}...")
        with open(output_file, 'w') as f:
            f.write(output)

        print("Done!")

    except Exception as e:
        print(f"Error occurred: {str(e)}")

if __name__ == '__main__':
    main()
