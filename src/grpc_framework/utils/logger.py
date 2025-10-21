import logging

__all__ = [
    'get_logger',
    'logger'
]


def get_logger(name: str, level=logging.DEBUG) -> logging.Logger:
    _logger = logging.getLogger(name)
    if not _logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        _logger.addHandler(handler)
        _logger.setLevel(level)
    return _logger


logger = get_logger('grpc-framework')
