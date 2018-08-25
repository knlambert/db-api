# coding: utf-8
"""
Module which contains the API class.
"""

import csv
import datetime
import io
import calendar
import sqlcollection
from typing import List, Dict, Tuple
from cerberus import Validator
from .utils import json_to_one_level
from sqlcollection.exception import IntegrityError
from .api_exception import ApiUnprocessableEntity, ApiNotFound


class DBApi(object):
    """
    This class implement a base API. Others are inherited from this one.
    It brings a default implementation of methods to forward direct 
    interaction with DB classes.
    """

    def __init__(
        self,
        client: sqlcollection.client.Client,
        table_name: str,
        database_name: str = None,
        prefix: str = None
    ):
        """
        This is the constructor of the API Class.
        Args:
            client (sqlcollection.client.Clien): Client class to 
                communicate with DB.
            table_name (str): The name of the table to communicate 
                with.
            database_name (str): The name of the DB where the table 
                can be found.
            prefix (str): The prefix corresponding to the name of the dynamic
                databased used for each tenant.
        """
        self._client = client
        self._table_name = table_name
        self._database_name = database_name
        self._prefix = prefix

    def before(self, method_name):
        pass

    def _get_collection(self, customer_id: int = None):
        """
        Construct the DB object to connect to the table DB.
        Args:
            customer_id (int): The name of the customer.
        Returns:
            (sqlcollection.db.DB): The DB object generated.
        """
        db = getattr(
            self._client,
            (self._database_name or "{}{}".format(self._prefix, customer_id))
        )
        return getattr(db, self._table_name)

    @staticmethod
    def _get_timestamp_coerce(type_):
        """
        Returns a method to convert a timestamp into a date or into
        a datetime.
        Used to define the validation schema for the API.
        Args:
            type_ (str): The name of the type to convert into.

        Returns:
            (callable): The generated function.
        """
        def convert(timestamp):
            converted = datetime.datetime.utcfromtimestamp(int(timestamp))
            if type_ == "date":
                return converted.date()

            return converted

        return convert

    def get_validation_schema(
        self,
        description: Dict, 
        is_root: bool = True, 
        is_update: bool = False,
        deep_update: bool = True
    ) -> List[Tuple[str, str]]:
        """
        Get the list of columns reading the API description.
        Args:
            description (Dict): The API description.
            is_root (bool): If the description corresponds to the root
                collection (differs on how autoincrement are handled).
            is_update (bool): If the validation correspond to an update
                operation.
            deep_update (bool): Allows or not to perform an update on sub
                fields.

        Returns:
            (List[Tuple[str, str]]): List of fields (name, type).
        """
        schema = {}
        for field in description.get("fields"):
            is_foreign_field = (
                field["name"] == description.get("foreignField", False)
            )

            if is_root or is_foreign_field or (is_update and deep_update):
                rule = {
                    "type": field["type"],
                    "nullable": field["nullable"]
                }
                is_required = not field["nullable"]

                if is_update:  # If update, nothing is required.
                    is_required = False

                else:  # If insert
                    # If insert on the root table and has autoincrement,
                    # not nullable, but not required.
                    if (
                        is_root and
                        field.get("autoincrement", False) and
                        not is_foreign_field
                    ):
                        is_required = False
                    elif not is_root and is_foreign_field:
                        is_required = True
                    elif not is_root:
                        is_required = False

                rule["required"] = is_required

                if field["type"] in ["datetime", "date"]:
                    rule["type"] = field["type"]
                    rule["coerce"] = self._get_timestamp_coerce(field["type"])

                elif "nested_description" in field:
                    rule["type"] = "dict"
                    rule["required"] = not is_update

                    # If it's an insert or not a deep update.
                    if not is_update or not deep_update:
                        rule["purge_unknown"] = True

                    rule["schema"] = self.get_validation_schema(
                        description=field["nested_description"],
                        is_root=False,
                        is_update=is_update,
                        deep_update=deep_update
                    )

                schema[field["name"]] = rule

        return schema

    def _get_columns_name_types_from_description(
        self,
        description: Dict,
        parent: List[str] = None
    ) -> List[Tuple[str, str]]:
        """
        Return a list of columns with their types from the description.
        Args:
            description (Dict): The description to analyse.
            parent (List[str]): The parent prefix if there is one.
        Returns:
            (List[Tuple[str, str]]: A list of tuples column name / type.
        """
        result = []
        parent = parent or []

        for field in description.get("fields", []):
            if "nested_description" in field:
                result.extend(self._get_columns_name_types_from_description(
                    field.get("nested_description"),
                    parent + [field.get("name")]
                ))
            else:
                result.append(
                    (".".join(parent + [field.get("name")]), field.get("type"))
                )

        return result

    def export(
        self,
        filter=None, 
        projection=None, 
        lookup=None, 
        auto_lookup=0, 
        order=None, 
        order_by=None, 
        database_name: str = None
    ):
        output = io.StringIO()
        encoding = "utf-8"
        # Open parsers
        writer = csv.writer(
            output,
            delimiter="\t"
        )
        collection = self._get_collection(database_name)
        description = collection.get_description(lookup, auto_lookup)
        col_desc = self._get_columns_name_types_from_description(description)

        def fetch(offset):
            return self.list(
                filter,
                projection,
                lookup,
                auto_lookup,
                order,
                order_by,
                limit=100,
                offset=offset
            )

        def fetch_iterator():
            offset = 0
            result = fetch(offset)
            while offset == 0 or result.get("has_next"):
                result = fetch(offset)
                for item in result.get("items"):
                    yield json_to_one_level(item)
                offset += 100

            raise StopIteration

        writer.writerow([col[0].encode(encoding) for col in col_desc])

        for item in fetch_iterator():
            line = []
            for col_name, col_typ in col_desc:
                value = item.get(col_name) or ""
                if col_typ == "datetime":
                    value = datetime.datetime.utcfromtimestamp(
                        int(value)
                    ).strftime('%Y-%m-%d %H:%M:%S')
                line.append(value)

            writer.writerow(line)

        return output.getvalue()

    def get(
        self,
        id: int,
        lookup: List[Dict] = None,
        auto_lookup: int = 0,
        database_name: str = None
    ) -> Dict:
        """
        Get an item from ID.
        Args:
            id (int): The id of the item to fetch.
            lookup (List[Dict]): Lookup option (joins).
            auto_lookup (int): Let the database constructs
                the lookups (value is the deep).
            database_name (str): The name of the database to use.
        Returns:
            (Dict): The object fetched.
        """
        self.before("get")
        collection = self._get_collection(database_name)
        items = list(collection.find(
            {"id": id}, lookup=lookup, auto_lookup=auto_lookup)
        )
        if len(items) == 1:
            return items[0]
        raise ApiNotFound

    def validate(
        self,
        document: Dict,
        lookup: List[Dict],
        auto_lookup: int = 0,
        is_update: bool = False,
        deep_update: bool = False,
        database_name: str = None
    ) -> Dict:
        """
        Validate a document regarding the database.
        Args:
            document (Dict): The JSON representation of the Item.
            lookup (List[Dict]): Lookup option (joins).
            auto_lookup (int): Let the database construct the
                lookups (value is the deep).
            is_update (bool): If the validation correspond
                to an update operation.
            deep_update (bool): Allows or not to perform an
                update on sub fields.
            database_name (str): The name of the database to use.

        Returns:
            (Dict): The formatted document.

        Raises:
            ApiUnprocessableEntity: If the document doesn't comply to the 
                required format.
        """
        collection = self._get_collection(database_name)
        description = collection.get_description(
            lookup=lookup,
            auto_lookup=auto_lookup
        )
        validation_schema = self.get_validation_schema(
            description, is_update=is_update, deep_update=deep_update
        )
        validator = Validator(validation_schema)
        if not validator.validate(document):
            raise ApiUnprocessableEntity(
                message="The payload format is wrong.",
                api_error_code="WRONG_PAYLOAD_FORMAT",
                payload=validator.errors
            )
        return validator.document

    def create(
        self,
        document: Dict,
        lookup: List[Dict] = None,
        auto_lookup: int = 0,
        database_name: str = None
    ) -> Dict:
        """
        Create an item.
        Args:
            document (Dict): The JSON representation of the 
                Item to create.
            lookup (List[Dict]): Lookup option (joins).
            auto_lookup (int): Let the database construct the lookups (value is
                the deep).
            database_name (str): The name of the database to use.

        Returns:
            (Dict): The result of the created item operation (with created ID).
        """
        self.before("create")
        try:
            document = self.validate(
                document, 
                lookup, 
                auto_lookup, 
                database_name=database_name
            )
            collection = self._get_collection(database_name)
            result = collection.insert_one(document, lookup, auto_lookup)
        except IntegrityError:
            raise ApiUnprocessableEntity(
                "Integrity error.",
                api_error_code="INTEGRITY_ERROR"
            )
        return {
            "inserted_id": result.inserted_id
        }

    def description(
        self,
        lookup: List[Dict] = None,
        auto_lookup: int = 0,
        database_name: str = None
    ) -> Dict:
        """
        Get the description of the table (fields & relations).
        Args:
            lookup (List[Dict]): Lookup option (joins).
            auto_lookup (int): Let the database construct the lookups (value is 
                the deep).
            database_name (str): The name of the database to use.

        Returns:
            (Dict): The description.
        """
        self.before("description")
        collection = self._get_collection(database_name)
        return collection.get_description(lookup, auto_lookup)

    def validation_schema(
        self,
        lookup: List[Dict] = None,
        auto_lookup: int = 0,
        is_update: bool = False,
        database_name: str = None
    ):
        """
        Get the schema of the table (fields & relations).
        Args:
            lookup (List[Dict]): Lookup option (joins).
            auto_lookup (int): Let the database construct the lookups (value is
            the deep).
            is_update (bool): If the validation is for the specific update case
                or not.
            database_name (str): The name of the database to use.

        Returns:
            (Dict): The description.
        """
        self.before("description")
        collection = self._get_collection(database_name)
        description = collection.get_description(lookup, auto_lookup)
        return self.get_validation_schema(
            description,
            is_update
        )

    def delete(
        self,
        filter: Dict,
        lookup: List[Dict] = None,
        auto_lookup: int = 0,
        database_name: str = None
    ):
        """
        Delete item(s).
        Args:
            filter (Dict): Filter to know what to delete.
            lookup (List[Dict]): Lookup option (joins).
            auto_lookup (int): Let the database construct the lookups (value is
                the deep).
            database_name (str): The name of the database to use.

        Returns:
            (Dict): The result of the deletion (with number of items deleted).
        """
        self.before("delete")
        try:
            collection = self._get_collection(database_name)
            result = collection.delete_many(filter, lookup, auto_lookup)
        except IntegrityError:
            raise ApiUnprocessableEntity(
                "Integrity error.",
                api_error_code="INTEGRITY_ERROR"
            )
        return {
            "deleted_count": int(result.deleted_count)
        }

    def update(
        self,
        filter: Dict,
        update: Dict,
        lookup: List[Dict] = None,
        auto_lookup: int = 0,
        deep_update: bool = False,
        database_name: str = None
    ):
        """
        Update item(s).
        Args:
            filter (Dict): Filter to know what to delete.
            update (Dict): Fields to update.
            lookup (List[Dict]): Lookup option (joins).
            auto_lookup (int): Let the database construct the lookups 
                (value is the deep).
            deep_update (bool): Allows or not to perform an update on sub 
                fields.
            database_name (str): The name of the database to use.

        Returns:
            (Dict): The result of the deletion (with number of items deleted).
        """
        self.before("update")
        try:
            update["$set"] = self.validate(
                update["$set"],
                lookup,
                auto_lookup,
                is_update=True,
                deep_update=deep_update
            )
            collection = self._get_collection(database_name)
            result = collection.update_many(
                filter, 
                update, 
                lookup, 
                auto_lookup
            )
        except IntegrityError:
            raise ApiUnprocessableEntity(
                "Integrity error.",
                api_error_code="INTEGRITY_ERROR"
            )

        return {
            "matched_count": int(result.matched_count)
        }

    def list(
        self,
        filter: Dict = None,
        projection: Dict = None,
        lookup: List[Dict]= None,
        auto_lookup: int = 0,
        order: List[str] = None,
        order_by: List[int] = None,
        offset: int = 0,
        limit: int = 100,
        database_name: str = None
    ):
        self.before("list")
        order = order or []
        order_by = order_by or []

        collection = self._get_collection(database_name)
        items = list(collection.find(**{
            "query": filter,
            "projection": projection,
            "lookup": lookup,
            "auto_lookup": auto_lookup
        }).sort(order, order_by).skip(offset).limit(limit + 1))

        has_next = len(items) > limit

        if has_next:
            del items[-1]

        return {
            "items": self._convert_python_types(items),
            "offset": offset,
            "limit": limit,
            "has_next": has_next
        }

    def _convert_python_types(self, items):
        """
        Process a List[Dict] to convert the python type into API friendly ones.
        Args:
            items (List[Dict]): The array to process.

        Returns:
            (List[Dict]): The List[Dict] with converted types.
        """
        for index, _ in enumerate(items):
            for key in items[index]:

                if isinstance(items[index][key], datetime.datetime):
                    items[index][key] = int(
                        (items[index][key] - datetime.datetime(
                            1970, 1, 1)).total_seconds())

                elif isinstance(items[index][key], datetime.date):
                    items[index][key] = int(
                        calendar.timegm(items[index][key].timetuple())
                    )

                elif isinstance(items[index][key], dict):
                    items[index][key] = self._convert_python_types(
                        [items[index][key]]
                    )[0]
        return items

    def get_flask_adapter(self, flask_user_api):
        """
        Get an adapter for the API.
        Args:
            flask_user_api: The user api used to check roles.
        Returns:
            (FlaskAdapter): The adapter.
        """
        from .adapter.flask_adapter import FlaskAdapter
        return FlaskAdapter(self, flask_user_api)
