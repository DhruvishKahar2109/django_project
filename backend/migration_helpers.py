from django.db import connection


def move_column_after(table_name, column_name, after_column):
    with connection.cursor() as cursor:

        # Existing columns check
        columns = [
            column.name
            for column in connection.introspection.get_table_description(
                cursor,
                table_name
            )
        ]

        # Table/column exist nahi karta to kuch mat karo
        if column_name not in columns:
            return

        if after_column not in columns:
            return

        cursor.execute(
            f"""
            ALTER TABLE `{table_name}`
            MODIFY COLUMN `{column_name}` BIGINT NULL
            AFTER `{after_column}`
            """
        )