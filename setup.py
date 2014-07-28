# -*- coding:utf-8 -*-

from setuptools import setup, find_packages

install_requires = [
    'django',
    'django-storages'
    'boto',
    'requests'
]

setup(
    name='cloud-sync',
    version='0.0.1',
    author='cogenda-dev-team',
    author_email='support@cogenda.com',
    url='http://cogenda.com',
    packages=find_packages(exclude=['tests', 'test_*']), 
    install_requires=install_requires,
    zip_safe=False,
    include_package_data=True,
    **kwargs
)




