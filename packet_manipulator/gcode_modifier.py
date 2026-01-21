"""
gcode_modifier.py - G-Code Modification Logic
Author: luke pepin
Description: Provides functions to analyze and modify G-Code payloads for attack scenarios.
"""

def modify_y_axis(gcode_line, delta):
    """
    Modifies the Y-axis value in a G-Code line by a given delta.
    Returns the modified G-Code line.
    """
    import re
    match = re.search(r'Y([-+]?[0-9]*\.?[0-9]+)', gcode_line)
    if match:
        original_y = float(match.group(1))
        new_y = original_y + delta
        modified_line = re.sub(r'Y([-+]?[0-9]*\.?[0-9]+)', f'Y{new_y:.3f}', gcode_line)
        return modified_line
    return gcode_line

# Example usage:
# line = "G01 X10.0 Y20.0 Z-1.0 F1000"
# print(modify_y_axis(line, 5.0))
