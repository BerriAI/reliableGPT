from setuptools import setup, find_packages

setup(
    name='reliableGPT',
<<<<<<< HEAD
    version='0.2.9933',
=======
    version='0.2.995',
>>>>>>> 2d14e98f98c2099bc6a19d040dc42c427966768d
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
