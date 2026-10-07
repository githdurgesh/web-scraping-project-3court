# import re
# import cv2
# import numpy as np
# from paddleocr import PaddleOCR
# import asyncio


# class PaddleCaptchaSolver:
#     """
#     Generic Singleton Captcha Solver using PaddleOCR.
#     Can be reused across multiple courts (Gujarat HC, eCourts, etc.)
#     with dynamic captcha lengths.
#     """
#     _instance = None

#     def __new__(cls):
#         if cls._instance is None:
#             cls._instance = super(PaddleCaptchaSolver, cls).__new__(cls)
#             cls._instance.ocr = PaddleOCR(use_angle_cls=False, lang="en", show_log=False)
#         return cls._instance

#     def solve(self, image_bytes: bytes, expected_length: int = None) -> str:
   
#         if not image_bytes:
#             return ""

#         np_arr = np.frombuffer(image_bytes, np.uint8)
#         img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
#         if img is None:
#             return ""

#         # 1. OCR on Raw Image
#         res_raw = self.ocr.ocr(img, cls=False)
#         raw_text = ""
#         if res_raw and res_raw[0]:
#             raw_text = "".join([line[1][0] for line in res_raw[0]])
#         cleaned_raw = re.sub(r"[^a-zA-Z0-9]", "", raw_text).strip()

#         # Check raw image result if expected_length matches
#         if expected_length is not None:
#             if len(cleaned_raw) == expected_length:
#                 return cleaned_raw

#         # 2. OCR on Preprocessed / Thresholded Image (Grayscale + Otsu Thresholding)
#         gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#         _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
#         res_thresh = self.ocr.ocr(thresh, cls=False)
#         thresh_text = ""
#         if res_thresh and res_thresh[0]:
#             thresh_text = "".join([line[1][0] for line in res_thresh[0]])
#         cleaned_thresh = re.sub(r"[^a-zA-Z0-9]", "", thresh_text).strip()

#         if expected_length is not None:
#             if len(cleaned_thresh) == expected_length:
#                 return cleaned_thresh
#             return cleaned_raw if len(cleaned_raw) == expected_length else (cleaned_thresh or cleaned_raw)

#         # Fallback for dynamic length (when expected_length is None)
#         if cleaned_raw and cleaned_thresh:
#             return cleaned_raw if len(cleaned_raw) >= len(cleaned_thresh) else cleaned_thresh

#         return cleaned_raw or cleaned_thresh



import re
import cv2
import numpy as np
from paddleocr import PaddleOCR
import asyncio


class PaddleCaptchaSolver:
    """
    Generic CAPTCHA text extraction using PaddleOCR.
    CAPTCHA length is not assumed here.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PaddleCaptchaSolver, cls).__new__(cls)
            cls._instance.ocr = PaddleOCR(use_angle_cls=False, lang="en", show_log=False )
        return cls._instance

    def solve(self, image_bytes: bytes) -> str:

        if not image_bytes:
            return ""

        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if img is None:
            return ""

        # 1. OCR on raw image
        res_raw = self.ocr.ocr(img, cls=False)

        raw_text = ""

        if res_raw and res_raw[0]:
            raw_text = "".join(
                line[1][0]
                for line in res_raw[0]
            )

        cleaned_raw = re.sub(
            r"[^a-zA-Z0-9]",
            "",
            raw_text
        ).strip()

        # 2. OCR on preprocessed image
        gray = cv2.cvtColor(
            img,
            cv2.COLOR_BGR2GRAY
        )

        _, thresh = cv2.threshold(
            gray,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        res_thresh = self.ocr.ocr(
            thresh,
            cls=False
        )

        thresh_text = ""

        if res_thresh and res_thresh[0]:
            thresh_text = "".join(
                line[1][0]
                for line in res_thresh[0]
            )

        cleaned_thresh = re.sub(
            r"[^a-zA-Z0-9]",
            "",
            thresh_text
        ).strip()

        # Return OCR result without assuming CAPTCHA length
        if cleaned_raw and cleaned_thresh:
            return (
                cleaned_raw
                if len(cleaned_raw) >= len(cleaned_thresh)
                else cleaned_thresh
            )

        return cleaned_raw or cleaned_thresh