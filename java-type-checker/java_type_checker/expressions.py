# -*- coding: utf-8 -*-

from .types import Type


class Expression(object):
    """
    AST for simple Java expressions. Note that this package deal only with compile-time types;
    this class does not actually _evaluate_ expressions.
    """

    def static_type(self):
        """
        Returns the compile-time type of this expression, i.e. the most specific type that describes
        all the possible values it could take on at runtime. Subclasses must implement this method.
        """
        raise NotImplementedError(type(self).__name__ + " must implement static_type()")

    def check_types(self):
        """
        Validates the structure of this expression, checking for any logical inconsistencies in the
        child nodes and the operation this expression applies to them.
        """
        raise NotImplementedError(type(self).__name__ + " must implement check_types()")


class Variable(Expression):
    """ An expression that reads the value of a variable, e.g. `x` in the expression `x + 5`.
    """
    def __init__(self, name, declared_type):
        self.name = name                    #: The name of the variable
        self.declared_type = declared_type  #: The declared type of the variable (Type)
    
    def static_type(self):
        """
        Returns the compile-time type of this expression, i.e. the most specific type that describes
        all the possible values it could take on at runtime. Subclasses must implement this method.
        """
        return self.declared_type

    def check_types(self):
        """
        Validates the structure of this expression, checking for any logical inconsistencies in the
        child nodes and the operation this expression applies to them.
        """
        return


class Literal(Expression):
    """ A literal value entered in the code, e.g. `5` in the expression `x + 5`.
    """
    def __init__(self, value, type):
        self.value = value  #: The literal value, as a string
        self.type = type    #: The type of the literal (Type)

    def static_type(self):
        """
        Returns the compile-time type of this expression, i.e. the most specific type that describes
        all the possible values it could take on at runtime. Subclasses must implement this method.
        """
        return self.type

    def check_types(self):
        """
        Validates the structure of this expression, checking for any logical inconsistencies in the
        child nodes and the operation this expression applies to them.
        """
        return


class NullLiteral(Literal):
    def __init__(self):
        super().__init__("null", Type.null)


class MethodCall(Expression):
    """
    A Java method invocation, i.e. `foo.bar(0, 1, 2)`.
    """
    def __init__(self, receiver, method_name, *args):
        self.receiver = receiver        #: The object whose method we are calling (Expression)
        self.method_name = method_name  #: The name of the method to call (String)
        self.args = args                #: The method arguments (list of Expressions)

    def static_type(self):
        """
        Returns the compile-time type of this expression, i.e. the most specific type that describes
        all the possible values it could take on at runtime. Subclasses must implement this method.
        """
        return self.receiver.static_type().method_named(self.method_name).return_type

    def check_types(self):
        """
        Validates the structure of this expression, checking for any logical inconsistencies in the
        child nodes and the operation this expression applies to them.
        """
        # Recursively check the types of the rest of the expressions
        self.receiver.check_types()
        for arg in self.args:
            arg.check_types()

        receiver_type = self.receiver.static_type()

        # Check that methods can be called on the receiver
        if not receiver_type.is_subtype_of(Type.object):
            raise JavaTypeError(
                "Type {0} does not have methods".format(receiver_type.name))

        # Check that there are the correct number of arguments
        expected_arg_types = receiver_type.method_named(self.method_name).argument_types
        if len(expected_arg_types) != len(self.args):
            raise JavaTypeError(
                "Wrong number of arguments for {0}.{1}(): expected {2}, got {3}".format(
                receiver_type.name,
                self.method_name,
                len(expected_arg_types),
                len(self.args)))
        
        # Check that the argument types match with the method declaration
        for i in range(0, len(expected_arg_types)):
            if not self.args[i].static_type().is_subtype_of(expected_arg_types[i]):
                raise JavaTypeError(
                    "{0}.{1}() expects arguments of type {2}, but got {3}".format(
                        self.receiver.static_type().name,
                        self.method_name,
                        names(expected_arg_types),
                        names([a.static_type() for a in self.args])))

class ConstructorCall(Expression):
    """
    A Java object instantiation, i.e. `new Foo(0, 1, 2)`.
    """
    def __init__(self, instantiated_type, *args):
        self.instantiated_type = instantiated_type  #: The type to instantiate (Type)
        self.args = args                            #: Constructor arguments (list of Expressions)

    def static_type(self):
        """
        Returns the compile-time type of this expression, i.e. the most specific type that describes
        all the possible values it could take on at runtime. Subclasses must implement this method.
        """
        return self.instantiated_type

    def check_types(self):
        """
        Validates the structure of this expression, checking for any logical inconsistencies in the
        child nodes and the operation this expression applies to them.
        """
        # Recursively check the types of the rest of the expressions
        for arg in self.args:
            arg.check_types()

        # Check that the type is instantiable
        if not self.instantiated_type.is_instantiable:
            raise JavaTypeError(
                "Type {0} is not instantiable".format(self.instantiated_type.name))

        # Check that there are the correct number of arguments
        expected_arg_types = self.instantiated_type.constructor.argument_types
        if len(expected_arg_types) != len(self.args):
            raise JavaTypeError(
                "Wrong number of arguments for {0} constructor: expected {1}, got {2}".format(
                self.instantiated_type.name,
                len(expected_arg_types),
                len(self.args)))

        # Check that the argument types match with the method declaration
        for i in range(0, len(expected_arg_types)):
            if not self.args[i].static_type().is_subtype_of(expected_arg_types[i]):
                raise JavaTypeError(
                    "{0} constructor expects arguments of type {1}, but got {2}".format(
                        self.instantiated_type.name,
                        names(expected_arg_types),
                        names([a.static_type() for a in self.args])))




class JavaTypeError(Exception):
    """ Indicates a compile-time type error in an expression.
    """
    pass


def names(named_things):
    """ Helper for formatting pretty error messages
    """
    return "(" + ", ".join([e.name for e in named_things]) + ")"
