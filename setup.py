"""Setup script for odoo-ule-handler"""

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    README = readme_file.read()

# This call to setup() does all the work
setup_args = dict(
    name="odoo-ule-handler",
    version="0.0.9",
    description="Get ULE's Odoo data",
    long_description=README,
    long_description_content_type="text/markdown",
    license="MIT",
    packages=find_packages(),
    author="Aitor Iturrioz",
    author_email="iraiturrioz@lhusurbil.eus",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3"
    ],
    url='https://github.com/Usurbilgo-Lanbide-Eskola/odoo-ule-handler',
    download_url='https://pypi.org/project/odoo-ule-handler/'
)

install_requires = []

if __name__ == '__main__':
    setup(install_requires=install_requires, **setup_args)