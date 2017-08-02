import setuptools

long_description = 'Solution tester for programming contests'
setuptools.setup(
    name='hazmat',
    version='0.1',
    description='Solution tester for programming contests',
    long_description=long_description,
    author='Xeoeen',
    license='MIT',
    python_requires='>=3',
    packages=setuptools.find_packages(),
    scripts=['bin/hazmat'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Solution testing',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    include_package_data=True,
    url='https://github.com/Xeoeen/hazmat',
    zip_safe=True)
