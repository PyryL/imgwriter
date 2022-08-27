# -*- mode: python ; coding: utf-8 -*-

# imgwriter / gui.spec
# Copyright (c) 2022 Pyry Lahtinen
# https://github.com/PyryL/imgwriter
# File created on 2022-08-27

import main
import os

# MAKE ICON WITH WHITE BACKGROUND
if not os.path.exists("build/icon_white.png"):
    print("Creating an icon with white background...")
    from PIL import Image
    if not os.path.exists("build"):
        os.mkdir("build")
    iconImg = Image.open("icon.png")
    iconImg.load()
    whiteImg = Image.new("RGB", iconImg.size, (239, 239, 239))
    whiteImg.paste(iconImg, mask=iconImg.split()[3])
    whiteImg.save("build/icon_white.png")
    iconImg.close()
    whiteImg.close()


block_cipher = None

a = Analysis(['gui.py'],
             pathex=[],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,  
          [],
          name='gui',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None)

app = BUNDLE(exe,
             name='ImgWriter.app',
             icon='build/icon_white.png',
             bundle_identifier=None,
             version=main.__version__)
