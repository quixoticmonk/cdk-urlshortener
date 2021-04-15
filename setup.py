import setuptools

setuptools.setup(
    name="urlshortener",
    version="0.0.1",

    author="Manu Chandrasekhar",

    package_dir={"": "lib"},
    packages=setuptools.find_packages(where="lib"),
    install_requires=[
        "aws-cdk.core==1.98.0",
        "aws-cdk.core==1.98.0",
        "aws-cdk.aws-dynamodb==1.98.0",
        "aws-cdk.aws-apigateway==1.98.0",
        "aws-cdk.aws-lambda==1.98.0",
        "aws-cdk.aws-lambda-event-sources==1.98.0"
    ],

)
