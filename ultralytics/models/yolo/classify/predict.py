# Ultralytics YOLO 🚀, AGPL-3.0 license

import torch
from PIL import Image

from ultralytics.data.augment import ToTensor
from ultralytics.engine.predictor import BasePredictor
from ultralytics.engine.results import Results
from ultralytics.utils import DEFAULT_CFG


class ClassificationPredictor(BasePredictor):
    """
    A class extending the BasePredictor class for prediction based on a classification model.

    Notes:
        - Torchvision classification models can also be passed to the 'model' argument, i.e. model='resnet18'.

    Example:
        ```python
        from ultralytics.utils import ASSETS
        from ultralytics.models.yolo.classify import ClassificationPredictor

        args = dict(model='yolov8n-cls.pt', source=ASSETS)
        predictor = ClassificationPredictor(overrides=args)
        predictor.predict_cli()
        ```
    """

    def __init__(self, cfg=DEFAULT_CFG, overrides=None, _callbacks=None):
        super().__init__(cfg, overrides, _callbacks)
        self.args.task = 'classify'
        self.has_legacy_transforms = any([isinstance(transform, ToTensor) for transform in self.transforms.transforms])

    def preprocess(self, img):
        """Converts input image to model-compatible data type."""
        if not isinstance(img, torch.Tensor):
            if self.has_legacy_transforms:  # to handle legacy transforms
                img = torch.stack([self.transforms(im) for im in img], dim=0)
            else:
                img = torch.stack([self.transforms(Image.fromarray(im)) for im in img], dim=0)
        img = (img if isinstance(img, torch.Tensor) else torch.from_numpy(img)).to(self.model.device)
        return img.half() if self.model.fp16 else img.float()  # uint8 to fp16/32

    def postprocess(self, preds, img, orig_imgs):
        """Post-processes predictions to return Results objects."""
        results = []
        is_list = isinstance(orig_imgs, list)  # input images are a list, not a torch.Tensor
        for i, pred in enumerate(preds):
            orig_img = orig_imgs[i] if is_list else orig_imgs
            img_path = self.batch[0][i]
            results.append(Results(orig_img, path=img_path, names=self.model.names, probs=pred))
        return results
