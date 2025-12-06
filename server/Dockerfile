FROM python:3.12.12-slim

# 定义构建参数，默认为 false (GitHub Actions 环境使用)
# 本地构建时如果需要加速，可使用: docker build --build-arg USE_CHINA_MIRROR=true ...
ARG USE_CHINA_MIRROR=false

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Shanghai

WORKDIR /app

RUN if [ "$USE_CHINA_MIRROR" = "true" ]; then \
        sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources; \
    fi \
    && apt-get update && apt-get install -y --no-install-recommends \
    gcc libc-dev tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

RUN if [ "$USE_CHINA_MIRROR" = "true" ]; then \
        pip install --no-cache-dir poetry -i https://pypi.tuna.tsinghua.edu.cn/simple; \
    else \
        pip install --no-cache-dir poetry; \
    fi

# 复制依赖文件和 README.md（构建上下文是 server 目录）
COPY pyproject.toml poetry.lock* README.md ./

RUN poetry config virtualenvs.create false \
    && if [ "$USE_CHINA_MIRROR" = "true" ]; then \
        poetry source add --priority=default mirrors https://pypi.tuna.tsinghua.edu.cn/simple/; \
    fi \
    && poetry install --no-root --only main --no-interaction --no-ansi

# 复制 server 目录的其他内容（src、main.py 等）
COPY . .

RUN poetry install --only main --no-interaction --no-ansi

EXPOSE 8080

CMD ["python", "main.py"]
