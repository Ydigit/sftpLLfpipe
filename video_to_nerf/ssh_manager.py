import os
import logging
import paramiko

class SSHManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def test_connection(self, host, username, password):
        """Testa a conexão SSH"""
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname=host, username=username, password=password, timeout=10)
            client.close()
            return True, "✅ SSH connection successful!"
        except Exception as e:
            self.logger.error(f"❌ SSH connection error: {str(e)}")
            return False, str(e)

    def upload_dataset(self, host, username, password, local_dir, remote_dir, progress_callback=None):
        """Envia um diretório completo via SFTP, garantindo que os arquivos sejam copiados corretamente"""
        try:
            if not os.path.exists(local_dir):
                return False, f"❌ Diretório local não encontrado: {local_dir}"

            print(f"🔄 Connecting with SSH {host}...")
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname=host, username=username, password=password)

            # 🔹 Create remote dir without dups
            stdin, stdout, stderr = client.exec_command(f"mkdir -p {remote_dir}")
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                return False, f"❌ Erro ao criar diretório remoto: {stderr.read().decode()}"

            # 🔹 Criar sessão SFTP
            sftp = client.open_sftp()

            print(f"📂 Upload from local: {local_dir} to {remote_dir} (ssh) ...")

            # 🔹 Obter lista de arquivos para progresso
            file_list = []
            #com path-> root, _->subdirs on folder but not used, files->list of current files 
            for root, _, files in os.walk(local_dir): #iteracaco das tuplas do walk
                for file in files:
                    file_list.append(os.path.join(root, file))

            total_files = len(file_list)
            if total_files == 0:
                return False, "❌ Nenhum arquivo encontrado para upload!"

            uploaded_files = 0

            for root, _, files in os.walk(local_dir):
                rel_path = os.path.relpath(root, local_dir)  # Relative path for the the 
                remote_path = os.path.join(remote_dir, rel_path).replace("\\", "/")

                # Criar diretório remoto se necessário
                try:
                    sftp.mkdir(remote_path)
                except IOError:
                    pass  # alredy exists the dir

                for file in files:
                    local_file = os.path.join(root, file)
                    remote_file = os.path.join(remote_path, file).replace("\\", "/")

                    print(f"⬆️ Sending {local_file} to {remote_file}...")
                    sftp.put(local_file, remote_file)

                    # Atualizar progresso
                    uploaded_files += 1
                    if progress_callback:
                        progress_value = int((uploaded_files / total_files) * 100)
                        progress_callback(min(100, progress_value))

            print("✅ Upload finalizado com sucesso!")

            sftp.close()
            client.close()
            return True, "✅ Upload completed successfully!"
        except Exception as e:
            return False, f"❌ Upload failed: {str(e)}"
