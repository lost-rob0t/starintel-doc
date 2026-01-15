from setuptools import setup, find_packages


setup(
    name="starintel_doc",
    version="0.8.2",
    description="Document Spec for Star intel",
    long_description_content_type="text/markdown",
    url="https://github.com/lost-rob0t/starintel-doc",
    packages=find_packages(),
    install_requires=["ulid-py", "dataclasses-json"],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
)
