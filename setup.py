from setuptools import find_packages, setup


setup(
    name="starintel_doc",
    version="0.9.0",
    description="Canonical Python runtime for StarIntel document schema v0.9.0",
    long_description_content_type="text/markdown",
    url="https://github.com/lost-rob0t/starintel-doc",
    packages=find_packages(),
    install_requires=["ulid-py", "dataclasses-json"],
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
)
