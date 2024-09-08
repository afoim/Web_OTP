# 使用官方 Python 3.9 作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 将当前目录内容复制到容器的 /app 目录
COPY . /app

RUN pip config set global.index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple

# 安装应用程序的依赖项
RUN pip install --no-cache-dir -r requirements.txt

# 运行应用程序
CMD ["python", "app.py"]
