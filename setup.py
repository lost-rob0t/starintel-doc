from setuptools import find_packages, setup

setup(
    name="starintel_doc",
    version="0.10.1",
    description="StarLang-generated StarIntel 0.10.1 runtime with explicit historical compatibility",
    long_description_content_type="text/markdown",
    url="https://github.com/lost-rob0t/starintel-doc",
    packages=find_packages(),
    package_data={"starintel_canonical": ["py.typed", "_release/*", "_release/generated/*", "_compatibility/*.json"], "starintel_doc": ["_legacy/*"]},
    install_requires=[
        "ulid-py",
        "dataclasses-json",
        "jsonschema[format]>=4.23,<5",
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
