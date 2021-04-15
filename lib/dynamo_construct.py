from aws_cdk import (core, aws_dynamodb as _ddb)

from aws_cdk.aws_dynamodb import (BillingMode, Table, Attribute, AttributeType,
                                  ITable)


class DbConstruct(core.Construct):
    def __init__(self, scope: core.Construct, construct_id: str,
                 db_context: str, **kwargs) -> None:
        super().__init__(scope, construct_id)

        # setting the db context
        db = dict(self.node.try_get_context(db_context))

        # Shortening some of the logic
        billing_mode = BillingMode.PROVISIONED if db[
            "db_billing_mode"] == "provisioned" else BillingMode.PAY_PER_REQUEST
        pk = db["db_table_pk"]
        pk_type = AttributeType.STRING if db[
            "db_table_pk_type"] == "string" else AttributeType.NUMBER

        table = Table(
            self,
            db["db_table"],
            table_name=db["db_table"],
            partition_key=Attribute(name=pk, type=pk_type),
            read_capacity=db["db_min_read_capacity"],
            write_capacity=db["db_min_write_capacity"],
            encryption=_ddb.TableEncryption.AWS_MANAGED,
            point_in_time_recovery=True,
            removal_policy=core.RemovalPolicy.DESTROY,
            billing_mode=billing_mode,
        )

        # Add read/write autoscaling enabled at X% utilization
        if db["db_billing_mode"] == "provisioned" and db[
                "db_enable_autoscaling"]:
            read_scaling = table.auto_scale_read_capacity(
                min_capacity=db["db_min_read_capacity"],
                max_capacity=db["db_max_read_capacity"],
            )

            read_scaling.scale_on_utilization(
                target_utilization_percent=db["db_target_utilization"], )
            write_scaling = table.auto_scale_write_capacity(
                min_capacity=db["db_min_write_capacity"],
                max_capacity=db["db_max_write_capacity"],
            )
            write_scaling.scale_on_utilization(
                target_utilization_percent=db["db_target_utilization"], )

        self.table = table

    @property
    def main_table(self) -> ITable:
        return self.table
