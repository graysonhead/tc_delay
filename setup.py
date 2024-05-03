import setuptools

setuptools.setup(
    name="tc_delay",
    version="0.0.1",
    author="Grayson Head",
    author_email="grayson@graysonhead.net",
    packages=setuptools.find_packages(),
    install_requires=[
        "PyYAML<=5.3.1"
    ],
    python_requires='>=3.5, <4',
    entry_points={
        "console_scripts": [
            'tc_delay = tc_delay.__main__:main'
        ]
    }
)