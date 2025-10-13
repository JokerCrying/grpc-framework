import logging

__all__ = [
    'get_logger',
    'logger'
]


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


logger = get_logger('grpc-framework')
