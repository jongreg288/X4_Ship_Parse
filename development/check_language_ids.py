"""
Simple language ID checker for X4 files
"""
import xml.etree.ElementTree as ET
from pathlib import Path

def main():
    print("Checking actual language IDs in X4 files...")
    print("=" * 45)

    t_dir = Path('data/t')
    if not t_dir.exists():
        print("No data/t directory found")
        return

    for xml_file in sorted(t_dir.glob('0001-l*.xml')):
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            lang_id = root.get('id')
            
            # Get a sample text to identify language
            sample_text = 'Unknown'
            for page in root.findall('.//page'):
                for text_entry in page.findall('t'):
                    if text_entry.get('id') == '1' and text_entry.text:  # Hull text
                        sample_text = text_entry.text.strip()
                        break
                if sample_text != 'Unknown':
                    break
            
            print(f'{xml_file.name}: ID {lang_id:>3} - Sample: "{sample_text}"')
            
        except Exception as e:
            print(f'{xml_file.name}: Error - {e}')

if __name__ == "__main__":
    main()