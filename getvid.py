import os
import sys
import subprocess
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import threading
import paramiko
from pathlib import Path

class VideoToNerfApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Video to NeRF Pipeline")
        self.root.geometry("700x600")
        
        # Configure style
        self.style = ttk.Style()
        self.style.configure("TButton", padding=6, relief="flat", background="#ccc")
        
        # Variables
        self.video_path = tk.StringVar()
        self.output_dir = tk.StringVar() #Deafult fot the data set test
        self.fps = tk.StringVar(value="1")  # Default 1 frame per second
        self.ssh_host = tk.StringVar()
        self.ssh_username = tk.StringVar()
        self.ssh_password = tk.StringVar()
        self.remote_dir = tk.StringVar()
        
        # Create frames
        self.create_input_frame()
        self.create_process_frame()
        self.create_ssh_frame()
        self.create_log_frame()
        
        # Initialize progress
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=680, mode="determinate")
        self.progress.pack(pady=10, padx=10)
        
    def create_input_frame(self):
        frame = ttk.LabelFrame(self.root, text="Input Settings")
        frame.pack(fill="x", padx=10, pady=5)
        
        # Video selection
        ttk.Label(frame, text="Video File:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.video_path, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Browse", command=self.browse_video).grid(row=0, column=2, padx=5, pady=5)
        
        # Output directory
        ttk.Label(frame, text="Output Directory:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.output_dir, width=50).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Browse", command=self.browse_output_dir).grid(row=1, column=2, padx=5, pady=5)
        
        # FPS setting
        ttk.Label(frame, text="Frames per second:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.fps, width=10).grid(row=2, column=1, sticky="w", padx=5, pady=5)
    def create_input_frame(self):
        frame = ttk.LabelFrame(self.root, text="Input Settings")
        frame.pack(fill="x", padx=10, pady=5)

        # Input type selection
        ttk.Label(frame, text="Input Type:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Radiobutton(frame, text="Video", variable=self.input_type, value="video", command=self.update_input_type).grid(row=0, column=1, sticky="w", padx=5, pady=5)
        ttk.Radiobutton(frame, text="Photos", variable=self.input_type, value="photos", command=self.update_input_type).grid(row=0, column=2, sticky="w", padx=5, pady=5)

        # Video selection
        self.video_frame = ttk.Frame(frame)
        self.video_frame.grid(row=1, column=0, columnspan=3, sticky="w", padx=5, pady=5)
        ttk.Label(self.video_frame, text="Video File:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(self.video_frame, textvariable=self.video_path, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(self.video_frame, text="Browse", command=self.browse_video).grid(row=0, column=2, padx=5, pady=5)

        # Photos selection
        self.photos_frame = ttk.Frame(frame)
        self.photos_frame.grid(row=2, column=0, columnspan=3, sticky="w", padx=5, pady=5)
        ttk.Label(self.photos_frame, text="Photo Files:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Button(self.photos_frame, text="Select Photos", command=self.browse_photos).grid(row=0, column=1, padx=5, pady=5)
        self.photos_frame.grid_remove()  # Hide by default

        # Output directory
        ttk.Label(frame, text="Output Directory:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.output_dir, width=50).grid(row=3, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Browse", command=self.browse_output_dir).grid(row=3, column=2, padx=5, pady=5)

        # FPS setting (only for video)
        self.fps_frame = ttk.Frame(frame)
        self.fps_frame.grid(row=4, column=0, columnspan=3, sticky="w", padx=5, pady=5)
        ttk.Label(self.fps_frame, text="Frames per second:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(self.fps_frame, textvariable=self.fps, width=10).grid(row=0, column=1, sticky="w", padx=5, pady=5)

    def update_input_type(self):
        """Update UI based on selected input type."""
        if self.input_type.get() == "video":
            self.video_frame.grid()
            self.photos_frame.grid_remove()
            self.fps_frame.grid()
        else:
            self.video_frame.grid_remove()
            self.photos_frame.grid()
            self.fps_frame.grid_remove()

    def browse_photos(self):
        """Allow the user to select multiple photos."""
        filepaths = filedialog.askopenfilenames(
            filetypes=[("Image files", "*.jpg *.jpeg *.png"), ("All files", "*.*")]
        )
        if filepaths:
            self.photo_paths = list(filepaths)
            self.log_message(f"Selected {len(self.photo_paths)} photos.")

    def run_llff(self):
    output_dir = self.output_dir.get()

    if not output_dir:
        messagebox.showerror("Error", "Please set an output directory")
        return

    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    if self.input_type.get() == "video":
        # Certifique-se de que os frames foram extraídos
        if not os.path.exists(images_dir) or not os.listdir(images_dir):
            messagebox.showerror("Error", "No images found. Extract frames first.")
            return
    else:
        # Copie as fotos selecionadas para o diretório de saída
        if not self.photo_paths:
            messagebox.showerror("Error", "No photos selected.")
            return
        for photo in self.photo_paths:
            dest_path = os.path.join(images_dir, os.path.basename(photo))
            if not os.path.exists(dest_path):
                os.link(photo, dest_path)

    # Executa o processamento do LLFF
    def run_llff_processing():
        try:
            self.log_message("Running LLFF (COLMAP) processing...")
            self.progress["value"] = 10

            llff_script = os.path.expanduser("~/LLFF/imgs2poses.py")
            if not os.path.exists(llff_script):
                self.log_message(f"Error: LLFF script not found at {llff_script}")
                self.log_message("Please install LLFF from https://github.com/Fyusion/LLFF")
                self.progress["value"] = 0
                return

            cmd = [
                sys.executable,  # Python executável
                llff_script,
                output_dir
            ]

            self.log_message(f"Running command: {' '.join(cmd)}")

            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            while process.poll() is None:
                if self.progress["value"] < 90:
                    self.progress["value"] += 1
                self.root.update()
                self.root.after(1000)

            stdout, stderr = process.communicate()

            if process.returncode == 0:
                self.log_message("LLFF processing completed successfully")
                if os.path.exists(os.path.join(output_dir, "poses_bounds.npy")):
                    self.log_message("poses_bounds.npy file generated successfully")
                else:
                    self.log_message("Warning: poses_bounds.npy file not found")
                self.progress["value"] = 100
            else:
                self.log_message(f"Error during LLFF processing: {stderr.decode()}")
                self.progress["value"] = 0

        except Exception as e:
            self.log_message(f"Error: {str(e)}")
            self.progress["value"] = 0

    threading.Thread(target=run_llff_processing).start()
        
    def create_process_frame(self):
        frame = ttk.LabelFrame(self.root, text="Processing")
        frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(frame, text="1. Extract Frames", command=self.extract_frames).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(frame, text="2. Run LLFF (COLMAP)", command=self.run_llff).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(frame, text="3. Upload to Server", command=self.upload_to_server).grid(row=0, column=2, padx=5, pady=5)
        
    def create_ssh_frame(self):
        frame = ttk.LabelFrame(self.root, text="SSH Settings")
        frame.pack(fill="x", padx=10, pady=5)
        
        # SSH Host
        ttk.Label(frame, text="SSH Host:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.ssh_host).grid(row=0, column=1, padx=5, pady=5)
        
        # SSH Username
        ttk.Label(frame, text="Username:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.ssh_username).grid(row=1, column=1, padx=5, pady=5)
        
        # SSH Password
        ttk.Label(frame, text="Password:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.ssh_password, show="*").grid(row=2, column=1, padx=5, pady=5)
        
        # Remote Directory
        ttk.Label(frame, text="Remote Directory:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.remote_dir).grid(row=3, column=1, padx=5, pady=5)
        
        # Test connection button
        ttk.Button(frame, text="Test Connection", command=self.test_ssh_connection).grid(row=3, column=2, padx=5, pady=5)
        
    def create_log_frame(self):
        frame = ttk.LabelFrame(self.root, text="Log")
        frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log = tk.Text(frame, wrap=tk.WORD, width=80, height=10)
        self.log.pack(fill="both", expand=True, padx=5, pady=5)
        scrollbar = ttk.Scrollbar(self.log, command=self.log.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log.config(yscrollcommand=scrollbar.set)
        
    def browse_video(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("Video files", "*.mp4 *.avi *.mov"), ("All files", "*.*")]
        )
        if filepath:
            self.video_path.set(filepath)
            
            # Auto-set output directory to video name
            video_name = os.path.splitext(os.path.basename(filepath))[0]
            default_output = os.path.join(os.path.dirname(filepath), video_name)
            self.output_dir.set(default_output)
    
    def browse_output_dir(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir.set(directory)
    
    def log_message(self, message):
        self.log.insert(tk.END, message + "\n")
        self.log.see(tk.END)
        self.root.update_idletasks()
        
    def extract_frames(self):
        video_path = self.video_path.get()
        output_dir = self.output_dir.get()
        fps = self.fps.get()
        
        if not video_path or not output_dir:
            messagebox.showerror("Error", "Please select a video and output directory")
            return
            
        # Create output directory if it doesn't exist
        images_dir = os.path.join(output_dir, "images")
        os.makedirs(images_dir, exist_ok=True)
        
        def run_extraction():
            try:
                self.log_message(f"Extracting frames from {video_path} at {fps} fps...")
                self.progress["value"] = 10
                
                # Run FFmpeg command
                cmd = [
                    "ffmpeg", "-i", video_path, 
                    "-r", fps, 
                    "-q:v", "1",  # High quality
                    os.path.join(images_dir, "frame_%04d.jpg")
                ]
                
                process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                stdout, stderr = process.communicate()
                
                self.progress["value"] = 90
                
                if process.returncode == 0:
                    num_frames = len([f for f in os.listdir(images_dir) if f.endswith('.jpg')])
                    self.log_message(f"Successfully extracted {num_frames} frames to {images_dir}")
                    self.progress["value"] = 100
                else:
                    self.log_message(f"Error extracting frames: {stderr.decode()}")
                    self.progress["value"] = 0
                    
            except Exception as e:
                self.log_message(f"Error: {str(e)}")
                self.progress["value"] = 0
                
        # Run in a separate thread to avoid freezing UI
        threading.Thread(target=run_extraction).start()
    
    def run_llff(self):
        output_dir = self.output_dir.get()
        
        if not output_dir:
            messagebox.showerror("Error", "Please set an output directory")
            return
        
        images_dir = os.path.join(output_dir, "images")
        if not os.path.exists(images_dir) or not os.listdir(images_dir):
            messagebox.showerror("Error", "No images found. Extract frames first.")
            return
            
        def run_llff_processing():
            try:
                self.log_message("Running LLFF (COLMAP) processing...")
                self.progress["value"] = 10
                
                # This assumes you have the LLFF repository in your PATH
                # You may need to adjust this to point to the actual location of imgs2poses.py
                llff_script = os.path.expanduser("~/LLFF/imgs2poses.py")
                if not os.path.exists(llff_script):
                    self.log_message(f"Error: LLFF script not found at {llff_script}")
                    self.log_message("Please install LLFF from https://github.com/Fyusion/LLFF")
                    self.progress["value"] = 0
                    return
                
                cmd = [
                    sys.executable,  # Python executable
                    llff_script,
                    output_dir
                ]
                
                self.log_message(f"Running command: {' '.join(cmd)}")
                
                process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                
                # This will take a while, so we'll show incremental progress
                while process.poll() is None:
                    if self.progress["value"] < 90:
                        self.progress["value"] += 1
                    self.root.update()
                    self.root.after(1000)  # Update every second
                
                stdout, stderr = process.communicate()
                
                if process.returncode == 0:
                    self.log_message("LLFF processing completed successfully")
                    if os.path.exists(os.path.join(output_dir, "poses_bounds.npy")):
                        self.log_message("poses_bounds.npy file generated successfully")
                    else:
                        self.log_message("Warning: poses_bounds.npy file not found")
                    self.progress["value"] = 100
                else:
                    self.log_message(f"Error during LLFF processing: {stderr.decode()}")
                    self.progress["value"] = 0
                    
            except Exception as e:
                self.log_message(f"Error: {str(e)}")
                self.progress["value"] = 0
        
        # Run in a separate thread
        threading.Thread(target=run_llff_processing).start()
    
    def test_ssh_connection(self):
        host = self.ssh_host.get()
        username = self.ssh_username.get()
        password = self.ssh_password.get()
        
        if not host or not username or not password:
            messagebox.showerror("Error", "Please fill in all SSH details")
            return
            
        def test_connection():
            try:
                self.log_message(f"Testing connection to {username}@{host}...")
                
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(hostname=host, username=username, password=password, timeout=10)
                
                self.log_message("SSH connection successful!")
                client.close()
                
            except Exception as e:
                self.log_message(f"SSH connection failed: {str(e)}")
        
        threading.Thread(target=test_connection).start()
    
    def upload_to_server(self):
        host = self.ssh_host.get()
        username = self.ssh_username.get()
        password = self.ssh_password.get()
        remote_dir = self.remote_dir.get()
        output_dir = self.output_dir.get()
        
        if not host or not username or not password or not remote_dir:
            messagebox.showerror("Error", "Please fill in all SSH details and remote directory")
            return
            
        if not output_dir or not os.path.exists(output_dir):
            messagebox.showerror("Error", "Output directory not found")
            return
            
        def upload():
            try:
                dataset_name = os.path.basename(output_dir)
                self.log_message(f"Uploading {dataset_name} to {username}@{host}:{remote_dir}...")
                self.progress["value"] = 10
                
                # Connect to SSH
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(hostname=host, username=username, password=password)
                
                # Create the remote directory structure
                remote_dataset_dir = f"{remote_dir}/{dataset_name}"
                stdin, stdout, stderr = client.exec_command(f"mkdir -p {remote_dataset_dir}")
                exit_status = stdout.channel.recv_exit_status()
                
                self.progress["value"] = 20
                
                # Open SFTP session
                sftp = client.open_sftp()
                
                # Upload all necessary files
                total_files = sum([len(files) for _, _, files in os.walk(output_dir)])
                uploaded_files = 0
                
                for root, dirs, files in os.walk(output_dir):
                    # Get the relative path from the output directory
                    rel_path = os.path.relpath(root, output_dir)
                    remote_path = remote_dataset_dir
                    
                    if rel_path != '.':
                        remote_path = f"{remote_dataset_dir}/{rel_path}"
                        client.exec_command(f"mkdir -p {remote_path}")
                        
                    for file in files:
                        local_file_path = os.path.join(root, file)
                        remote_file_path = f"{remote_path}/{file}"
                        
                        self.log_message(f"Uploading {local_file_path}...")
                        sftp.put(local_file_path, remote_file_path)
                        
                        uploaded_files += 1
                        progress_value = int(20 + (uploaded_files / total_files) * 70)
                        self.progress["value"] = min(90, progress_value)
                
                # Create a sample config file for NeRF
                config_content = f"""expname = {dataset_name}
datadir = ./data/nerf_llff_data/{dataset_name}
basedir = ./logs
dataset_type = llff
factor = 8
llffhold = 8
N_rand = 4096
N_samples = 64
N_importance = 64
use_viewdirs = True
raw_noise_std = 1.0"""
                
                # Create a temporary config file locally
                config_path = os.path.join(output_dir, f"config_{dataset_name}.txt")
                with open(config_path, 'w') as f:
                    f.write(config_content)
                
                # Upload the config file
                remote_config_path = f"{remote_dir}/config_{dataset_name}.txt"
                sftp.put(config_path, remote_config_path)
                
                self.progress["value"] = 95
                
                # Close connections
                sftp.close()
                client.close()
                
                self.log_message("Upload completed successfully!")
                self.log_message(f"To train your NeRF model, run:")
                self.log_message(f"python run_nerf.py --config config_{dataset_name}.txt")
                
                self.progress["value"] = 100
                
            except Exception as e:
                self.log_message(f"Upload failed: {str(e)}")
                self.progress["value"] = 0
        
        threading.Thread(target=upload).start()

def main():
    root = tk.Tk()
    app = VideoToNerfApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()