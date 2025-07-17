import os

def make_empty_labels(image_dir, label_dir):
    for fname in os.listdir(image_dir):
        if fname.lower().endswith(('.jpg', '.jpeg', '.png')):
            txt_name = os.path.splitext(fname)[0] + ".txt"
            txt_path = os.path.join(label_dir, txt_name)
            # 如果label文件不存在，创建空txt
            if not os.path.exists(txt_path):
                open(txt_path, 'w').close()
                print(f"生成空label: {txt_path}")

make_empty_labels(
    r".\dataset\images\train",
    r".\dataset\labels\train"
)
make_empty_labels(
    r".\dataset\images\val",
    r".\dataset\labels\val"
)