from setuptools import setup

setup(
    name="taskmanager",
    version="0.1",
    packages=[''],
    package_dir={'': '.'},
    install_requires=[
        'flask',
        'flask-sqlalchemy',
        'flask-jwt-extended'
    ],
)