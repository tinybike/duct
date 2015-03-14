#!/usr/bin/env python
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name="duct",
    version="0.0.1",
    description="tape",
    author="Jack Peterson",
    author_email="<jack@tinybike.net>",
    maintainer="Jack Peterson",
    maintainer_email="<jack@tinybike.net>",
    license="MIT",
    url="https://github.com/tinybike/duct",
    download_url = "https://github.com/tinybike/duct/tarball/0.0.1",
    install_requires=["Flask", "Flask-SocketIO", "GitPython", "Jinja2", "Werkzeug", "MarkupSafe", "gevent", "gitdb", "greenlet", "itsdangerous", "smmap", "numpy", "six"],
    keywords = ["bitcoin", "decentralized", "ethereum", "pyethereum", "UI"]
)
