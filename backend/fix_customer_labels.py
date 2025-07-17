import os

# 标签文件夹
label_dir = r".\customerLabel"

for filename in os.listdir(label_dir):
    if filename.endswith('.txt'):
        file_path = os.path.join(label_dir, filename)
        new_lines = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) > 0:
                    if parts[0] == '0':
                        parts[0] = '2'
                    elif parts[0] == '1':
                        parts[0] = '3'
                new_lines.append(' '.join(parts) + '\n')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

print("类别编号批量修改完成！")
