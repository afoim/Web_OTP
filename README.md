# Web_OTP
使用Python构建的Web_OTP

### 使用教程（Docker）

1. 启动Docker容器：`docker run -d -p 5000:5000 --name web_otp ghcr.io/afoim/web_otp:latest`
2. 导出你的OTP。如果是二维码请解析，可以使用草料二维码或者拿微信等不会直接导入OTP的软件扫一下，提取文本，如下
- 谷歌验证器导出后为：`otpauth-migration://offline?data=CioKCuTM6G%2BhwNS1yEgSDkdpdEh1YjpBY29Gb3JrGgZHaXRIdWIgASgBMAIQARgBIAAoqsCNpQc%3D`
- 普通验证器导出后为：`otpauth://totp/GitHub:AcoFork?algorithm=SHA1&digits=6&issuer=GitHub&period=30&secret=4TGOQ35BYDKLLSCI`
3. 将文本填入。如果你是谷歌验证器导出需要勾选`从谷歌验证器导入`

### 效果图

 ![效果图](img/demo.png)