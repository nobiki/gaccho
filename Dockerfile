FROM debian:stretch
MAINTAINER Naoaki Obiki
RUN apt-get update && apt-get install -y python3 python3-pip git
RUN apt-get install -y libncurses5 libncurses5-dev libncursesw5 libncursesw5-dev libreadline-dev pkg-config
RUN git clone "https://github.com/nobiki/gaccho.git" /usr/local/lib/gaccho
RUN pip3 install git+https://github.com/nobiki/gaccho_rss.git
CMD ["python3","/usr/local/lib/gaccho/gaccho.py"]
