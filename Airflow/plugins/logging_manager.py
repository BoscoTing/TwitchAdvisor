import logging

dev_logger: logging.Logger = logging.getLogger(name='dev')
dev_logger.setLevel(logging.DEBUG)
handler: logging.StreamHandler = logging.StreamHandler()
formatter: logging.Formatter = logging.Formatter('%(name)s-%(levelname)s [%(filename)s at line %(lineno)s: %(module)s-%(funcName)s]: (%(asctime)s) %(message)s')
handler.setFormatter(formatter)
dev_logger.addHandler(handler)