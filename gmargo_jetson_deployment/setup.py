from setuptools import find_packages
from distutils.core import setup

setup(
    name='jetsondeploy',
    version='1.0.0',
    author='Gabe Margolis',
    license="BSD-3-Clause",
    packages=find_packages(),
    author_email='gmargo@mit.edu',
    description='Deployment Code for Legged Robots on Jetson TX2',
    install_requires=[#'isaacgym',
                      #'matplotlib',
                      #'gym',
                      #'ml_logger',
                      ]
)
