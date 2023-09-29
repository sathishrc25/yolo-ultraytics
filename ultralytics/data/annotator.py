# Ultralytics YOLO 🚀, AGPL-3.0 license

from pathlib import Path

from ultralytics import SAM, YOLO


def auto_annotate(data, det_model='yolov8x.pt', sam_model='sam_b.pt', device='', output_dir=None):
    """
    Automatically annotates images using a YOLO object detection model and a SAM segmentation model.

    Args:
        data (str): Path to a folder containing images to be annotated.
        det_model (str, optional): Pre-trained YOLO detection model. Defaults to 'yolov8x.pt'.
        sam_model (str, optional): Pre-trained SAM segmentation model. Defaults to 'sam_b.pt'.
        device (str, optional): Device to run the models on. Defaults to an empty string (CPU or GPU, if available).
        output_dir (str | None | optional): Directory to save the annotated results.
            Defaults to a 'labels' folder in the same directory as 'data'.

    Example:
        ```python
        from ultralytics.data.annotator import auto_annotate

        auto_annotate(data='ultralytics/assets', det_model='yolov8n.pt', sam_model='mobile_sam.pt')
        ```
    """
    det_model = YOLO(det_model)
    sam_model = SAM(sam_model)

    data = Path(data)
    if not output_dir:
        output_dir = data.parent / f'{data.stem}_auto_annotate_labels'
    Path(output_dir).mkdir(exist_ok=True, parents=True)

    det_results = det_model(data, stream=True, device=device)

    for result in det_results:
        class_ids = result.boxes.cls.int().tolist()  # noqa
        if len(class_ids):
            boxes = result.boxes.xyxy  # Boxes object for bbox outputs
            sam_results = sam_model(result.orig_img, bboxes=boxes, verbose=False, save=False, device=device)
            segments = sam_results[0].masks.xyn  # noqa

            segment_dir = output_dir / 'segment'
            Path(segment_dir).mkdir(exist_ok=True, parents=True)
            with open(f'{str(Path(segment_dir) / Path(result.path).stem)}.txt', 'w') as f:
                for i in range(len(segments)):
                    s = segments[i]
                    if len(s) == 0:
                        continue
                    segment = map(str, segments[i].reshape(-1).tolist())
                    f.write(f'{class_ids[i]} ' + ' '.join(segment) + '\n')

            det_bboxes = result.boxes.xywhn.cpu().numpy()
            detection_dir = output_dir / 'detect'
            Path(detection_dir).mkdir(exist_ok=True, parents=True)
            result.save_txt(f'{str(Path(detection_dir) / Path(result.path).stem)}.txt')

            if result.keypoints:
                keypoints = result.keypoints.xyn.cpu().numpy()
                pose_dir = output_dir / 'pose'
                Path(pose_dir).mkdir(exist_ok=True, parents=True)
                with open(f'{str(Path(pose_dir) / Path(result.path).stem)}.txt', 'w') as f:
                    for i in range(len(det_bboxes)):
                        box = map(str, det_bboxes[i])
                        keypoint = map(str, keypoints[i].flatten())
                        f.write(f'{class_ids[i]} ' + ' '.join(box) + ' ' + ' '.join(keypoint) + '\n')
