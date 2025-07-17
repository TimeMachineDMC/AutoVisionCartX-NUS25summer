import os
import glob

def fix_label_folder(label_dir):
    for txtfile in glob.glob(os.path.join(label_dir, '*.txt')):
        lines = []
        with open(txtfile, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip() == '':
                    continue
                parts = line.strip().split()
                if parts[0] != '0':
                    parts[0] = '0'
                lines.append(' '.join(parts))
        with open(txtfile, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    print(f'已修正：{label_dir}')

folders = [
    r'.\dataset\labels\train',
    r'.\dataset\labels\val'
]

for folder in folders:
    fix_label_folder(folder)
print('全部修正完成，可以重新训练了！')
