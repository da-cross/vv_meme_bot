import os
import json
from ocr_utils import ocr_imgs2txts

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
    
    for filename in os.listdir(txt_folder):
        if filename.endswith('.txt'):
            filepath = os.path.join(txt_folder, filename)
            with open(filepath, 'r', encoding='utf-8') as file:
                lines = file.read().splitlines()
                files_dict[filename] = lines
                text_list.extend(lines)
                for line in lines:
                    if line in text_to_filepath:
                        text_to_filepath[line].append(filename)
                    else:
                        text_to_filepath[line] = [filename]
    
    save_plain_list(text_list, 'text_list.txt')
    save_dict_to_json(text_to_filepath, 'text_to_filepath.json')
    
    return True

if __name__ == "__main__":
    output_folder = ocr_imgs2txts("vvs", "txts")
    udpated = read_and_save_txt_files(output_folder)

