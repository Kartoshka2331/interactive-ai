import subprocess
import sys
import os


def run_command(command):
    try:
        subprocess.check_call(command, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing: {command}")
        sys.exit(1)


def main():
    print(">>> Setting up Interactive AI Environment...")

    os.makedirs("logs", exist_ok=True)
    os.makedirs("shared_data", exist_ok=True)
    print(">>> Created 'logs' and 'shared_data' directories")

    print(">>> Building Isolated Docker Environment...")
    run_command("docker build -t interactive-ai-env isolated_environment/")

    if not os.path.exists(".env"):
        print(">>> WARNING: .env file not found. Copying .env.example...")
        if os.path.exists(".env.example"):
            import shutil
            shutil.copy(".env.example", ".env")
            print(">>> .env created. PLEASE EDIT IT WITH YOUR API KEYS")
        else:
            print(">>> Error: .env.example missing")

    print("\n>>> Setup Complete")
    print(">>> Run 'python start_system.py' to launch")

if __name__ == "__main__":
    main()
