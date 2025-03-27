FROM python:3.12

RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && apt-get clean

ENV BROWSER_PATH=/usr/bin/chrom

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY cog_presets ./cog_presets
COPY cogs ./cogs
COPY components ./components
COPY config ./config
COPY data ./data
COPY database ./database
COPY facades ./facades
COPY globalconf ./globalconf
COPY services ./services
COPY util ./util
COPY main.py ./main.py

EXPOSE 5000

CMD ["/bin/sh", "-c", "python main.py > /dev/ttyS0 2>&1"]