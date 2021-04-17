from aws_cdk import (core as cdk, aws_lambda as _lambda, aws_dynamodb as _ddb)


class AppConstruct(cdk.Construct):
    def __init__(self, scope: cdk.Construct, construct_id: str, _fn1: _lambda.Function, _fn2: _lambda.Function,
                 _db: _ddb.ITable,
                 **kwargs) -> None:
        super().__init__(scope, construct_id)

        _fn1.add_environment("TABLE_NAME", _db.table_name)
        _fn1.add_environment("DOMAIN_URL", "manu.c")
        _fn1.add_environment("EXPIRY_TIME", "86400")

        _fn2.add_environment("TABLE_NAME",_db.table_name)

        _db.grant_read_write_data(_fn1)
        _db.grant_read_write_data(_fn2)

        _fn1.grant_invoke
