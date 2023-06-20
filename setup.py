from setuptools import setup

setup(
    name='reliableGPT',
    version='0.1.2',
    description='Error handling and auto-retry library for GPT',
    author='Ishaan Jaffer',
    packages=['reliablegpt'],
    install_requires=[
        'openai',
        'termcolor',
        'klotty'
    ],
)
