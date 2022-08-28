"""

imgwriter / devsetup.py
Copyright (c) 2022 Pyry Lahtinen
MIT license (read more on LICENSE.txt)
https://github.com/PyryL/imgwriter
File created on 2022-08-28

"""

# THIS SCRIPT IS USED TO SETUP THE DEVELOPMENT ENVIRONMENT
# NO NEED TO DISTRIBUTE THIS SCRIPT IN RELEASES

import os

class Setup:
    def __init__(self) -> None:
        self.__createWhiteBackgroundIcon()

    def __createWhiteBackgroundIcon(self) -> None:
        """ Create an icon with white background instead of transparency """

        projectDir = os.path.split(__file__)[0]
        buildDir = os.path.join(projectDir, "build")
        iconPath = os.path.join(projectDir, "icon.png")
        whiteIconPath = os.path.join(buildDir, "icon_white.png")

        if os.path.exists(whiteIconPath): return
        print("Creating an icon with white background...")
        from PIL import Image

        if not os.path.exists(buildDir):
            os.mkdir(buildDir)

        iconImg = Image.open(iconPath)
        iconImg.load()

        whiteImg = Image.new("RGB", iconImg.size, (239, 239, 239))
        whiteImg.paste(iconImg, mask=iconImg.split()[3])
        whiteImg.save(whiteIconPath)

        iconImg.close()
        whiteImg.close()


if __name__ == "__main__":
    Setup()
