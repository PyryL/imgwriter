"""

imgwriter / main.py
Copyright (c) 2022 Pyry Lahtinen
https://github.com/PyryL/imgwriter
File created on 2022-08-20

"""

from PIL import Image, ExifTags
from math import floor, ceil
from random import choice
from hashlib import sha256


class Writer:
    def __init__(self, image, payload: bytes, dataType: str) -> None:
        """
        param image should be string (path to file) or PIL.Image.Image
        param dataType is the file extension of the data
        """

        # load image
        if type(image) == str: self.__image = Image.open(image)
        elif isinstance(image, Image.Image): self.__image = image
        else: raise ValueError(f"Parameter image should be string or Pillow image, but {type(image)} was given")

        # check image color mode
        if self.__image.mode.lower() not in ["rgb", "rgba"]:
            raise ValueError(f"The provided image is in unsupported mode {self.__image.mode}, RGB or RGBA is needed")

        # prepare payload
        if type(payload) is not bytes:
            raise ValueError(f"Parameter payload should be string or bytes, but {type(payload)} was given")
        if type(dataType) is not str:
            raise ValueError("Data type must be provided when payload is not string")
        self.__payload = payload

        # perform writing
        self.__prepareMessage(dataType)
        self.__write()
    
    def __prepareMessage(self, dataType: str) -> None:
        self.__message = bytearray()

        # protocol version
        self.__message.append(0b1)

        # sha256 checksum
        self.__message += sha256(self.__payload).digest()

        # data type
        dataTypeBytes = dataType.encode("utf-8")
        if len(dataTypeBytes) > 10:
            raise ValueError("Data type is too long to be encoded")
        dataTypePadding = bytes(10 - len(dataTypeBytes))
        self.__message += dataTypePadding + dataTypeBytes

        # payload length
        payloadLength = len(self.__payload)
        if payloadLength.bit_length() > 10:
            raise ValueError("Payload is too long")
        if payloadLength+51 > self.__image.width*self.__image.height:
            raise ValueError("The provided image is too small")
        self.__message += payloadLength.to_bytes(8, "big")

        # the payload itself
        self.__message += self.__payload

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
    
    def __modifyPixel(self, pixel: tuple[int], messageByte: int) -> tuple[int]:
        # check that the byte is 8-bit
        if messageByte < 0 or messageByte > 255 or type(messageByte) != int:
            raise ValueError(f"Unexpected non-8-bit byte in message")

        # split the 8-bit byte into three parts for R, G and B
        messageBinary = f"{messageByte:08b}"        # str of eight ones and zeros
        messageParts = int(messageBinary[0:3], 2), int(messageBinary[3:6], 2), int(messageBinary[6:], 2)    # all ints in 0...7

        # modify the pixel colors
        newR = self.__modifyColor(pixel[0], messageParts[0])
        newG = self.__modifyColor(pixel[1], messageParts[1])
        newB = self.__modifyColor(pixel[2], messageParts[2])

        # return new pixel data
        if len(pixel) == 4: return (newR, newG, newB, pixel[3])
        return (newR, newG, newB)
        
    def __write(self) -> None:
        imageWidth = self.__image.width
        for i, messageByte in enumerate(self.__message):
            x, y = i%imageWidth, i//imageWidth
            oldPixel = self.__image.getpixel((x, y))
            newPixel = self.__modifyPixel(oldPixel, messageByte)
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
        self.__readMetadata()
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
    
    def __readMetadata(self) -> None:
        # protocol version
        protocolVersion = self.__readFromPixel(0, 0)
        if protocolVersion != 1:
            raise ValueError(f"Unexpected protocol version {protocolVersion}")

        # sha256 checksum
        imageWidth = self.__image.width
        self.__shaChecksum = bytes([self.__readFromPixel(i%imageWidth, i//imageWidth) for i in range(1, 33)])

        # data type
        dataType = bytearray([self.__readFromPixel(i%imageWidth, i//imageWidth) for i in range(33, 43)])
        self.__dataType = dataType.lstrip(b"\0").decode("utf-8")

        # payload length
        payloadLengthBytes = [self.__readFromPixel(i%imageWidth, i//imageWidth) for i in range(43, 51)]
        self.__payloadLength = int.from_bytes(bytearray(payloadLengthBytes), "big")

    def __read(self) -> None:
        imageWidth = self.__image.width
        payload = bytearray()
        for i in range(51, self.__payloadLength+51):
            payloadByte = self.__readFromPixel(i%imageWidth, i//imageWidth)
            payload.append(payloadByte)
        self.__payload = payload
        if sha256(self.__payload).digest() != self.__shaChecksum:
            raise ValueError("Payload corrupted")
    
    @property
    def payloadBinary(self) -> bytearray:
        return self.__payload
    
    @property
    def dataType(self) -> str:
        """ The file extension of the payload """
        return self.__dataType
