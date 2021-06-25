# ODOO ULE HANDLER

Internal script to read Odoo's DB data


# Release process

This repository is not linked to the PyPi repository (https://pypi.org/project/odoo-ule-handler/), so new versions must be manually created and deployed.
The process is really simple: clone the GitHub repository and execute the following command:

> Warning: you should use a virtual enviroment for dependency/library management.

- pip install twine

- python setup.py sdist bdist_wheel

- twine upload dist/*

Introduce the PyPi account credentials and you are done.


# License

Everything in this repository is licensed under the MIT license.