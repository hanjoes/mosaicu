import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="mosaicu",
    version="0.0.1",
    author="hanjoes",
    author_email="hanzhou87@gmail.com",
    description="Mosaic an input picture.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hanjoes/mosaicu",
    py_modules=["mosaicu"],
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)