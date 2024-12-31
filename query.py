import json
import os
from search_utils import similarity
from typing import List, Dict

from PIL import Image
import matplotlib.pyplot as plt


def _load_data(text_list: str='text_list.txt', text_to_filepath: str='text_to_filepath.json', txts_json: str='txts.json') -> List[str]:
    with open(text_list, 'r', encoding='utf-8') as file:
        text_list = file.read().splitlines()
    with open(text_to_filepath, 'r', encoding='utf-8') as file:
        text_to_filepath = json.load(file)
    with open(txts_json, 'r', encoding='utf-8') as file:
        txts = json.load(file)
    return text_list, text_to_filepath, txts

def find_matches(query: str, text_list: list, text_to_filepath: dict, top_k: int = 5, sim_thres: float=0.3):
    results = []
    for text in text_list:
        sim = similarity(query, text)
        if sim > sim_thres:
            results.append((text, sim, text_to_filepath[text]))
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]

def locate_matched_images(results: List[str], img_folder: str='vvs'):
    img_paths = []
    for result in results:
        corresponding_images = result[2]
        for img_name in corresponding_images:
            img_path = os.path.join(img_folder, img_name.replace('.txt', '.jpg'))
            img_paths.append(img_path)
    return img_paths

def fetch_image(txt_name: str, img_folder: str='vvs', display: bool=True):
    img_name_from_txt = txt_name.replace('.txt', '.jpg')
    img_path = os.path.join(img_folder, img_name_from_txt)
    print(img_path)
    if display:
        img = Image.open(img_path)
        plt.imshow(img)
        plt.axis('off')  # Hide axes
        plt.show()
    return img_path

if __name__ == "__main__":
    text_list, text_to_filepath = _load_data()
    query = "迎头痛击"
    results = find_matches(query, text_list, text_to_filepath)
    for result in results:
        print(result)
    fetch_image(results[0][2][0])
