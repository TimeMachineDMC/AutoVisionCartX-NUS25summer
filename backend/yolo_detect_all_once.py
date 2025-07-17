from ultralytics import YOLO
import cv2

model = YOLO(r"runs\detect\train\weights\best.pt") 

cap = cv2.VideoCapture(0)
print("按空格检测一次所有目标，q退出")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    show_frame = frame.copy()
    key = cv2.waitKey(1) & 0xFF

    if key == ord(' '):
        results = model(frame)
        found = False
        all_output = []

        for r in results:
            for box in r.boxes:
                cls = int(box.cls[0])
                name = model.names[cls]
                conf = float(box.conf[0])

                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = [float(x) for x in [x1, y1, x2, y2]]
                cx, cy = (x1 + x2) / 2, (y1 + y2) / 2

                found = True
                # 记录所有检测结果
                all_output.append(
                    f"类别: {name}, 置信度: {conf:.2f}, 坐标: [{x1:.2f}, {y1:.2f}, {x2:.2f}, {y2:.2f}], 中心: ({cx:.2f}, {cy:.2f})"
                )

                # 多类别标注
                color_map = {
                    'banana': (0, 255, 0),
                    'book': (255, 0, 0),
                    'elderly': (255, 200, 0),
                    'young': (0, 128, 255),
                }
                box_color = color_map.get(name, (0, 255, 255))

                # 框出来+标注类别和置信度
                cv2.rectangle(show_frame, (int(x1), int(y1)), (int(x2), int(y2)), box_color, 2)
                label = f"{name} {conf:.2f}"
                cv2.putText(show_frame, label, (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, box_color, 2)
                # 标注坐标
                coord_text = f"({int(x1)},{int(y1)})-({int(x2)},{int(y2)})"
                cv2.putText(show_frame, coord_text, (int(x1), int(y2) + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)
                # 标注中心点
                center_text = f"({int(cx)},{int(cy)})"
                cv2.circle(show_frame, (int(cx), int(cy)), 5, (0,0,255), -1)
                cv2.putText(show_frame, center_text, (int(cx)+10, int(cy)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)

        if found:
            # 统一打印所有目标
            print('\n'.join(all_output))
        else:
            print("没有检测到目标")

        cv2.imshow("result_all", show_frame)
        cv2.waitKey(0)
        cv2.destroyWindow("result_all")
    else:
        cv2.imshow("YOLOv8 custom detect", show_frame)

    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
