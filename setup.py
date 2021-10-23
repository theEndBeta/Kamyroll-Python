from setuptools import setup

setup(
    name="Kamyroll-Python",
    version="0.0.2",
    description="Download shows from crunchyroll",
    url="https://github.com/theEndBeta/Kamyroll-Python",
    author="theEndBeta",
    license="MIT",
    scripts=["bin/kamyroll"],
    packages=["kamyroll"],
    install_requires=[
        "requests",
    ],
    tests_requires=[],
    zip_safe=False,
)
