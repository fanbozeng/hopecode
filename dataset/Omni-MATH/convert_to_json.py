""" Omni-MATH CSV  JSON/JSONL """
import csv
import json
from pathlib import Path

def csv_to_json(csv_path, output_format='jsonl'):
    """
     CSV  JSON  JSONL
    
    Args:
        csv_path: CSV 
        output_format: 'json'  'jsonl'
    """
    csv_file = Path(csv_path)
    
    #  CSV
    data = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'question': row['question'],
                'answer': row['answer']
            })
    
    print(f"  {csv_file.name}: {len(data)} ")
    
    # 
    if output_format == 'jsonl':
        output_file = csv_file.with_suffix('.jsonl')
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
    else:  # json
        output_file = csv_file.with_suffix('.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f" : {output_file}")
    return len(data)

def main():
    print("="*80)
    print("Omni-MATH CSV  JSON ")
    print("="*80)
    
    archive_dir = Path("archive")
    
    #  CSV 
    csv_files = list(archive_dir.glob("*.csv"))
    
    if not csv_files:
        print("  CSV ")
        return
    
    print(f"\n {len(csv_files)}  CSV :")
    for f in csv_files:
        print(f"  - {f.name}")
    
    # 
    print(f"\n:")
    print(f"  1. JSONL ( JSON )")
    print(f"  2. JSON ( JSON )")
    
    choice = input("\n (1  2 1): ").strip()
    output_format = 'json' if choice == '2' else 'jsonl'
    
    print(f"\n {output_format.upper()} ...\n")
    
    total = 0
    for csv_file in csv_files:
        count = csv_to_json(csv_file, output_format)
        total += count
    
    print(f"\n{'='*80}")
    print(f"  {total} ")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()

