import json
import site
import os
import sys
from typing import Callable
import datetime as dt
from requests import Session
import functools
import tarfile


def bool_decorator(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            f(*args, **kwargs)
        except:
            return False
        else:
            return True
    return wrapper


class Log(object):
    def __init__(self, out: Callable = sys.stdout.write, err: Callable = sys.stderr.write) -> None:
        self.__out, self.__err = out, err

    def log(self, s: str) -> None:
        l = ("{time} - {message}".format(time=dt.datetime.now().strftime("%H:%M:%S"), message=s))
        self.__out(l)

    def log_error(self, s: str) -> None:
        l = ("{time} - ERROR - {message}".format(time=dt.datetime.now().strftime("%H:%M:%S"), message=s))
        self.__err(l)


class Install(object):
    def __init__(self, module: str) -> None:
        self.__module = module
        self.__base = "https://pypi.python.org/pypi/{}/json"
        u, self.__packages_abs_path = site.getsitepackages()
        self.__rel_path = os.path.join("temporary", self.__module+".tar.gz")
        self.__goal_path = os.path.join(
            self.__packages_abs_path, self.__module)
        if "temporary" not in os.listdir():
            os.mkdir("temporary")

    @bool_decorator
    def download(self) -> None:
        r = Session()
        response = r.get(self.__base.format(self.__module))
        if response.status_code != 200:
            raise Exception()
        url = json.loads(response.text)["urls"][-1]["url"]
        package_response = r.get(url)
        if package_response.status_code != 200:
            raise Exception()
        with open(self.__rel_path, mode="wb") as f:
            for chunk in package_response.iter_content(chunk_size=512*1024):
                if chunk:
                    f.write(chunk)
        r.close()

    @bool_decorator
    def unzip(self) -> None:
        with tarfile.open(self.__rel_path) as f:
            f.extractall(self.__goal_path)
        self.__clean()

    def __clean(self) -> None:
        os.remove(self.__rel_path)
        os.remove("temporary")


class ImportResolve(Install):
    def __init__(self, error: tuple) -> None:
        self.__error = error
        self.__module = self.__error.name
        self.__base = "https://pypi.python.org/pypi/{}/json"
        u, self.__packages_abs_path = site.getsitepackages()
        self.__rel_path = os.path.join("temporary", self.__module+".tar.gz")
        self.__goal_path = os.path.join(
            self.__packages_abs_path, self.__module)
        if "temporary" not in os.listdir():
            os.mkdir("temporary")

    def check(self) -> None:
        self.__module = self.__module.replace("_", "-")

    def restart(self) -> None:
        os.startfile(os.path.abspath(__file__))


def auto_resolve(error: tuple) -> None:
    l = Log(out=print, err=print)
    r = ImportResolve(error)
    r.check()
    l.log("Beginning the download of package '{}'.".format(error.name))
    if r.download():
        l.log("Package '{}' downloaded successfully.".format(error.name))
        r.unzip()
    else:
        l.log_error("Failed to install package '{}'.".format(error.name))
    r.restart()


def install(module: str) -> bool:
    l = Log(out=print, err=print)
    i = Install(module)
    l.log("Beginning the download of package '{}'.".format(module))
    r = i.download() and i.unzip()
    if r:
        l.log("Package '{}' downloaded successfully.".format(module))
    else:
        l.log_error("Failed to install package '{}'.".format(module))
    return r
