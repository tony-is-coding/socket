"""
安全思路:
    目的: 最大限度的保证客户端服务端的安全传输

    步骤:
        预备: 客户端生成一对公/私钥 cp,cs, 服务端持有一对公/私钥 sp,ss
        1. 握手阶段, 确立可靠通信第一步; 客户端向服务器发起握手请求, 并且将明文的cp 传递给到服务端,
           保证这次连接的keep-alive(后期可以设计为close)
           服务端收到握手请求确认后, 将 sp 用 cp 加密后返回给客户端,客户端拿到sp用 cs解密获取到原来的sp
        2. 之后传输, 默认以 sp 加密传输, md5 生成摘要去做检验比对
"""
import base64
from typing import ByteString

import rsa

__pub_key = b''
__sec_key = b''


def __load_pub_key():
    global __pub_key
    with open("keys/public", "rb") as f:
        __pub_key = f.read()


def __load_sec_key():
    global __sec_key
    with open("keys/private", "rb") as f:
        __sec_key = f.read()


def pub_key():
    if not __pub_key:
        __load_pub_key()
    return __pub_key


def sec_key():
    if not __sec_key:
        __load_sec_key()
    return __sec_key


class Crypto:
    @staticmethod
    def encrypt(data: ByteString) -> ByteString:
        pubkey = rsa.PublicKey.load_pkcs1_openssl_pem(pub_key())
        # 公钥加密
        crypt = rsa.encrypt(data, pubkey)
        return base64.b64encode(crypt)

    @staticmethod
    def decrypt(data: ByteString) -> ByteString:
        data = base64.b64decode(data)
        seckey = rsa.PrivateKey.load_pkcs1(sec_key(), format='PEM')
        return rsa.decrypt(data, seckey)


crypto = Crypto()
