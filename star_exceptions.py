#!/usr/bin/env python3

class TypeMissingError(Exception):
    """Exception raised for documents missing the type field"""

    def __init__(self, message="Document is missing the type field"):
        super().__init__(self.message)

class TypeMismatch(Exception):
    """Exception is rasied when the object is not the expected type"""
    def __init__(self, message="Document is not the specifed type!"):
        super().__init__(self.message)
