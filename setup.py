from setuptools import setup

import starintel_doc

setup(name="starintel_doc",
        version=starintel_doc.__version__,
        description="Document Spec for Star intel",
        long_description=open("README.md", "r").read(),
        long_description_content_type="text/markdown",
        url="https://gitlab.com/unseen-giants/starintel_doc",
        author="Nsaspy",
        author_email="nsaspy@airmail.cc",
        license="MIT",
        classifiers=[
              "License :: OSI Approved :: MIT License",
            "Intended Audience :: Developers",
            "Natural Language :: English",
            "Programming Language :: Python :: 3 :: Only",
            "Programming Language :: Python :: 3.10",
             "Operating System :: OS Independent",
            ]
)
