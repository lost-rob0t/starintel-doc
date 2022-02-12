from setuptools import setup

import starintel_doc

setup(name="starintel_doc",
      version=starintel_doc.__version__,
      description=couch3.__doc__[0],
      long_description=open("README.md", "r").read(),
      long_description_content_type="text/markdown",
      url="https://github.com/pekrau/CouchDB2",
      author="Nsaspy",
      author_email="nsaspy@airmail.cc",
      license="MIT",
      python_requires=">= 3.6",
      py_modules=["starintel_doc"],
      
      classifiers=[
          "License :: OSI Approved :: MIT License",
          "Intended Audience :: Developers",
          "Natural Language :: English",
          "Programming Language :: Python :: 3 :: Only",
          "Programming Language :: Python :: 3.10",
          "Operating System :: OS Independent",
          ],
)
