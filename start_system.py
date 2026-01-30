import subprocess
import time
import os
import sys
from dotenv import load_dotenv


load_dotenv()


def main():
    ssh_port = os.getenv("SSH_PORT", "2222")
    ssh_password = os.getenv("SSH_PASSWORD", "Pa55w0rd!")
    host_data = os.path.abspath(os.getenv("HOST_SHARED_DATA_PATH", "./shared_data"))

    print(f"--- Interactive AI Launcher ---")

    print("Stopping existing containers...")
    subprocess.run("docker rm -f interactive-ai-container", shell=True, stderr=subprocess.DEVNULL)

    print("Launching Isolated Environment...")
    docker_cmd = (
        f"docker run -d --name interactive-ai-container "
        f"-p {ssh_port}:22 "
        f"-v \"{host_data}:/root/data\" "
        f"-e SSH_ROOT_PASSWORD={ssh_password} "
        f"interactive-ai-env"
    )

    if subprocess.call(docker_cmd, shell=True) != 0:
        print("Failed to start Docker container")
        sys.exit(1)

    print("Waiting for SSH to initialize...")
    time.sleep(3)

    print("Starting FastAPI Backend...")
    try:
        subprocess.run([sys.executable, "main.py"], check=True)
    except KeyboardInterrupt:
        print("\nShutting down...")
        subprocess.run("docker stop interactive-ai-container", shell=True)


if __name__ == "__main__":
    main()
