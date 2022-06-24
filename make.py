# Created by BaiJiFeiLong@gmail.com at 2022/6/24
import os
import pathlib
import shutil

import PyInstaller.__main__

name = "IceSpringDesktopHelper"

excluded_files = """
Qt5DataVisualization.dll
Qt5Pdf.dll
Qt5Quick.dll
Qt5VirtualKeyboard.dll
d3dcompiler_47.dll
libGLESv2.dll
opengl32sw.dll
""".strip().splitlines()

print("Building...")
if pathlib.Path("dist").exists():
    print("Folder dist exists, removing...")
    shutil.rmtree("dist")

if pathlib.Path(f"{name}.7z").exists():
    print("Target archive exists, removing...")
    pathlib.Path(f"{name}.7z").unlink()

print("Packing...")
PyInstaller.__main__.run([
    "main.py",
    "--noconsole",
    "--noupx",
    "--name",
    name,
    "--ico",
    "resources/logo.ico",
    "--add-data",
    "resources;resources"
])

print("Cleaning...")
for file in pathlib.Path("dist").glob("*/*"):
    if file.name in excluded_files:
        print(f"Removing {file.name}")
        file.unlink()

os.system(f"cd dist && 7z a -mx=9 ../{name}.7z {name}")
