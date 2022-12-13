# syntax=docker/dockerfile:1
FROM ubuntu:20.04

ENV DEBIAN_FRONTEND noninteractive
#ENV HOME /root
#ENV TEST_ENV test-value
RUN echo "Europe/Moscow" > /etc/timezone
# install app dependencies
RUN apt-get clean autoclean
RUN apt update
RUN apt install -y python3
RUN apt update
RUN apt install -y python3-pip
RUN apt install -y openjdk-8-jdk
RUN apt install -y openjdk-8-jre
RUN apt install -y firefox firefox-geckodriver
RUN apt install -y firefox-geckodriver
RUN apt install -y cron
RUN apt install -y tzdata
RUN pip install selenium
RUN pip install BeautifulSoup4
RUN pip install lxml
RUN pip install webdriver-manager
RUN mkdir selen
RUN mkdir /selen/share
RUN chmod a+x /selen
RUN cd selen/



RUN dpkg-reconfigure -f noninteractive tzdata

WORKDIR /selen/

COPY . .

RUN chmod a+x Selenium.py


#ENTRYPOINT ["python3", "Selenium.py"]

RUN crontab -l | { cat; echo "*/20 * * * * python3 /selen/Selenium.py >> /var/log/info.log 2>&1"; } | crontab -
RUN ln -sf /dev/stdout /var/log/info.log
CMD /usr/sbin/cron -f