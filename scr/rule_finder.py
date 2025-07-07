import os
import numpy as np
import pandas as pd
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import logging

# === Configure logging ===
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)

def standardize_term(x):
    if isinstance(x, str):
        x = x.strip()
        replacements = {
            "Distributed Three": "Distribute_Three",
            "Distribute Three": "Distribute_Three",
            "Arithmetic": "Arithmetic"
        }
        return replacements.get(x, x)
    return x

def save_problem_grid(image, filename):
    fig = plt.figure(figsize=(10, 10))
    for i in range(8):
        ax = plt.subplot(3, 3, i + 1)
        ax.imshow(image[i], cmap='gray')
        ax.axis('off')
        rect = Rectangle((0, 0), 1, 1, transform=ax.transAxes, color='gray', fill=False, lw=1.8)
        ax.add_patch(rect)
    ax = plt.subplot(3, 3, 9)
    ax.text(0.5, 0.5, '?', fontsize=40, ha='center', va='center')
    ax.axis('off')
    rect = Rectangle((0, 0), 1, 1, transform=ax.transAxes, color='gray', fill=False, lw=1.8)
    ax.add_patch(rect)
    plt.subplots_adjust(wspace=0.1, hspace=0.1)
    plt.savefig(filename)
    plt.close(fig)

def save_choices_plot(image, target, filename):
    fig = plt.figure(figsize=(12, 6))
    for i in range(8, 16):
        ax = plt.subplot(2, 4, i - 7)
        ax.set_title(f"Choice {i - 7}")
        ax.imshow(image[i], cmap='gray')
        ax.axis('off')
        rect = Rectangle((0, 0), 1, 1, transform=ax.transAxes, color='gray', fill=False, lw=1.8)
        ax.add_patch(rect)
    plt.subplots_adjust(wspace=0.1, hspace=0.3)
    plt.savefig(filename)
    plt.close(fig)

def main():
    logging.info("Starting rule_finder process...")
    current_dir = os.getcwd()
    project_dir = os.path.dirname(current_dir)

    # Load Excel files
    data_spec_path = os.path.join(project_dir, 'data', 'raw_data_2.xlsx')
    single_dir = os.path.join(project_dir, 'rule_output', 'in_out_single.xlsx')
    four_dir = os.path.join(project_dir, 'rule_output', 'in_out_four.xlsx')
    left_right_dir = os.path.join(project_dir, 'rule_output', 'left_right_single.xlsx')
    up_down_dir = os.path.join(project_dir, 'rule_output', 'up_down.xlsx')

    logging.info("Loading rule and data specification files...")
    data_spec = pd.read_excel(data_spec_path, sheet_name='Scoring Key')
    single_df = pd.read_excel(single_dir)
    four_df = pd.read_excel(four_dir)
    left_right_df = pd.read_excel(left_right_dir)
    up_down_df = pd.read_excel(up_down_dir)

    for col in ['Type_0', 'Size_0', 'Type_1', 'Size_1']:
        data_spec[col] = data_spec[col].apply(standardize_term)

    design_to_df = {
        'In_Out_Center_Single': single_df,
        'In_Out_Distribute_Four': four_df,
        'Left_Right_Single': left_right_df,
        'Up_Down_Single': up_down_df
    }

    eligible_sources = []
    logging.info("Matching eligible source matrices...")
    for i, row in data_spec.iterrows():
        design = row['Design']
        df = design_to_df.get(design)

        if df is not None:
            filtered = df[
                (df['Number_0'] == 'Constant') &
                (df['Position_0'] == 'Constant') &
                (df['Number_1'] == 'Constant') &
                (df['Position_1'] == 'Constant') &
                (df['Color_0'] == 'Constant') &
                (df['Color_1'] == 'Constant') &
                (df['Type_0'] == row['Type_0']) &
                (df['Size_0'] == row['Size_0']) &
                (df['Type_1'] == row['Type_1']) &
                (df['Size_1'] == row['Size_1'])
            ]
            names = filtered['Name'].tolist()
            eligible_sources.append(names)
            logging.debug(f"Row {i}: Found {len(names)} eligible sources.")
        else:
            logging.warning(f"Row {i}: Design '{design}' not found in mapping.")
            eligible_sources.append([])

    result_df = data_spec.copy()
    result_df['Source_file'] = eligible_sources

    output_folder = os.path.join(project_dir, 'new_image')
    os.makedirs(output_folder, exist_ok=True)
    temp_folder = os.path.join(project_dir, 'temp')
    os.makedirs(temp_folder, exist_ok=True)

    updated_result_df = result_df.copy()
    logging.info("Rendering and saving images...")

    for idx, row in updated_result_df.iterrows():
        file_base = row['File_Name']
        design = row['Design']
        source_files = row['Source_file']

        if not isinstance(source_files, list) or len(source_files) == 0:
            logging.info(f"Row {idx}: No source files found. Skipping.")
            continue

        correct_options = []
        for i, file_name in enumerate(source_files):
            if not file_name.endswith('.npz'):
                file_name += '.npz'

            design_paths = {
                'In_Out_Center_Single': 'output/in_center_single_out_center_single',
                'In_Out_Distribute_Four': 'output/in_distribute_four_out_center_single',
                'Left_Right_Single': 'output/left_center_single_right_center_single',
                'Up_Down_Single': 'output/up_center_single_down_center_single',
            }

            folder = design_paths.get(design)
            if not folder:
                logging.error(f"Row {idx}: Design {design} not recognized.")
                continue

            npz_path = os.path.join(project_dir, folder, file_name)
            if not os.path.exists(npz_path):
                logging.warning(f"File not found: {npz_path}")
                continue

            data = np.load(npz_path)
            image = data['image']
            target = int(data['target'])
            correct_options.append(target)

            output_name = f"{file_base}_val.png" if len(source_files) == 1 else f"{file_base}_val_{i}.png"
            save_path = os.path.join(output_folder, output_name)

            save_problem_grid(image, "temp_img/problem_grid.png")
            save_choices_plot(image, target, "temp_img/choices_plot.png")

            problem_grid = Image.open("temp_img/problem_grid.png")
            choices_plot = Image.open("temp_img/choices_plot.png")

            combined_width = max(problem_grid.width, choices_plot.width)
            combined_height = problem_grid.height + choices_plot.height

            combined_image = Image.new("RGB", (combined_width, combined_height), (255, 255, 255))
            combined_image.paste(problem_grid, ((combined_width - problem_grid.width) // 2, 0))
            combined_image.paste(choices_plot, ((combined_width - choices_plot.width) // 2, problem_grid.height))
            combined_image.save(save_path)
            logging.info(f"Saved image: {save_path}")

        updated_result_df.at[idx, 'Correct Option'] = correct_options[0] if len(correct_options) == 1 else correct_options

    result_dir = os.path.join(project_dir, 'result')
    os.makedirs(result_dir, exist_ok=True)
    output_path = os.path.join(result_dir, 'eligible_matrix.xlsx')
    updated_result_df.to_excel(output_path, index=False)
    logging.info(f"Final Excel saved to: {output_path}")
    logging.info("Done!")

if __name__ == '__main__':
    main()
