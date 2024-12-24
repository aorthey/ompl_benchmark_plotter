from setuptools import setup, find_packages

with open('README.md', 'r') as fh:
  long_description = fh.read()

setup(
    name='ompl_benchmark_plotter',
    version='0.1.0',
    author='Andreas Orthey',
    author_email='aorthey@rtr.ai',
    description='A simple tool to plot OMPL benchmark results',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/aorthey/ompl_benchmark_plotter',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'numpy==1.24.3',
        'matplotlib==3.7.1',
        'argparse==1.4.0'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    python_requires='>=3.6',
)

