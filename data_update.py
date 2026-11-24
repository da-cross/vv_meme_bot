import os
import json
from text_clean import clean_text
from text_clean import clean_text

def save_plain_list(text_list, output_file):
    with open(output_file, 'w', encoding='utf-8') as file:
        for line in text_list:
            file.write(line + '\n')

def save_dict_to_json(data, output_file):
    with open(output_file, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)

def read_and_save_txt_files(txt_folder):
    '''
    空间换时间
    '''
    files_dict = {}
    text_list = []
    text_to_filepath = {}

    for filename in sorted(os.listdir(txt_folder)):
        if filename.endswith('.txt'):
            filepath = os.path.join(txt_folder, filename)
            with open(filepath, 'r', encoding='utf-8') as file:
                # 原始 OCR 结果保留在 txts/，只在这里滤掉台标/UI/乱码后再建索引
                lines = []
                for raw_line in file.read().splitlines():
                    text = clean_text(raw_line)
                    if text and text not in lines:
                        lines.append(text)

                files_dict[filename] = lines
                for line in lines:
                    if line not in text_to_filepath:
                        text_list.append(line)
                        text_to_filepath[line] = [filename]
                    elif filename not in text_to_filepath[line]:
                        text_to_filepath[line].append(filename)
    
    save_plain_list(text_list, 'text_list.txt')
    save_dict_to_json(text_to_filepath, 'text_to_filepath.json')
    
    return True

if __name__ == "__main__":
    # 只有真正跑 OCR 时才需要 cnocr，重建索引（read_and_save_txt_files）不需要
    from ocr_utils import ocr_imgs2txts

    output_folder = ocr_imgs2txts("vvs", "txts")
    udpated = read_and_save_txt_files(output_folder)

