from distutils.core import setup

setup(
    name='excesiv',
    version='0.1.0dev',
    author='Nicolas Hery',
    author_email='nicolahery@gmail.com',
    url='http://github.com/nicolahery/excesiv',
    license='MIT',
    description='Application component to generate and read Excel files '
                'using Apache POI',
    packages=['excesiv',],
    install_requires=[
        "Flask>=0.9",
        "pymongo>=2.3"
    ],
)
