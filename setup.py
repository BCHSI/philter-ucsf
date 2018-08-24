import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="philter-ucsf-beta",
    version="0.0.1",
    author="Beau Norgeot",
    author_email="beaunorgeot@gmail.com",
    description="An open-source PHI-filtering software",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/beaunorgeot/philter-ucsf-beta",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)