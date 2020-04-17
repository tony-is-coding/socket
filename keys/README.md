# 在当前目录下生成一堆RSA-pem公私钥对
# 
#
#
#
#
# 先进入openssl 命令行下

#生成RSA私钥
genrsa -out rsa_private_key.pem 1024

#把RSA私钥转换成PKCS8格式
pkcs8 -topk8 -inform PEM -in rsa_private_key.pem -outform PEM –nocrypt

# 生成RSA公钥
rsa -in rsa_private_key.pem -pubout -out rsa_public_key.pem
