import os

label_folder = r".\labelbook"

for filename in os.listdir(label_folder):
    if filename.endswith('.txt'):
        file_path = os.path.join(label_folder, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            if line.strip() == '':
                continue
            parts = line.strip().split()
            # 只修改类别号（第一个），其他不变
            parts[0] = '1'
            new_line = ' '.join(parts)
            new_lines.append(new_line + '\n')

        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

print("已全部将labelbook下的标签class编号改为1")
