import subprocess
import sys

def create_venv():
    # Criar ambiente virtual
    subprocess.call([sys.executable, "-m", "venv", "venv"])

def install_packages():
    # Comando para ativar o ambiente virtual, dependendo do sistema operacional
    activate_command = ".\\venv\\Scripts\\activate.bat" if sys.platform == "win32" else "source venv/bin/activate"

    # Lista de pacotes a serem instalados
    packages = ["kivy[full]", "kivy_garden.graph", "pymodbustcp", "pymodbus"]

    # Instalar pacotes no ambiente virtual
    for package in packages:
        subprocess.call(f"{activate_command} && {sys.executable} -m pip install {package}", shell=True)

if __name__ == "__main__":
    create_venv()
    print("Ambiente virtual criado. Por favor, ative-o manualmente antes de continuar.")
    print("No Windows, use: .\\venv\\Scripts\\activate")
    print("No Unix/MacOS, use: source venv/bin/activate")
    install_packages()
