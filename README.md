# Gaccho

gaccho is timeline aggregation tool for Rss, Twitter, and more

#### require

```
[debian,ubuntu]
$ sudo apt-get install -y libncurses5 libncurses5-dev libncursesw5 libncursesw5-dev libreadline-dev pkg-config
  or
$ sudo make setup
```

#### manage gaccho plugin

plugin currently under development [repositories](https://github.com/nobiki?utf8=%E2%9C%93&tab=repositories&q=gaccho&type=&language=)

```
$ make install PACKAGE=[PACKAGE NAME]
$ make update PACKAGE=[PACKAGE NAME]
$ make remove PACKAGE=[PACKAGE NAME]

example:
$ make install PACKAGE=rss
```
