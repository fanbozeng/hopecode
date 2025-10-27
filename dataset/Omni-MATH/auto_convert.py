""" CSV  JSONL"""
import csv
import json
from pathlib import Path

def csv_to_jsonl(csv_path):
    """ CSV  JSONL"""
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
    
    #  JSONL
    output_file = csv_file.with_suffix('.jsonl')
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f" {csv_file.name:25s}  {output_file.name:25s} ({len(data):5d} )")
    return len(data)

def main():
    print("\n" + "="*80)
    print("Omni-MATH CSV  JSONL ")
    print("="*80 + "\n")
    
    archive_dir = Path("archive")
    csv_files = sorted(archive_dir.glob("*.csv"))
    
    if not csv_files:
        print("  CSV ")
        return
    
    total = 0
    for csv_file in csv_files:
        count = csv_to_jsonl(csv_file)
        total += count
    
    print("\n" + "="*80)
    print(f"  {total:,} ")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()

