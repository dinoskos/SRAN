from utils.file_extraction import Raven
from utils.parsing import Parsing
from tqdm import tqdm
import os
import numpy as np
import pandas as pd

if __name__ == '__main__':
    raven_util = Raven()
    parsing = Parsing()

    columns = ['Name', 'Rotation', 'Uniformity']
    whole_attribute = pd.DataFrame(columns=columns)

    # Input specification
    path_input = input(f'Which folder do you want to extract: ')
    path_output = input(f'Name of output folder: ')

    # Create folder if not already exist
    os.makedirs("rule_output", exist_ok=True)
    data_path = raven_util.get_path(path=os.path.join("rule_output", path_input))
    #data_path = raven_util.get_path(path_input)

    npz_file = raven_util.get_npz_files()

    # Iteratively loadfile
    for file_name in tqdm(npz_file):
        base_name = os.path.splitext(file_name)[0]
        npz_file_path = os.path.join(data_path, file_name)
        xml_file_path = os.path.join(data_path, f"{base_name}.xml")

        # Load npz file
        raven = np.load(npz_file_path)
        structure = raven['structure'][3]

        raven_data = parsing.parse_raven_xml(xml_file_path)

        # Specifying the structure for first figure
        number_0 = raven_data[1][0]['rules'][0]['name']
        position_0 = raven_data[1][0]['rules'][0]['name']
        type_0 = raven_data[1][0]['rules'][1]['name']
        size_0 = raven_data[1][0]['rules'][2]['name']
        color_0 = raven_data[1][0]['rules'][3]['name']
        uniformity = parsing.extract_unique_uniformity_values(raven_data)
        rotation = parsing.extract_unique_angle_values(raven_data)

        # Specifying the structure for the second figure
        try:
            number_1 = raven_data[1][1]['rules'][0]['name']
            position_1 = raven_data[1][1]['rules'][0]['name']
            type_1 = raven_data[1][1]['rules'][1]['name']
            size_1 = raven_data[1][1]['rules'][2]['name']
            color_1 = raven_data[1][1]['rules'][3]['name']
        except (IndexError, KeyError):
            number_1 = None
            position_1 = None
            type_1 = None
            size_1 = None
            color_1 = None

        # Extract attributes and append to DataFrame
        single_matrices = pd.DataFrame({
            'Name': base_name,
            'Structure': [structure],
            'Number_0': number_0,
            'Position_0': position_0,
            'Type_0': type_0,
            'Size_0': size_0,
            'Color_0': color_0,
            'Number_1': number_1,
            'Position_1': position_1,
            'Type_1': type_1,
            'Size_1': size_1,
            'Color_1': color_1,
            'Rotation': [rotation],
            'Uniformity': [uniformity]
        })

        whole_attribute = pd.concat([whole_attribute, single_matrices], ignore_index=True)

    if not path_output.endswith(".xlsx"):
        path_output += ".xlsx"

    raven_util.export_data(whole_attribute, path_output, 'output')