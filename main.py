"""

imgwriter / main.py
Copyright (c) 2022 Pyry Lahtinen
https://github.com/PyryL/imgwriter
File created on 2022-08-20

"""

from PIL import Image, ExifTags
from math import floor, ceil
from random import choice


class Writer:
    def __init__(self, image, payload) -> None:
        """
        param image should be string (path to file) or PIL.Image.Image
        param payload should be string or bytes
        """

        # load image
        if type(image) == str: self.__image = Image.open(image)
        elif isinstance(image, Image.Image): self.__image = image
        else: raise ValueError(f"Parameter image should be string or Pillow image, but {type(image)} was given")

        # prepare payload
        if type(payload) == str: self.__payload = payload.encode("utf-8")
        elif type(payload) == bytes: self.__payload = payload
        else: raise ValueError(f"Parameter payload should be string or bytes, but {type(payload)} was given")

        # add the message length data to the beginning of the payload
        payloadLength = len(self.__payload)
        if payloadLength.bit_length() > 64: raise ValueError(f"The payload is too long")
        messageLengthBinary = f"{payloadLength:064b}"        # str of 64 ones and zeros
        messageLengthParts = [int(messageLengthBinary[(8*i):(8*i+8)], 2) for i in range(8)]     # array len=8, each item 0...255
        self.__payload = bytearray(messageLengthParts) + self.__payload

        # check image color mode
        if self.__image.mode.lower() not in ["rgb", "rgba"]:
            raise ValueError(f"The provided image is in unsupported mode {self.__image.mode}, RGB or RGBA is needed")

        # check image size
        if self.__image.width*self.__image.height < payloadLength+8:
            raise ValueError(f"The provided image is too small")
        
        # perform writing
        self.__write()

    def __modifyColor(self, color: int, targetMod: int) -> int:
        """
        color in range 0...255
        targetMod in range 0...7
        """
        
        # check that the color is 8-bit
        if color < 0 or color > 255 or type(color) != int:
            raise ValueError()
        
        # calculate the two nearest target mods
        n = (color - targetMod) / 8
        lowN, highN = floor(n), ceil(n)
        lowerColor, higherColor = 8*lowN+targetMod, 8*highN+targetMod

        # make decision
        if lowerColor < 0: return higherColor
        if higherColor > 255: return lowerColor
        return choice([lowerColor, higherColor])
    
    def __modifyPixel(self, pixel: tuple[int], payloadByte: int) -> tuple[int]:
        # check that the byte is 8-bit
        if payloadByte < 0 or payloadByte > 255 or type(payloadByte) != int:
            raise ValueError(f"Unexpected non-8-bit byte in payload")

        # split the 8-bit byte into three parts for R, G and B
        payloadBinary = f"{payloadByte:08b}"        # str of eight ones and zeros
        payloadParts = int(payloadBinary[0:3], 2), int(payloadBinary[3:6], 2), int(payloadBinary[6:], 2)    # all ints in 0...7

        # modify the pixel colors
        newR = self.__modifyColor(pixel[0], payloadParts[0])
        newG = self.__modifyColor(pixel[1], payloadParts[1])
        newB = self.__modifyColor(pixel[2], payloadParts[2])

        # return new pixel data
        if len(pixel) == 4: return (newR, newG, newB, pixel[3])
        return (newR, newG, newB)
        
    def __write(self) -> None:
        imageWidth = self.__image.width
        for i, payloadByte in enumerate(self.__payload):
            x, y = i%imageWidth, i//imageWidth
            oldPixel = self.__image.getpixel((x, y))
            newPixel = self.__modifyPixel(oldPixel, payloadByte)
            self.__image.putpixel((x, y), newPixel)
    
    @property
    def image(self) -> Image.Image:
        """ The modified image with data in it """
        return self.__image
    
    def save(self, path: str, addExif: bool = False) -> None:
        """ Saves the modified image to provided path """
        exif = None
        if addExif:
            processingSoftwareCode = list(ExifTags.TAGS.keys())[list(ExifTags.TAGS.values()).index("ProcessingSoftware")]
            exif = self.__image.getexif()
            exif[processingSoftwareCode] = "ImgWriter 1.0"

        self.__image.save(path, exif=exif)


class Reader:
    def __init__(self, image) -> None:
        """
        param image should be string (path to file) or PIL.Image.Image
        """

        # load image
        if type(image) == str: self.__image = Image.open(image)
        elif isinstance(image, Image.Image): self.__image = image
        else: raise ValueError(f"Parameter image should be string or Pillow image, but {type(image)} was given")

        # check image color mode
        if self.__image.mode.lower() not in ["rgb", "rgba"]:
            raise ValueError(f"The provided image is in unsupported mode {self.__image.mode}, RGB or RGBA is needed")

        # preform read
        self.__read()
    
    def __readFromPixel(self, x: int, y: int) -> int:
        pixelData = self.__image.getpixel((x, y))

        # calculate targetMod
        tR, tG, tB = pixelData[0]%8, pixelData[1]%8, pixelData[2]%8

        # convert to binary
        tR, tG, tB = f"{tR:03b}", f"{tG:03b}", f"{tB:02b}"
        return int(tR+tG+tB, 2)

    def __readPayloadLength(self) -> int:
        imageWidth = self.__image.width
        eightPixels = [self.__readFromPixel(i%imageWidth, i//imageWidth) for i in range(8)]
        together = "".join([f"{p:08b}" for p in eightPixels])
        messageLength = int(together, 2)
        return messageLength

    def __read(self) -> None:
        payloadLength = self.__readPayloadLength()
        imageWidth = self.__image.width
        payload = bytearray()
        for i in range(8, payloadLength+8):
            x, y = i%imageWidth, i//imageWidth
            payloadByte = self.__readFromPixel(x, y)
            payload.append(payloadByte)
        self.__payload = payload
    
    @property
    def payloadBinary(self) -> bytearray:
        return self.__payload
    
    @property
    def payloadString(self) -> str:
        return self.__payload.decode("utf-8")
