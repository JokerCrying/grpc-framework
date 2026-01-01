import os
import typing
import warnings
import dataclasses
from typing import Type, List, Dict, Set, Any, Tuple, get_origin, get_args, Optional, TYPE_CHECKING
from ..core.params import ParamInfo
from ..core.serialization import ProtobufConverter, DataclassesConverter, JsonConverter
from ..core.enums import Interaction

if TYPE_CHECKING:
    from ..application import GRPCFramework


def generate_proto(
        app: 'GRPCFramework',
        output_path: Optional[os.PathLike[str]] = './proto',
        services: Optional[List[str]] = None,
        auto_mkdir: Optional[bool] = False,
        auto_save: Optional[bool] = True
) -> Dict[str, str]:
    """Helper function to generate proto from app"""
    generate_result = ProtoGenerator(app).generate(services)
    if auto_save:
        if not os.path.exists(output_path):
            if auto_mkdir:
                os.mkdir(output_path)
            else:
                warnings.warn(f"Make sure that {output_path} exists, otherwise it may cause the save to fail.")
        for service_name, proto_content in generate_result.items():
            with open(f'{str(output_path)}/{service_name}.proto', 'w+', encoding='utf-8') as stream:
                stream.write(proto_content)
    return generate_result


class ProtoGenerator:
    """
    Generate Protobuf definition from Python gRPC Framework application.
    Supports Code-First development by converting Python types (dataclasses) to Proto messages.
    """

    PROTO_TYPE_MAPPING = {
        int: "int32",
        str: "string",
        bool: "bool",
        float: "double",
        bytes: "bytes",
    }

    def __init__(self, app: 'GRPCFramework'):
        self.app = app
        self.converter_type = self.app.config.converter
        self._defined_messages: Set[str] = set()
        self._message_definitions: List[str] = []
        self._imports: Set[str] = set()

    def generate(self, services: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Generate .proto content strings, separated by service.
        
        Args:
            services: List of service names to generate. If None, generate all.
            
        Returns:
            Dict[str, str]: Map of service_name -> proto_content
        """
        # 1. Check Converter compatibility
        if issubclass(self.converter_type, ProtobufConverter):
            pass

        result = {}
        target_services = services if services is not None else self.app._services.keys()

        for service_name in target_services:
            if service_name not in self.app._services:
                continue

            # Reset state for each service to ensure clean dependencies
            self._defined_messages = set()
            self._message_definitions = []
            self._imports = set()

            methods = self.app._services[service_name]
            services_block = [f'service {service_name} {{']

            for method_name, meta in methods.items():
                rpc_name = method_name

                # Input
                input_type_name = self._parse_input_types(f"{service_name}{method_name}Request",
                                                          meta['input_param_info'])

                # Output
                return_info: ParamInfo = meta['return_param_info']
                if return_info.type is type(None) or return_info.type is None:
                    output_type_name = "google.protobuf.Empty"
                    self._imports.add('google/protobuf/empty.proto')
                else:
                    origin = get_origin(return_info.type) or return_info.type
                    is_list = origin is list or origin is List

                    if is_list and meta['response_interaction'] == Interaction.unary:
                        wrapper_name = f"{service_name}{method_name}Response"
                        self._create_message_from_params(wrapper_name, {"result": return_info})
                        output_type_name = wrapper_name
                    elif is_list and meta['response_interaction'] == Interaction.stream:
                        args = get_args(return_info.type)
                        if args:
                            item_info = ParamInfo(type=args[0])
                            output_type_name = self._resolve_type_to_proto(item_info)
                        else:
                            output_type_name = "string"
                    else:
                        output_type_name = self._resolve_type_to_proto(return_info)

                # Interaction
                req_stream = "stream " if meta['request_interaction'] == Interaction.stream else ""
                res_stream = "stream " if meta['response_interaction'] == Interaction.stream else ""

                services_block.append(
                    f'  rpc {rpc_name} ({req_stream}{input_type_name}) returns ({res_stream}{output_type_name});')

            services_block.append('}')
            services_block.append('')

            # Build file content
            sb = ['syntax = "proto3";', f'package {self.app.config.package};', '']

            for imp in sorted(self._imports):
                sb.append(f'import "{imp}";')
            if self._imports:
                sb.append('')

            sb.extend(self._message_definitions)
            sb.append('')
            sb.extend(services_block)

            result[service_name] = "\n\n".join(sb)

        return result

    def _parse_input_types(self, request_message_name: str, input_params: Dict[str, ParamInfo]) -> str:
        """
        Handle input parameters. 
        If there is only one parameter and it's a dataclass, use it directly as the message.
        Otherwise, create a wrapper Message.
        """
        if not input_params:
            self._imports.add('google/protobuf/empty.proto')
            return "google.protobuf.Empty"

        # Special case: Single argument that is a complex type (dataclass)
        # If the user defined `def func(self, request: MyRequest):`, we should use `MyRequest` directly.
        # But we need to verify if we can mapped it directly.
        # For Code-First, usually we treat the function arguments as the fields of the Request Message
        # unless it is a single argument which IS a message structure.

        # Strategy: 
        # Always generate a wrapper message for the RPC arguments to ensure stability,
        # UNLESS the user explicitly uses a single argument that looks like a DTO.
        # However, to be safe and consistent with "func(a, b)", let's create a synthetic message 
        # if there are multiple args or simple args.

        # Check if single dataclass arg
        if len(input_params) == 1:
            key = list(input_params.keys())[0]
            param_info = input_params[key]
            if dataclasses.is_dataclass(param_info.type):
                return self._resolve_type_to_proto(param_info)

        # Create a synthetic message for the arguments
        # e.g. GetUser(id: int, name: str) -> message GetUserRequest { int32 id = 1; string name = 2; }
        self._create_message_from_params(request_message_name, input_params)
        return request_message_name

    def _resolve_type_to_proto(self, param_info: ParamInfo) -> str:
        """
        Resolve a Python type to a Proto type name.
        If it's a complex type, it triggers message generation.
        """
        py_type = param_info.type

        # 1. Basic Types
        if py_type in self.PROTO_TYPE_MAPPING:
            return self.PROTO_TYPE_MAPPING[py_type]

        # 2. List / Repeated
        # Note: 'repeated' is a modifier, not a type. 
        # This method returns the TYPE name. The caller handles 'repeated'.
        # But wait, if we are resolving a top-level type (like return type), 
        # we can't return 'repeated string'. It must be wrapped in a message.
        # Proto RPCs cannot return 'repeated string' directly, they must return a Message.
        # So if we encounter a List at top level, we might need a wrapper.
        # However, this method is also used for field types.
        # Let's handle 'List' detection in the field generation, not here?
        # No, we need to handle it here if it's a return type.

        origin = get_origin(py_type) or py_type

        if origin is list or origin is List:
            # We cannot have a top-level List in gRPC return. 
            # It must be wrapped.
            # For now, let's assume this method returns the type name, 
            # and if it's used as a field, the caller adds 'repeated'.
            # If it's used as a return type, we might need to generate a *ListWrapper.
            args = get_args(py_type)
            if args:
                inner_type = args[0]
                # Recursive resolve
                inner_param = ParamInfo(type=inner_type)
                return self._resolve_type_to_proto(inner_param)
                # But wait, how does the caller know it's repeated?
                # This design needs to be careful.
                # Let's assume this method returns the *Base Type Name*.

        # 3. Dataclasses
        if dataclasses.is_dataclass(py_type):
            return self._register_dataclass_message(py_type)

        # 4. Dictionary (Map)
        if origin is dict or origin is Dict:
            # Proto maps: map<key_type, value_type>
            # This acts as a type name.
            args = get_args(py_type)
            if len(args) == 2:
                k_type, v_type = args
                k_proto = self._resolve_type_to_proto(ParamInfo(type=k_type))
                v_proto = self._resolve_type_to_proto(ParamInfo(type=v_type))
                return f"map<{k_proto}, {v_proto}>"

        return "string"  # Fallback for unknown types

    def _register_dataclass_message(self, dc_type: Type) -> str:
        """
        Generate a message definition for a dataclass and return its name.
        """
        name = dc_type.__name__
        if name in self._defined_messages:
            return name

        self._defined_messages.add(name)

        # Parse fields
        type_hints = dataclasses.fields(dc_type)
        params = {}
        for field in type_hints:
            params[field.name] = ParamInfo(type=field.type)

        self._create_message_from_params(name, params)
        return name

    def _create_message_from_params(self, message_name: str, params: Dict[str, ParamInfo]):
        """
        Create a message definition string and append to definitions.
        """
        lines = []
        lines.append(f'message {message_name} {{')

        idx = 1
        for name, info in params.items():
            field_line = self._generate_field(name, info, idx)
            lines.append(f'  {field_line}')
            idx += 1

        lines.append('}')
        self._message_definitions.append("\n".join(lines))

    def _generate_field(self, field_name: str, info: ParamInfo, idx: int) -> str:
        """
        Generate a single line for a field. e.g. "int32 id = 1;"
        """
        origin = get_origin(info.type) or info.type

        # Handle List
        if origin is list or origin is List:
            args = get_args(info.type)
            if args:
                inner_info = ParamInfo(type=args[0])
                type_name = self._resolve_type_to_proto(inner_info)
                return f"repeated {type_name} {field_name} = {idx};"
            else:
                # Fallback list of strings
                return f"repeated string {field_name} = {idx};"

        # Handle Optional (Oneof or just standard field in proto3)
        # Proto3 fields are optional by default.
        # But if it's explicit Optional[T], it's just T.
        # Python Optional[T] is Union[T, None]
        if origin is typing.Union:
            # Simplified handling for Optional
            args = get_args(info.type)
            valid_args = [a for a in args if a is not type(None)]
            if len(valid_args) == 1:
                # It is Optional[T]
                inner_info = ParamInfo(type=valid_args[0])
                type_name = self._resolve_type_to_proto(inner_info)
                # In newer proto3, we can use 'optional' keyword to track presence
                return f"optional {type_name} {field_name} = {idx};"

        # Standard field
        type_name = self._resolve_type_to_proto(info)
        return f"{type_name} {field_name} = {idx};"
