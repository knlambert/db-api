# coding: utf-8
"""
Module which contains the API class.
"""

import csv
import datetime
import StringIO
import calendar
from cerberus import Validator
from .utils import json_to_one_level
from sqlcollection.exception import IntegrityError
from .api_exception import ApiUnprocessableEntity, ApiNotFound


class DBApi(object):
    """
    This class implement a base API. Others are inherited from this one.
    It brings a default implementation of methods to forward direct interaction with
    DB classes.
    """

    def __init__(self, db, table_name):
        """
        This is the constructor of the API Class.
        Args:
            db (DB): Client class to communicate with DB.
            table_name (unicode): The name of the table to communicate with.
        """
        self._db = db
        self._collection = getattr(self._db, table_name)

    def before(self, method_name):
        pass

    @staticmethod
    def _get_timestamp_coerce(type_):
        """
        Returns a method to convert a timestamp into a date or into
        a datetime.
        Used to define the validation schema for the API.
        Args:
            type_ (unicode): The name of the type to convert into.

        Returns:
            (callable): The generated function.
        """
        def convert(timestamp):
            converted = datetime.datetime.utcfromtimestamp(int(timestamp))
            if type_ == u"date":
                return converted.date()

            return converted

        return convert

    def get_validation_schema_from_description(self, description, is_root=True, is_update=False, deep_update=True):
        """
        Get the list of columns reading the API description.
        Args:
            description (dict): The API description.
            is_root (boolean): If the description corresponds to the root collection (differs on how autoincrement
                are handled).
            is_update (boolean): If the validation correspond to an update operation.
            deep_update (boolean): Allows or not to perform an update on sub fields.

        Returns:
            (list of tuples): List of fields (name, type).
        """
        schema = {}
        for field in description.get(u"fields"):
            is_foreign_field = (field[u"name"] == description.get(u"foreignField", False))

            if is_root or is_foreign_field or (is_update and deep_update):
                rule = {
                    u"type": field[u"type"],
                    u"nullable": field[u"nullable"]
                }
                is_required = not field[u"nullable"]

                if is_update:  # If update, nothing is required.
                    is_required = False

                else:  # If insert
                    # If insert on the root table and has autoincrement, not nullable, but not required.
                    if is_root and field.get(u"autoincrement", False) and not is_foreign_field:
                        is_required = False
                    elif not is_root and is_foreign_field:
                        is_required = True
                    elif not is_root:
                        is_required = False

                rule[u"required"] = is_required

                if field[u"type"] in [u"datetime", u"date"]:
                    rule[u"type"] = field[u"type"]
                    rule[u"coerce"] = self._get_timestamp_coerce(field[u"type"])

                elif u"nested_description" in field:
                    rule[u"type"] = u"dict"
                    rule[u"required"] = not is_update

                    # If it's an insert or not a deep update.
                    if not is_update or not deep_update:
                        rule[u"purge_unknown"] = True

                    rule[u"schema"] = self.get_validation_schema_from_description(
                        description=field[u"nested_description"],
                        is_root=False,
                        is_update=is_update,
                        deep_update=deep_update
                    )

                schema[field[u"name"]] = rule

        return schema

    def _get_columns_name_types_from_description(self, description, parent=None):
        """
        Return a list of columns with their types from the description.
        Args:
            description (dict): The description to analyse.
            parent (list of unicode): The parent prefix if there is one.
        Returns:
            (list of (unicode, unicode): A list of tuples column name / type.
        """
        result = []
        parent = parent or []

        for field in description.get(u"fields", []):
            if u"nested_description" in field:
                result.extend(self._get_columns_name_types_from_description(
                    field.get(u"nested_description"),
                    parent + [field.get(u"name")]
                ))
            else:
                result.append((u".".join(parent + [field.get(u"name")]), field.get(u"type")))

        return result

    def export(self, filter=None, projection=None, lookup=None, auto_lookup=0, order=None, order_by=None):
        output = StringIO.StringIO()
        encoding = u"utf-8"
        # Open parsers
        writer = csv.writer(
            output,
            delimiter="\t"
        )
        description = self._collection.get_description(lookup, auto_lookup)
        col_desc = self._get_columns_name_types_from_description(description)

        def fetch(offset):
            return self.list(filter, projection, lookup, auto_lookup, order, order_by, limit=100, offset=offset)

        def fetch_iterator():
            offset = 0
            while offset == 0 or result.get(u"has_next"):
                result = fetch(offset)
                for item in result.get(u"items"):
                    yield json_to_one_level(item)
                offset += 100

            raise StopIteration

        writer.writerow([col[0].encode(encoding) for col in col_desc])

        for item in fetch_iterator():
            line = []
            for col_name, col_typ in col_desc:
                value = item.get(col_name) or u""
                if col_typ == u"datetime":
                    value = datetime.datetime.utcfromtimestamp(
                        int(value)
                    ).strftime(u'%Y-%m-%d %H:%M:%S')
                line.append(unicode(value).encode(encoding))

            writer.writerow(line)

        return output.getvalue()

    def get(self, id, lookup=None, auto_lookup=0):
        """
        Get an item from ID.
        Args:
            id (int): The id of the item to fetch.
            lookup (list of dict): Lookup option (joins).
            auto_lookup (int): Let the database construct the lookups (value is the deep).
        """
        self.before(u"get")
        items = list(self._collection.find({u"id": id}, lookup=lookup, auto_lookup=auto_lookup))
        if len(items) == 1:
            return items[0]
        raise ApiNotFound

    def validate(self, document, lookup, auto_lookup, is_update=False, deep_update=False):
        """
        Validate a document regarding the database.
        Args:
            document (dict): The JSON representation of the Item.
            lookup (list of dict): Lookup option (joins).
            auto_lookup (int): Let the database construct the lookups (value is the deep).
            is_update (boolean): If the validation correspond to an update operation.
            deep_update (boolean): Allows or not to perform an update on sub fields.

        Returns:
            (dict): The formatted document.

        Raises:
            ApiUnprocessableEntity: If the document doesn't comply to the required format.
        """
        description = self._collection.get_description(lookup=lookup, auto_lookup=auto_lookup)
        validation_schema = self.get_validation_schema_from_description(
            description, is_update=is_update, deep_update=deep_update
        )
        validator = Validator(validation_schema)
        if not validator.validate(document):
            raise ApiUnprocessableEntity(
                message=u"The payload format is wrong.",
                api_error_code=u"WRONG_PAYLOAD_FORMAT",
                payload=validator.errors
            )
        return validator.document

    def create(self, document, lookup=None, auto_lookup=0):
        """
        Create an item.
        Args:
            document (dict): The JSON representation of the Item to create.
            lookup (list of dict): Lookup option (joins).
            auto_lookup (int): Let the database construct the lookups (value is the deep).

        Returns:
            (dict): The result of the created item operation (with created ID).
        """
        self.before(u"create")
        try:
            document = self.validate(document, lookup, auto_lookup)
            result = self._collection.insert_one(document, lookup, auto_lookup)
        except IntegrityError:
            raise ApiUnprocessableEntity(U"Integrity error.", api_error_code=u"INTEGRITY_ERROR")
        return {
            u"inserted_id": result.inserted_id
        }

    def description(self, lookup=None, auto_lookup=0):
        """
        Get the description of the table (fields & relations).
        Args:
            lookup (list of dict): Lookup option (joins).
            auto_lookup (int): Let the database construct the lookups (value is the deep).

        Returns:
            (dict): The description.
        """
        self.before(u"description")
        return self._collection.get_description(lookup, auto_lookup)

    def validation_schema(self, lookup=None, auto_lookup=0, is_update=False):
        """
        Get the schema of the table (fields & relations).
        Args:
            lookup (list of dict): Lookup option (joins).
            auto_lookup (int): Let the database construct the lookups (value is the deep).

        Returns:
            (dict): The description.
        """
        self.before(u"description")
        description = self._collection.get_description(lookup, auto_lookup)
        return self.get_validation_schema_from_description(description, is_update)

    def delete(self, filter, lookup=None, auto_lookup=0):
        """
        Delete item(s).
        Args:
            filter (dict): Filter to know what to delete.
            lookup (list of dict): Lookup option (joins).
            auto_lookup (int): Let the database construct the lookups (value is the deep).

        Returns:
            (dict): The result of the deletion (with number of items deleted).
        """
        self.before(u"delete")
        try:
            result = self._collection.delete_many(filter, lookup, auto_lookup)
        except IntegrityError:
            raise ApiUnprocessableEntity(U"Integrity error.", api_error_code=u"INTEGRITY_ERROR")
        return {
            u"deleted_count": int(result.deleted_count)
        }

    def update(self, filter, update, lookup=None, auto_lookup=0, deep_update=False):
        """
        Update item(s).
        Args:
            filter (dict): Filter to know what to delete.
            update (dict): Fields to update.
            lookup (list of dict): Lookup option (joins).
            auto_lookup (int): Let the database construct the lookups (value is the deep).
            deep_update (boolean): Allows or not to perform an update on sub fields.

        Returns:
            (dict): The result of the deletion (with number of items deleted).
        """
        self.before(u"update")
        try:
            update[u"$set"] = self.validate(update[u"$set"], lookup, auto_lookup, is_update=True, deep_update=deep_update)
            result = self._collection.update_many(filter, update, lookup, auto_lookup)
        except IntegrityError:
            raise ApiUnprocessableEntity(U"Integrity error.", api_error_code=u"INTEGRITY_ERROR")

        return {
            u"matched_count": int(result.matched_count)
        }

    def list(self, filter=None, projection=None, lookup=None, auto_lookup=0, order=None, order_by=None, offset=0,
             limit=100):
        self.before(u"list")
        order = order or []
        order_by = order_by or []

        

        items = list(self._collection.find(**{
            u"query": filter,
            u"projection": projection,
            u"lookup": lookup,
            u"auto_lookup": auto_lookup
        }).sort(order, order_by).skip(offset).limit(limit + 1))

        has_next = len(items) > limit

        if has_next:
            del items[-1]

        return {
            u"items": self._convert_python_types(items),
            u"offset": offset,
            u"limit": limit,
            u"has_next": has_next
        }

    def _convert_python_types(self, items):
        """
        Process a list of dict to convert the python type into API friendly ones.
        Args:
            items (list of dict): The array to process.

        Returns:
            (list of dict): The list of dict with converted types.
        """
        for index, item in enumerate(items):
            for key in items[index]:

                if isinstance(items[index][key], datetime.datetime):
                    items[index][key] = int((items[index][key] - datetime.datetime(1970, 1, 1)).total_seconds())

                elif isinstance(items[index][key], datetime.date):
                    items[index][key] = int(calendar.timegm(items[index][key].timetuple()))

                elif isinstance(items[index][key], dict):
                    items[index][key] = self._convert_python_types([items[index][key]])[0]
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
