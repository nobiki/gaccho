setup:
	apt-get install libncurses5 libncurses5-dev libncursesw5 libncursesw5-dev libreadline-dev pkg-config
	pip install -r requirements.txt

install:
	pip install git+https://github.com/nobiki/gaccho_${PACKAGE}.git

update:
	pip install -U git+https://github.com/nobiki/gaccho_${PACKAGE}.git

remove:
	pip uninstall gaccho-${PACKAGE}

container:
	docker run --rm -it -v $$PWD:/app -e "TZ=Asia/Tokyo" --name gaccho python:3.6 /bin/bash -c "cd /app/ && mkdir -p cache && make install PACKAGE=rss && make install PACKAGE=twitter && python ./gaccho.py"
