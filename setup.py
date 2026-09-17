from setuptools import find_packages, setup

setup(
    name="starintel_doc",
    version="0.9.1",
    description="StarIntel 0.9.1 base parser with additive 0.9.2 HTTP transaction and web-capture profile support",
    long_description_content_type="text/markdown",
    url="https://github.com/lost-rob0t/starintel-doc",
    packages=find_packages(),
    install_requires=[
        "ulid-py",
        "dataclasses-json",
        "jsonschema>=4.23,<5",
    ],
    entry_points={
        "console_scripts": [
            "starintel-conformance=starintel_doc.conformance_adapter:main",
        ]
    },
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
)
