import xml.etree.ElementTree as ET
from collections import defaultdict

def parse_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Extract all timer definitions
    timer_defs = {}
    for ip in root.findall(".//IP"):
        if ip.get('Name').startswith('TIM'):
            instance = ip.get('InstanceName')
            if instance.startswith('TIM'):
                timer_defs[instance] = {
                    'name': instance,
                    'power_domain': ip.get('PowerDomain')
                }

    # Extract all pin configurations for timers
    timer_pins = defaultdict(list)
    for pin in root.findall(".//Pin"):
        pin_name = pin.get('Name')
        for signal in pin.findall('Signal'):
            signal_name = signal.get('Name', '')
            if signal_name.startswith('TIM'):
                # Parse timer signal (e.g., "TIM1_CH1" -> timer="TIM1", channel="CH1")
                parts = signal_name.split('_')
                if len(parts) != 2:
                    continue

                timer_name, channel = parts
                if not channel.startswith('CH'):
                    continue

                timer_pins[timer_name].append({
                    'pin': pin_name,
                    'signal': signal_name,
                    'channel': channel
                })

    return timer_defs, timer_pins

def generate_timer_definitions(timer_defs):
    # Map power domains to RCC macros
    power_domain_to_rcc = {
        'D1': 'RCC_APB2',
        'D2': {
            'TIM1': 'RCC_APB2',
            'TIM8': 'RCC_APB2',
            'TIM15': 'RCC_APB2',
            'TIM16': 'RCC_APB2',
            'TIM17': 'RCC_APB2',
            'TIM2': 'RCC_APB1L',
            'TIM3': 'RCC_APB1L',
            'TIM4': 'RCC_APB1L',
            'TIM5': 'RCC_APB1L',
            'TIM6': 'RCC_APB1L',
            'TIM7': 'RCC_APB1L',
            'TIM12': 'RCC_APB1L',
            'TIM13': 'RCC_APB1L',
            'TIM14': 'RCC_APB1L',
        }
    }

    # Generate timer definitions
    definitions = []
    for timer_name, info in sorted(timer_defs.items()):
        if not timer_name.startswith('TIM'):
            continue

        rcc_domain = power_domain_to_rcc['D2'].get(timer_name, 'RCC_APB1L')

        # Map IRQ names based on timer
        if timer_name in ['TIM1', 'TIM8']:
            irq = f"{timer_name}_CC_IRQn"
        elif timer_name == 'TIM6':
            irq = "TIM6_DAC_IRQn"
        elif timer_name == 'TIM12':
            irq = "TIM8_BRK_TIM12_IRQn"
        elif timer_name == 'TIM13':
            irq = "TIM8_UP_TIM13_IRQn"
        elif timer_name == 'TIM14':
            irq = "TIM8_TRG_COM_TIM14_IRQn"
        else:
            irq = f"{timer_name}_IRQn"

        definition = f"    {{ .TIMx = {timer_name}, .rcc = {rcc_domain}({timer_name}), .inputIrq = {irq}}}"
        definitions.append(definition)

    return definitions

def generate_timer_hardware(timer_pins):
    hardware_defs = []

    for timer_name, pins in sorted(timer_pins.items()):
        for pin_info in sorted(pins, key=lambda x: (x['pin'], x['channel'])):
            # Parse channel number and type
            channel = pin_info['channel']
            if 'N' in channel:  # Complementary channel
                ch_num = channel.replace('CHN', '')
                ch_type = 'CH1N'  # Assuming all complementary channels are type 1
            else:
                ch_num = channel.replace('CH', '')
                ch_type = f'CH{ch_num}'

            # Format pin name without any parentheses text
            pin_name = pin_info['pin'].split('(')[0].strip()

            # Generate the DEF_TIM macro
            definition = f"    DEF_TIM({timer_name}, {ch_type}, {pin_name}, 0, 0, 0)"
            hardware_defs.append(definition)

    return hardware_defs

def generate_output_file(timer_defs, hardware_defs):
    output = """/*
 * This file is part of Cleanflight and Betaflight.
 *
 * Cleanflight and Betaflight are free software. You can redistribute
 * this software and/or modify this software under the terms of the
 * GNU General Public License as published by the Free Software
 * Foundation, either version 3 of the License, or (at your option)
 * any later version.
 *
 * Cleanflight and Betaflight are distributed in the hope that they
 * will be useful, but WITHOUT ANY WARRANTY; without even the implied
 * warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this software.
 *
 * If not, see <http://www.gnu.org/licenses/>.
 */

#include "platform.h"

#ifdef USE_TIMER

#include "common/utils.h"
#include "drivers/dma.h"
#include "drivers/io.h"
#include "timer_def.h"
#include "stm32h7xx.h"
#include "drivers/rcc.h"
#include "drivers/timer.h"

const timerDef_t timerDefinitions[HARDWARE_TIMER_DEFINITION_COUNT] = {
%s
};

#if defined(USE_TIMER_MGMT)
const timerHardware_t fullTimerHardware[FULL_TIMER_CHANNEL_COUNT] = {
%s
};
#endif

#endif
""" % (',\n'.join(timer_defs), ',\n'.join(hardware_defs))

    return output

def main():
    # Parse XML and generate definitions
    timer_defs, timer_pins = parse_xml('STM32H743IIKx.xml')
    timer_definitions = generate_timer_definitions(timer_defs)
    hardware_definitions = generate_timer_hardware(timer_pins)

    # Generate and write output file
    output = generate_output_file(timer_definitions, hardware_definitions)
    with open('timer_stm32h7xx.c', 'w') as f:
        f.write(output)

if __name__ == '__main__':
    main()
