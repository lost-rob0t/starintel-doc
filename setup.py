from setuptools import setup, find_packages
import re
PACKAGE_NAME = 'starintel_doc'
SOURCE_DIRECTORY = './src'
SOURCE_PACKAGE_REGEX = re.compile(rf'^{SOURCE_DIRECTORY}')

source_packages = find_packages(include=[SOURCE_DIRECTORY, f'{SOURCE_DIRECTORY}.*'])
proj_packages = [SOURCE_PACKAGE_REGEX.sub(PACKAGE_NAME, name) for name in source_packages]
setup(
    version="0.4.2",
    description="Document Spec for Star intel",
    long_description=open("README.md", "r").read(),
    long_description_content_type="text/markdown",
    url="https://gitlab.com/unseen-giants/starintel_doc",
    author="Nsaspy",
    license="MIT",
    name=PACKAGE_NAME,
    packages=proj_packages,
    package_dir={PACKAGE_NAME: SOURCE_DIRECTORY},
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
)
