# coding: utf-8
"""
Module which contains the API class.
"""

import csv
import StringIO
from datetime import datetime
from .utils import json_to_one_level
from .api_exception import ApiForbidden, ApiUnauthorized, ApiNotFound


class Api(object):
    """
    This class implement a base API. Others are inherited from this one.
    It brings a default implementation of methods to forward direct interaction with
    DB classes.
    """

    def __init__(self, db, default_table_name):
        """
        This is the constructor of the API Class.
        Args:
            db (DB): Client class to communicate with DB.
            default_table_name (unicode): Name of the default table interrogated by the API.
        """
        self._db = db
        self._db = getattr(self._db, default_table_name)

    def before(self, method_name):
        pass

    def get_columns_from_description(self, description, parent=None):
        columns = []
        for field in description.get(u"fields"):
            if u"nested_description" in field:
                columns += self.get_columns_from_description(field[u"nested_description"], field.get(u"as"))
            else:
                column_name = field.get(u"name")
                if parent:
                    column_name = u".".join(parent.split(u".") + [field.get(u"name")])
                columns.append((column_name, field.get(u"type")))

        return columns

    def export(self, filters=None, projection=None, lookup=None, auto_lookup=None, order=None, order_by=None):
        output = StringIO.StringIO()
        encoding = u"utf-8"
        # Open parsers
        writer = csv.writer(
            output,
            delimiter="\t"
        )
        description = self._db.get_description(None, lookup, auto_lookup)
        col_desc = self.get_columns_from_description(description)

        def fetch(offset):
            return self.list(filters, projection, lookup, auto_lookup, order, order_by, limit=100, offset=offset)

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
                if col_typ == u"timestamp":
                    value = datetime.utcfromtimestamp(
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
        items = list(self._db.find({u"id": id}, lookup=lookup, auto_lookup=auto_lookup))
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
        result = self._db.insert_one(document, lookup, auto_lookup)
        return {
            u"inserted_id": result.inserted_id
        }

    def description(self, lookup=None, auto_lookup=None):
        """
        Get the description of the table (fields & relations).
        Args:
            lookup (list of dict): Lookup option (joins).
            auto_lookup (int): Let the database construct the lookups (value is the deep).

        Returns:
            (dict): The description.
        """
        self.before(u"description")
        return self._db.get_description(None, lookup, auto_lookup)

    def delete(self, filters, lookup=None, auto_lookup=None):
        """
        Delete item(s).
        Args:
            filters (dict): Filter to know what to delete.
            lookup (list of dict): Lookup option (joins).
            auto_lookup (int): Let the database construct the lookups (value is the deep).

        Returns:
            (dict): The result of the deletion (with number of items deleted).
        """
        self.before(u"delete")
        result = self._db.delete_many(filters, lookup, auto_lookup)
        return {
            u"deleted_count": int(result.deleted_count)
        }

    def update(self, filters, update, lookup=None, auto_lookup=None):
        """
        Update item(s).
        Args:
            filters (dict): Filter to know what to delete.
            update (dict): Fields to update.
            lookup (list of dict): Lookup option (joins).
            auto_lookup (int): Let the database construct the lookups (value is the deep).

        Returns:
            (dict): The result of the deletion (with number of items deleted).
        """
        self.before(u"update")
        result = self._db.update_many(filters, update, None, lookup, auto_lookup)
        return {
            u"matched_count": int(result.matched_count)
        }

    def update_id(self, document_id, update, lookup=None, auto_lookup=None):
        """
        Update item(s).
        Args:
            document_id (int): The ID of the document to update.
            update (dict): Fields to update.
            lookup (list of dict): Lookup option (joins).
            auto_lookup (int): Let the database construct the lookups (value is the deep).

        Returns:
            (dict): The result of the deletion (with number of items deleted).
        """
        self.before(u"update")
        if type(document_id) is not int:
            raise ValueError(u"document_id must be an integer.")

        self._db.update_many({
            u"id": document_id
        }, update, None, lookup, auto_lookup)
        return self.get(document_id, lookup, auto_lookup)

    def list(self, filters=None, projection=None, lookup=None, auto_lookup=None, order=None, order_by=None, offset=0,
             limit=100):
        self.before(u"list")
        order = order or []
        sort = [(order, order_by[index]) for index, order in enumerate(order)]
        items = list(self._db.find(**{
            u"query": filters,
            u"projection": projection,
            u"lookup": lookup,
            u"auto_lookup": auto_lookup
        }).sort(sort).skip(offset).limit(limit + 1))

        has_next = len(items) > limit

        if has_next:
            del items[-1]

        return {
            u"items": items,
            u"offset": offset,
            u"limit": limit,
            u"has_next": has_next
        }