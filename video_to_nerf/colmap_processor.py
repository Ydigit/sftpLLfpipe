import subprocess
import os

class ColmapProcessor:
    def __init__(self):
        pass

    def process(self, output_dir, progress_callback=None):
        """
        Process images using COLMAP and generate LLFF dataset.

        Args:
            output_dir (str): Path where the images are stored.
            progress_callback (function, optional): Function to update progress.

        Returns:
            tuple: (success, message)
        """
        try:
            database_path = os.path.join(output_dir, "database.db")
            image_path = os.path.join(output_dir, "images")
            sparse_path = os.path.join(output_dir, "sparse")

            os.makedirs(sparse_path, exist_ok=True)

            # 📌 Rodar COLMAP
            commands = [
                f"colmap feature_extractor --database_path {database_path} --image_path {image_path}",
                f"colmap exhaustive_matcher --database_path {database_path}",
                f"colmap mapper --database_path {database_path} --image_path {image_path} --output_path {sparse_path}"
            ]

            for i, cmd in enumerate(commands):
                process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if process.returncode != 0:
                    return False, f"Error in COLMAP: {process.stderr}"
                if progress_callback:
                    progress_callback((i + 1) * 30)

            # 🛠️ Gerar poses_bounds.npy com imgs2poses.py
            imgs2poses_script = os.path.join(os.getcwd(), "LLFF", "imgs2poses.py")
            process = subprocess.run(f"python {imgs2poses_script} {output_dir} --match_type exhaustive_matcher", shell=True, capture_output=True, text=True)

            if process.returncode != 0:
                return False, f"Error in imgs2poses.py: {process.stderr}"

            # 📉 Gerar versões reduzidas das imagens
            self.downscale_images(output_dir)

            return True, "COLMAP processing and LLFF conversion completed successfully."

        except Exception as e:
            return False, str(e)

    def downscale_images(self, output_dir):
        """Reduz imagens originais para criar `images_4` e `images_8`."""
        image_path = os.path.join(output_dir, "images")
        images_4_path = os.path.join(output_dir, "images_4")
        images_8_path = os.path.join(output_dir, "images_8")

        os.makedirs(images_4_path, exist_ok=True)
        os.makedirs(images_8_path, exist_ok=True)

        # Pega a lista de imagens
        image_files = sorted([f for f in os.listdir(image_path) if f.endswith(".jpg")])

        if len(image_files) == 0:
            print("❌ Nenhuma imagem encontrada para redimensionamento!")
            return

        print(f"📂 Encontradas {len(image_files)} imagens para processar.")

        # Loop para converter imagens individualmente
        for img in image_files:
            input_img = os.path.join(image_path, img)
            output_img_4 = os.path.join(images_4_path, img)
            output_img_8 = os.path.join(images_8_path, img)

            # ⚡ Reduz imagem para 1/4 da resolução original
            cmd_4 = f'ffmpeg -i "{input_img}" -vf scale=iw/4:ih/4 "{output_img_4}" -y'
            result_4 = subprocess.run(cmd_4, shell=True, capture_output=True, text=True)

            # ⚡ Reduz imagem para 1/8 da resolução original
            cmd_8 = f'ffmpeg -i "{input_img}" -vf scale=iw/8:ih/8 "{output_img_8}" -y'
            result_8 = subprocess.run(cmd_8, shell=True, capture_output=True, text=True)

            # 📌 Debug dos erros do ffmpeg
            if result_4.returncode != 0:
                print(f"❌ Erro ao converter {img} para images_4: {result_4.stderr}")
            if result_8.returncode != 0:
                print(f"❌ Erro ao converter {img} para images_8: {result_8.stderr}")

        print("✅ Redimensionamento concluído!")