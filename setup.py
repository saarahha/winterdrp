import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="winterdrp",
    version="0.0.1",
    author="Viraj Karambelkar, Robert Stein",
    author_email="rdstein@caltech.edu",
    description="Data reduction pipeline for WINTER",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    keywords="astronomy image WINTER",
    url="https://github.com/viraj21197/winter_drp",
    packages=setuptools.find_packages(),
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires='>=3.10',
    install_requires=[
        "astropy",
        "astroquery",
        "jupyter",
        "matplotlib",
        "numpy",
        "docker"
    ]
)