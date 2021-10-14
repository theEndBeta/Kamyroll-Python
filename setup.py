from setuptools import setup

setup(
    name="Kamyroll-Python",
    version="0.0.2",
    description="Download shows from crunchyroll",
    url="https://github.com/hyugogirubato/Kamyroll-Python",
    author="hyugogirubato",
    license="MIT",
    scripts=["bin/kamyroll"],
    packages=["kamyroll_python"],
    install_requires=[
        "requests",
        "colorama",
        "termcolor",
    ],
    tests_requires=[],
    zip_safe=False,
)
