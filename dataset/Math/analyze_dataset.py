"""MATH """
import json
from collections import Counter, defaultdict

def load_data(file_path):
    """ JSON """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_dataset(data, split_name):
    """"""
    print(f"\n{'='*80}")
    print(f"{split_name.upper()} ")
    print(f"{'='*80}")
    
    # 
    total = len(data)
    print(f"\n:")
    print(f"  : {total}")
    
    # 
    subjects = Counter(item['subject'] for item in data)
    print(f"\n:")
    for subject, count in sorted(subjects.items(), key=lambda x: -x[1]):
        percentage = count / total * 100
        print(f"  {subject:25s}: {count:4d} ({percentage:5.2f}%)")
    
    # 
    levels = Counter(int(item['level']) for item in data)
    print(f"\n:")
    for level in sorted(levels.keys()):
        count = levels[level]
        percentage = count / total * 100
        stars = '*' * level
        print(f"  Level {level} {stars:10s}: {count:4d} ({percentage:5.2f}%)")
    
    # +
    subject_level = defaultdict(lambda: defaultdict(int))
    for item in data:
        subject_level[item['subject']][int(item['level'])] += 1
    
    print(f"\n×:")
    print(f"  {'':<25s} | L1   | L2   | L3   | L4   | L5   | ")
    print(f"  {'-'*25} | {'-'*5}| {'-'*5}| {'-'*5}| {'-'*5}| {'-'*5}| {'-'*5}")
    for subject in sorted(subjects.keys()):
        counts = [subject_level[subject][i] for i in range(1, 6)]
        total_subj = sum(counts)
        row = f"  {subject:<25s} |"
        for c in counts:
            row += f" {c:4d}|"
        row += f" {total_subj:4d}"
        print(row)
    
    # 
    problem_lens = [len(item['problem']) for item in data]
    solution_lens = [len(item['solution']) for item in data]
    answer_lens = [len(item['answer']) for item in data]
    
    print(f"\n ():")
    print(f"  {'':15s} |  |  |  | ")
    print(f"  {'-'*15} | {'-'*6} | {'-'*6} | {'-'*6} | {'-'*6}")
    
    def stats(lens, name):
        sorted_lens = sorted(lens)
        median = sorted_lens[len(sorted_lens)//2]
        return f"  {name:15s} | {min(lens):6d} | {max(lens):6d} | {sum(lens)//len(lens):6d} | {median:6d}"
    
    print(stats(problem_lens, " (problem)"))
    print(stats(solution_lens, " (solution)"))
    print(stats(answer_lens, " (answer)"))
    
    # 
    print(f"\n:")
    pure_number = sum(1 for item in data if item['answer'].replace('.', '').replace('-', '').replace(',', '').isdigit())
    has_frac = sum(1 for item in data if '\\frac' in item['answer'])
    has_sqrt = sum(1 for item in data if '\\sqrt' in item['answer'])
    has_pi = sum(1 for item in data if '\\pi' in item['answer'])
    has_text = sum(1 for item in data if '\\text' in item['answer'])
    
    print(f"  : {pure_number} ({pure_number/total*100:.1f}%)")
    print(f"   (\\frac): {has_frac} ({has_frac/total*100:.1f}%)")
    print(f"   (\\sqrt): {has_sqrt} ({has_sqrt/total*100:.1f}%)")
    print(f"   π (\\pi): {has_pi} ({has_pi/total*100:.1f}%)")
    print(f"   (\\text): {has_text} ({has_text/total*100:.1f}%)")
    
    return subjects, levels

def show_samples(data, split_name, n=3):
    """"""
    print(f"\n{'='*80}")
    print(f"{split_name.upper()}  ( {n} )")
    print(f"{'='*80}")
    
    for i in range(min(n, len(data))):
        item = data[i]
        print(f"\n {i+1}")
        print(f"ID: {item['unique_id']}")
        print(f": {item['subject']}")
        print(f": Level {item['level']}")
        print(f"\n (Problem):")
        print(f"{item['problem'][:200]}..." if len(item['problem']) > 200 else item['problem'])
        print(f"\n (Answer): {item['answer']}")
        print(f"\n (Solution):")
        print(f"{item['solution'][:300]}..." if len(item['solution']) > 300 else item['solution'])
        print(f"\n{'-'*80}")

def compare_splits(train_data, test_data):
    """"""
    print(f"\n{'='*80}")
    print(" vs  ")
    print(f"{'='*80}")
    
    train_subjects = Counter(item['subject'] for item in train_data)
    test_subjects = Counter(item['subject'] for item in test_data)
    
    print(f"\n:")
    print(f"  {'':<25s} |  |  | ")
    print(f"  {'-'*25} | {'-'*6} | {'-'*6} | {'-'*8}")
    
    all_subjects = sorted(set(train_subjects.keys()) | set(test_subjects.keys()))
    for subject in all_subjects:
        train_count = train_subjects.get(subject, 0)
        test_count = test_subjects.get(subject, 0)
        ratio = f"{train_count}/{test_count}" if test_count > 0 else "N/A"
        print(f"  {subject:<25s} | {train_count:6d} | {test_count:6d} | {ratio:>8s}")

def main():
    # 
    print("...")
    train_data = load_data("train-00000-of-00001.parquet.json")
    test_data = load_data("test-00000-of-00001.parquet.json")
    print("")
    
    # 
    train_subjects, train_levels = analyze_dataset(train_data, "train")
    
    # 
    test_subjects, test_levels = analyze_dataset(test_data, "test")
    
    # 
    compare_splits(train_data, test_data)
    
    # 
    show_samples(train_data, "train", n=2)
    show_samples(test_data, "test", n=2)
    
    print(f"\n{'='*80}")
    print("")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()