from setuptools import setup, find_packages

setup(
    name='reliableGPT',
    version='0.2.9933',
    description='Error handling and auto-retry library for GPT',
    author='Ishaan Jaffer',
    packages=[
        'reliablegpt'
    ],
    install_requires=[
        'openai',
        'termcolor',
        'klotty',
        'numpy',
        'posthog',
        'tiktoken',
        'resend',
        'waitress'
    ],
)
