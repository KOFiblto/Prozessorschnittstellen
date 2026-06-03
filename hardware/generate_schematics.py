import os
import subprocess
import glob
import json
import xml.etree.ElementTree as ET

def postprocess_svg(svg_file, json_file):
    """
    Parses the Yosys JSON netlist to map net names (signals) to their bit IDs.
    Then, modifies the generated SVG file to:
      1. Add <title> tooltip elements on every line/path belonging to a named signal.
      2. Draw clean text labels on the longest segments of named wires.
    """
    if not os.path.exists(json_file) or not os.path.exists(svg_file):
        return

    try:
        with open(json_file) as f:
            netlist = json.load(f)
    except Exception as e:
        print(f"  Warning: Failed to parse JSON netlist: {e}")
        return

    # 1. Map tuple of bits to signal name
    bits_to_name = {}
    modules = netlist.get("modules", {})
    for mod_name, mod_data in modules.items():
        netnames = mod_data.get("netnames", {})
        for net_name, net_info in netnames.items():
            # Filter out auto-generated names (e.g. starting with $, containing auto, or just digits)
            name_parts = net_name.lstrip('\\').split('$')
            base_name = name_parts[0]
            if not base_name or base_name.isdigit() or base_name.startswith('$') or 'auto' in net_name:
                continue
            
            clean_name = net_name.lstrip('\\')
            bits = net_info.get("bits", [])
            bit_tuple = tuple(int(b) for b in bits if isinstance(b, int) or (isinstance(b, str) and b.isdigit()))
            if not bit_tuple:
                continue
            
            # Map the whole bus / signal
            bits_to_name[bit_tuple] = clean_name
            # If it's a multi-bit bus, map individual bits with index subscripts
            if len(bit_tuple) > 1:
                for idx, bit in enumerate(bit_tuple):
                    bits_to_name[(bit,)] = f"{clean_name}[{idx}]"

    # 2. Load SVG
    try:
        # Register namespaces to prevent ElementTree from rewriting prefixes (like s: and xlink:)
        ET.register_namespace("", "http://www.w3.org/2000/svg")
        ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
        ET.register_namespace("s", "https://github.com/nturley/netlistsvg")
        
        tree = ET.parse(svg_file)
        root = tree.getroot()
    except Exception as e:
        print(f"  Warning: Failed to parse SVG file: {e}")
        return

    net_lines = {}
    
    # Iterate through all line and path elements in the SVG
    for elem in root.iter():
        tag = elem.tag.split('}')[-1]
        if tag in ("line", "path"):
            classes = elem.get("class", "").split()
            net_class = None
            for c in classes:
                if c.startswith("net_"):
                    net_class = c
                    break
            
            if net_class:
                try:
                    bits_part = net_class[4:]
                    class_bits = tuple(int(x) for x in bits_part.split(','))
                except ValueError:
                    continue
                
                # Check if this net matches a user-defined signal
                net_name = bits_to_name.get(class_bits)
                if net_name:
                    # Add hover tooltip (<title>)
                    title_elem = ET.Element("{http://www.w3.org/2000/svg}title")
                    title_elem.text = net_name
                    elem.append(title_elem)
                    
                    # If it's a line, record its segment coordinates for text labeling
                    if tag == "line":
                        try:
                            x1 = float(elem.get("x1"))
                            y1 = float(elem.get("y1"))
                            x2 = float(elem.get("x2"))
                            y2 = float(elem.get("y2"))
                            if net_name not in net_lines:
                                net_lines[net_name] = []
                            net_lines[net_name].append((x1, y1, x2, y2))
                        except (TypeError, ValueError):
                            pass

    # 3. Add text labels on the longest wire segment for each signal
    for net_name, lines in net_lines.items():
        best_segment = None
        max_len = 0
        
        # Prefer horizontal segments for cleaner reading
        for x1, y1, x2, y2 in lines:
            if abs(y1 - y2) < 0.1:
                length = abs(x2 - x1)
                if length > max_len:
                    max_len = length
                    best_segment = (x1, y1, x2, y2)
                    
        # Fallback to vertical segments if no horizontal segment exists
        if not best_segment:
            for x1, y1, x2, y2 in lines:
                if abs(x1 - x2) < 0.1:
                    length = abs(y2 - y1)
                    if length > max_len:
                        max_len = length
                        best_segment = (x1, y1, x2, y2)

        # Place label if segment is long enough to avoid layout clutter
        if best_segment and max_len > 25:
            x1, y1, x2, y2 = best_segment
            text_elem = ET.Element("{http://www.w3.org/2000/svg}text")
            text_elem.text = net_name
            
            # Label styling: dark blue/navy, monospace (matching theme), small, bold
            text_elem.set("font-size", "7.5px")
            text_elem.set("fill", "#0033aa")
            text_elem.set("font-family", '"Courier New", monospace')
            text_elem.set("font-weight", "bold")
            
            if abs(y1 - y2) < 0.1: # Horizontal
                x_mid = (x1 + x2) / 2
                y_pos = y1 - 3.5  # Position slightly above the line
                text_elem.set("x", str(x_mid))
                text_elem.set("y", str(y_pos))
                text_elem.set("text-anchor", "middle")
            else: # Vertical
                x_pos = x1 + 3.5  # Position slightly to the right of the line
                y_mid = (y1 + y2) / 2
                text_elem.set("x", str(x_pos))
                text_elem.set("y", str(y_mid))
                text_elem.set("text-anchor", "start")
                
            root.append(text_elem)

    # 4. Save modified SVG
    try:
        tree.write(svg_file, encoding="utf-8", xml_declaration=True)
        print(f"Successfully postprocessed & labeled: {svg_file}")
    except Exception as e:
        print(f"  Warning: Failed to write labeled SVG: {e}")


def main():
    # Setup environment paths for OSS CAD Suite
    oss_root = r"C:\_dev\oss-cad-suite"
    oss_bin = os.path.join(oss_root, "bin")
    oss_lib = os.path.join(oss_root, "lib")
    
    # Prepend to PATH so Yosys and its DLLs can be found
    os.environ["YOSYSHQ_ROOT"] = oss_root
    os.environ["PATH"] = f"{oss_bin};{oss_lib};" + os.environ.get("PATH", "")
    
    # Path to Yosys executable
    yosys_path = os.path.join(oss_bin, "yosys.exe")
    if not os.path.exists(yosys_path):
        print(f"Error: Yosys not found at {yosys_path}")
        return
        
    export_dir = "verilog_export"
    if not os.path.exists(export_dir):
        print(f"Error: Directory {export_dir} does not exist.")
        return
        
    # Get all Verilog files in verilog_export
    v_files = glob.glob(os.path.join(export_dir, "*.v"))
    if not v_files:
        print("No Verilog (.v) files found in verilog_export.")
        return
        
    print(f"Found {len(v_files)} Verilog files. Starting conversion...")
    
    for v_file in v_files:
        base_name = os.path.splitext(os.path.basename(v_file))[0]
        json_file = os.path.join(export_dir, f"{base_name}.json")
        svg_file = os.path.join(export_dir, f"{base_name}.svg")
        
        print(f"\n--- Processing {base_name} ---")
        
        # 1. Run Yosys to generate JSON netlist
        yosys_cmd = [
            yosys_path,
            "-p", f"read_verilog {v_file}; prep; write_json {json_file}"
        ]
        print(f"Running Yosys: {' '.join(yosys_cmd)}")
        try:
            subprocess.run(yosys_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            print(f"Successfully generated netlist: {json_file}")
        except subprocess.CalledProcessError as e:
            print(f"Error running Yosys for {base_name}: {e.stderr.decode().strip()}")
            continue
            
        # 2. Run netlistsvg to generate SVG schematic
        npx_cmd = ["npx.cmd", "-y", "netlistsvg", json_file, "-o", svg_file]
        print(f"Running netlistsvg: {' '.join(npx_cmd)}")
        try:
            subprocess.run(npx_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Successfully generated schematic: {svg_file}")
        except subprocess.CalledProcessError as e:
            print(f"Error running netlistsvg for {base_name}: {e.stderr.decode().strip()}")
            continue
            
        # 3. Postprocess SVG to add wire names & tooltips
        postprocess_svg(svg_file, json_file)
            
        # 4. Clean up the temporary JSON file
        if os.path.exists(json_file):
            os.remove(json_file)
            
    print("\nConversion finished! You can view the SVG files in a browser or vector image viewer.")

if __name__ == "__main__":
    main()
