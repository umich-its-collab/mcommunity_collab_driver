from setuptools import find_packages, setup

setup(
    name='mcommunity_collab_driver',
    packages=find_packages(include=['mcommunity_collab_driver']),
    description='Python library for using the MCommunity Gateway',
    version='0.1.0',
    author='Richard Sawoscinski',
    install_requires=['requests'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    test_suite='tests',
)
