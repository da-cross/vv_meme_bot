from cnocr import CnOcr
import os
from typing import Dict, List
from tqdm import tqdm

# prepare the data

def single_image_ocr(img_fp, threshold=0, raw=True):
    ocr = CnOcr()  # 所有参数都使用默认值
    out = ocr.ocr(img_fp)
    if raw:
        return out
    texts = []
    for result in out:
        if result['score'] > threshold:
            texts.append(result['text'])
    return texts

def ocr_imgs2txts(img_folder, output_folder, threshold=0):
    ocr = CnOcr()
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    img_files = os.listdir(img_folder)
    for img_fp in tqdm(img_files, desc="Processing images"):
        img_texts = []
        img_path = os.path.join(img_folder, img_fp)
        out: List[Dict] = ocr.ocr(img_path)
        for result in out:
            if result['score'] > threshold:
                img_texts.append(result['text'])
        output_fp = os.path.join(output_folder, os.path.splitext(img_fp)[0] + '.txt')
        with open(output_fp, 'w', encoding='utf-8') as f:
            f.write('\n'.join(img_texts))
    return output_folder


if __name__ == "__main__":
    # print(single_image_ocr("V5bCQAxMDgxMzc4NTc-xiVmRJ2-JA.jpg", raw=False))
    ocr_imgs2txts("vvs", "txts")