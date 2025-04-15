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
    def upload_via_jump(self, jump_host, jump_user, jump_pass, local_dir, final_host, final_path, progress_callback=None):
        """
        Envia dataset para o servidor final via máquina intermédia (jump host).
        """
        import paramiko
        import os

        try:
            # Conectar à máquina intermédia (jump host)
            jump = paramiko.SSHClient()
            jump.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            jump.connect(jump_host, username=jump_user, password=jump_pass)

            # Criar diretório temporário na máquina intermédia
            tmp_remote = "/tmp/nerf_dataset"
            sftp = jump.open_sftp()
            try:
                sftp.mkdir(tmp_remote)
            except:
                pass  # se já existir

            # Enviar local_dir -> máquina intermédia
            files = []
            for root, _, filelist in os.walk(local_dir):
                for f in filelist:
                    full = os.path.join(root, f)
                    rel = os.path.relpath(full, local_dir)
                    remote_file = os.path.join(tmp_remote, rel).replace("\\", "/")
                    remote_dir = os.path.dirname(remote_file)

                    # Criar pasta remota se não existir
                    try:
                        sftp.stat(remote_dir)
                    except:
                        parts = remote_dir.split("/")
                        for i in range(2, len(parts) + 1):
                            try:
                                sftp.mkdir("/".join(parts[:i]))
                            except:
                                pass

                    sftp.put(full, remote_file)
                    files.append(full)
                    if progress_callback:
                        progress_callback(int(len(files) / 10))  # feedback simples

            sftp.close()

            # Executar comando SSH na máquina intermédia → scp para servidor final
            dataset_name = os.path.basename(local_dir)
            cmd = f"ssh {jump_user}@{final_host} 'mkdir -p {final_path}/{dataset_name}' && scp -r {tmp_remote}/* {final_host}:{final_path}/{dataset_name}/"
            stdin, stdout, stderr = jump.exec_command(cmd)
            stdout.channel.recv_exit_status()

            jump.close()
            return True, f"Upload completo para {final_host}:{final_path}/{dataset_name}"

        except Exception as e:
            return False, f"Erro no upload via jump: {str(e)}"
    def test_remote_connection_via_jump(self, jump_host, jump_user, jump_pass, final_host, final_user, final_pass, final_port=22):
        """
        Testa a conexão ao servidor final através de uma máquina intermédia (jump host).
        Apenas verifica a conexão SSH, sem testar se o COLMAP está instalado.
        """
        import paramiko
        try:
            # 1. Conexão à máquina intermédia (jump host)
            jump = paramiko.SSHClient()
            jump.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            jump.connect(hostname=jump_host, username=jump_user, password=jump_pass, timeout=10)

            # 2. Encaminhar canal para o servidor final
            transport = jump.get_transport()
            dest_addr = (final_host, final_port)  # usa porta customizada
            local_addr = ('127.0.0.1', 0)
            channel = transport.open_channel("direct-tcpip", dest_addr, local_addr)

            # 3. Conexão ao servidor final via canal
            final = paramiko.SSHClient()
            final.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            final.connect(hostname=final_host, username=final_user, password=final_pass, sock=channel, timeout=10)

            final.close()
            jump.close()

            return True, "✅ Ligação ao servidor final estabelecida com sucesso (sem verificar COLMAP)."

        except Exception as e:
            return False, f"❌ Falha na ligação encadeada: {str(e)}"
