install:
	pip install git+https://github.com/nobiki/gaccho_${PACKAGE}.git

update:
	pip install -U git+https://github.com/nobiki/gaccho_${PACKAGE}.git

remove:
	pip uninstall gaccho-${PACKAGE}

