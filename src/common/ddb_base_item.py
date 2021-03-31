#
#   Thiscovery API - THIS Institute’s citizen science platform
#   Copyright (C) 2019 THIS Institute
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   A copy of the GNU Affero General Public License is available in the
#   docs folder of this project.  It is also available www.gnu.org/licenses/
#
class DdbBaseItem:
    """
    Base class representing a Ddb item
    #todo: move this class to thiscovery-lib
    """

    def __repr__(self):
        return self.as_dict()

    def as_dict(self):
        return {
            k: v
            for k, v in self.__dict__.items()
            if (k[0] != "_") and (k not in ["created", "modified"])
        }

    def from_dict(self, item_dict):
        self.__dict__.update(item_dict)
