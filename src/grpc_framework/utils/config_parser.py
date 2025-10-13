import json
import yaml
import configparser
from ..types import FilePath, StrAnyDict
from typing import Callable, TypedDict


class ConfigParserOptions(TypedDict):
    ini_root_name: str


CONFIG_PARSER_TYPE = Callable[[FilePath, ConfigParserOptions], StrAnyDict]


def json_parser(filepath: FilePath, options: ConfigParserOptions) -> StrAnyDict:
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def yaml_parser(filepath: FilePath, options: ConfigParserOptions) -> StrAnyDict:
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def ini_parser(filepath: FilePath, options: ConfigParserOptions) -> StrAnyDict:
    cfg = configparser.ConfigParser()
    cfg.read(filepath)
    return dict(cfg[options['ini_root_name']])


config_map = {
    'json': json_parser,
    'yaml': yaml_parser,
    'yml': yaml_parser,
    'ini': ini_parser
}


def add_config_parser(file_type: str, parser: CONFIG_PARSER_TYPE):
    config_map[file_type] = parser


def parse_config(file_type: str, filepath: FilePath, options: ConfigParserOptions) -> StrAnyDict:
    if file_type not in config_map:
        raise ValueError(f'No parser supporting this configuration file type could be found, '
                         f'you can use `GRPCFrameworkConfig.add_config_parser` to add new parser.')
    return config_map[file_type](filepath, options)


__all__ = [
    'add_config_parser',
    'parse_config',
    'CONFIG_PARSER_TYPE',
    'ConfigParserOptions'
]
