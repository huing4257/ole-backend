FROM python:3.10

ENV DEPLOY 1

WORKDIR /opt/tmp

COPY . .

RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple cmake
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

EXPOSE 80

CMD ["sh", "start.sh"]
