# video_to_nerf/app.py
import os
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import threading

from .frame_extractor import FrameExtractor
from .colmap_processor import ColmapProcessor
from .ssh_manager import SSHManager
from .utils import setup_logger


class VideoToNerfApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Video to NeRF Pipeline")
        self.root.geometry("700x600")
        
        # Configure style
        self.style = ttk.Style()
        self.style.configure("TButton", padding=6, relief="flat", background="#ccc")
        
        # Setup logger
        self.logger = setup_logger()
        
        # Initialize components
        self.frame_extractor = FrameExtractor()
        self.colmap_processor = ColmapProcessor()
        self.ssh_manager = SSHManager()
        
        # Variables
        self.video_path = tk.StringVar()
        self.output_dir = tk.StringVar()
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
        # Input frame implementation
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
    
    def create_process_frame(self):
        # Process frame implementation
        frame = ttk.LabelFrame(self.root, text="Processing")
        frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(frame, text="1. Extract Frames", command=self.extract_frames).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(frame, text="2. Run LLFF (COLMAP)", command=self.run_llff).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(frame, text="3. Upload to Server", command=self.upload_to_server).grid(row=0, column=2, padx=5, pady=5)
    
    def create_ssh_frame(self):
        # SSH frame implementation
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
        # Log frame implementation
        frame = ttk.LabelFrame(self.root, text="Log")
        frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log = tk.Text(frame, wrap=tk.WORD, width=80, height=10)
        self.log.pack(fill="both", expand=True, padx=5, pady=5)
        scrollbar = ttk.Scrollbar(self.log, command=self.log.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log.config(yscrollcommand=scrollbar.set)
    
    def log_message(self, message):
        self.log.insert(tk.END, message + "\n")
        self.log.see(tk.END)
        self.root.update_idletasks()
        self.logger.info(message)
    
    def browse_video(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("Video files", "*.mp4 *.avi *.mov"), ("All files", "*.*")]
        )
        if filepath:
            self.video_path.set(filepath)
            
            # Auto-set output directory to video name
            video_name = os.path.splitext(os.path.basename(filepath))[0] #fica so com o nome sem extensao
            default_output = os.path.join(os.path.dirname(filepath), video_name)
            self.output_dir.set(default_output)
    
    def browse_output_dir(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir.set(directory)
    
    def extract_frames(self):
        video_path = self.video_path.get()
        output_dir = self.output_dir.get()
        fps = self.fps.get()
        
        if not video_path or not output_dir:
            messagebox.showerror("Error", "Please select a video and output directory")
            return
            
        def run_extraction():
            try:
                self.log_message(f"Extracting frames from {video_path} at {fps} fps...")
                self.progress["value"] = 10
                
                # Use the FrameExtractor module
                success, message, num_frames = self.frame_extractor.extract(
                    video_path=video_path,
                    output_dir=output_dir,
                    fps=fps
                )
                
                if success:
                    self.log_message(f"Successfully extracted {num_frames} frames")
                    self.progress["value"] = 100
                else:
                    self.log_message(f"Error extracting frames: {message}")
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
        
        def run_llff_processing():
            try:
                self.log_message("Running LLFF (COLMAP) processing...")
                self.progress["value"] = 10
                
                # Use the ColmapProcessor module
                success, message = self.colmap_processor.process(
                    output_dir=output_dir,
                    progress_callback=self.update_progress
                )
                
                if success:
                    self.log_message("LLFF processing completed successfully")
                    self.progress["value"] = 100
                else:
                    self.log_message(f"Error during LLFF processing: {message}")
                    self.progress["value"] = 0
                    
            except Exception as e:
                self.log_message(f"Error: {str(e)}")
                self.progress["value"] = 0
        
        # Run in a separate thread
        threading.Thread(target=run_llff_processing).start()
    
    def update_progress(self, value):
        self.progress["value"] = value
        self.root.update_idletasks()
    
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
                
                # Use the SSHManager module
                success, message = self.ssh_manager.test_connection(
                    host=host,
                    username=username,
                    password=password
                )
                
                if success:
                    self.log_message("SSH connection successful!")
                else:
                    self.log_message(f"SSH connection failed: {message}")
                
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

        # 🚨 Verifica se o diretório local existe antes do upload
        if not output_dir or not os.path.exists(output_dir):
            messagebox.showerror("Error", f"Local directory {output_dir} not found!")
            return

        # 🔍 Debug: Mostra os caminhos no log
        self.log_message(f"📂 Local dir: {output_dir}")
        self.log_message(f"🌍 Remote dir: {remote_dir}")

        def upload():
            try:
                dataset_name = os.path.basename(output_dir)
                self.log_message(f"📤 Uploading {dataset_name} to {username}@{host}:{remote_dir}...")
                self.progress["value"] = 10

                # Chamar upload_directory corretamente
                success, message = self.ssh_manager.upload_dataset(
                    host=host,
                    username=username,
                    password=password,
                    local_dir=output_dir,
                    remote_dir=remote_dir,
                    progress_callback=self.update_progress
                )

                if success:
                    self.log_message("✅ Upload completed successfully!")
                    self.progress["value"] = 100
                else:
                    self.log_message(f"❌ Upload failed: {message}")
                    self.progress["value"] = 0

            except Exception as e:
                self.log_message(f"❌ Upload failed: {str(e)}")
                self.progress["value"] = 0

        threading.Thread(target=upload).start()


def main():
    root = tk.Tk()
    app = VideoToNerfApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()