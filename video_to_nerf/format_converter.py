import os
import json
import numpy as np
import shutil
from PIL import Image

def convert_llff_to_nerfstudio(dataset_dir, output_path=None):
    """
    Converte um dataset LLFF (com poses_bounds.npy) para formato Nerfstudio (transforms.json).
    """
    try:
        poses_bounds_path = os.path.join(dataset_dir, "poses_bounds.npy")
        images_dir = os.path.join(dataset_dir, "images")
        if not os.path.exists(poses_bounds_path):
            return False, "Ficheiro poses_bounds.npy não encontrado!"
        if not os.path.exists(images_dir):
            return False, "Diretório de imagens não encontrado!"

        poses_bounds = np.load(poses_bounds_path)
        if output_path is None:
            output_path = os.path.join(dataset_dir, "nerfstudio_format")
        os.makedirs(output_path, exist_ok=True)

        num_images = poses_bounds.shape[0]
        image_paths = sorted([
            f for f in os.listdir(images_dir)
            if f.lower().endswith((".jpg", ".png", ".jpeg"))
        ])

        if len(image_paths) != num_images:
            return False, f"Número de imagens ({len(image_paths)}) não coincide com poses ({num_images})"

        frames = []
        for i in range(num_images):
            pose = poses_bounds[i, :-2].reshape(3, 5)
            transform_matrix = np.eye(4)
            transform_matrix[:3, :4] = pose[:, :4]

            frame = {
                "file_path": f"./images/{image_paths[i]}",
                "transform_matrix": transform_matrix.tolist()
            }
            frames.append(frame)

        # Copiar imagens
        ns_images_path = os.path.join(output_path, "images")
        os.makedirs(ns_images_path, exist_ok=True)
        for img in image_paths:
            shutil.copy2(os.path.join(images_dir, img), os.path.join(ns_images_path, img))

        # ⚠️ Focal pode ser estimado de forma mais precisa via imgs2poses.py, aqui é default aproximado
        transforms = {
            "camera_angle_x": 0.6911112070083618,
            "frames": frames
        }

        with open(os.path.join(output_path, "transforms.json"), "w") as f:
            json.dump(transforms, f, indent=4)

        return True, f"Dataset convertido com sucesso para {output_path}"
    
    except Exception as e:
        return False, str(e)
