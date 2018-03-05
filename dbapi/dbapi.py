# coding: utf-8
"""
Module which contains the API class.
"""

import csv
import time
import datetime
import StringIO
import calendar
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

    def get_columns_from_description(self, description):
        """
        Get the list of columns reading the API description.
        Args:
            description (dict): The API description.

        Returns:
            (list of tuples): List of fields (name, type).
        """
        columns = []
        for field in description.get(u"fields"):
            if u"nested_description" in field:
                columns += self.get_columns_from_description(field[u"nested_description"])
            else:
                column_name = field.get(u"name")
                if description.get(u"table") != self._collection._table.name:
                    column_name = u".".join(description.get(u"as").split(u".") + [column_name])
                columns.append((column_name, field.get(u"type")))

        return columns

    def export(self, filter=None, projection=None, lookup=None, auto_lookup=None, order=None, order_by=None):
        output = StringIO.StringIO()
        encoding = u"utf-8"
        # Open parsers
        writer = csv.writer(
            output,
            delimiter="\t"
        )
        description = self._collection.get_description(lookup, auto_lookup)
        col_desc = self.get_columns_from_description(description)
        print(col_desc)

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
                value = item.get(col_name)
                if col_typ == u"datetime":
                    value = datetime.datetime.utcfromtimestamp(
                        int(value)
                    ).strftime(u'%Y-%m-%d %H:%M:%S')
                line.append(unicode(value).encode(encoding))

            writer.writerow(line)

        return output.getvalue()

    def get(self, id, lookup=None, auto_lookup=None):
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

    def create(self, document, lookup=None, auto_lookup=None):
        """
        Create an item.
        Args:
            item (dict): The JSON representation of the Item to create.
            lookup (list of dict): Lookup option (joins).
            auto_lookup (int): Let the database construct the lookups (value is the deep).

        Returns:
            (dict): The result of the created item operation (with created ID).
        """
        self.before(u"create")
        try:
            result = self._collection.insert_one(document, lookup, auto_lookup)
        except IntegrityError:
            raise ApiUnprocessableEntity(U"Error at item creation.")
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

    def delete(self, filter, lookup=None, auto_lookup=None):
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
            raise ApiUnprocessableEntity(U"Error at item(s) deletion.")
        return {
            u"deleted_count": int(result.deleted_count)
        }

    def update(self, filter, update, lookup=None, auto_lookup=None):
        """
        Update item(s).
        Args:
            filter (dict): Filter to know what to delete.
            update (dict): Fields to update.
            lookup (list of dict): Lookup option (joins).
            auto_lookup (int): Let the database construct the lookups (value is the deep).

        Returns:
            (dict): The result of the deletion (with number of items deleted).
        """
        self.before(u"update")
        try:
            result = self._collection.update_many(filter, update, lookup, auto_lookup)
        except IntegrityError:
            raise ApiUnprocessableEntity(U"Error at item(s) update.")

        return {
            u"matched_count": int(result.matched_count)
        }

    def list(self, filter=None, projection=None, lookup=None, auto_lookup=None, order=None, order_by=None, offset=0,
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
