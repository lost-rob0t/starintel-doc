from setuptools import setup, find_packages


setup(
    name="starintel_doc",
    version="0.5.0",
    description="Document Spec for Star intel",
    long_description_content_type="text/markdown",
    url="https://gitlab.com/unseen-giants/starintel_doc",
    author="Nsaspy",
    license="MIT",
    py_modules=["starintel_doc", "star_exceptions"],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
)
